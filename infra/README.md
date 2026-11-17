# Infrastructure

AWS pieces that sit next to the API (frontend hosting and the scheduled guest
cleanup). They are currently created by hand in the
AWS console (region `eu-north-1`); the plan is to describe them as code
(Terraform or CDK) later, and this file documents what exists until then.

## Frontend hosting (S3 + CloudFront)

The frontend is a static build, so it needs no server. It is deployed to **two
hosts at once**, each with its own flow, and both talk to the same API:

```
push to main
  |
  +-- CI: frontend-build (lint, typecheck, build)
        |
        +-- deploy-frontend      -> Vercel CLI                      -> bilance.vercel.app
        |
        +-- deploy-frontend-aws  -> GitHub OIDC -> S3 sync          -> CloudFront
                                    -> CloudFront invalidation         d8jwj1s3y6g2n.cloudfront.net
```

Both jobs live in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) and
only run on a push to `main` (not on pull requests), after `frontend-build`
passes. They are independent: if one fails, the other still deploys, and
neither is a required check for merging.

### How a request is served

```
Browser --HTTPS--> CloudFront edge --(cache miss)--> private S3 bucket
   |                    ^ serves cached copy on a hit
   +--> API calls go straight to the backend, not through CloudFront
```

CloudFront gives HTTPS and caching. The bucket is private and only readable by
this distribution (Origin Access Control).

### Resources

| Resource | Name / value | Notes |
| --- | --- | --- |
| S3 bucket | `bilance-frontend-01` (`eu-north-1`) | Block all public access ON, ACLs disabled, versioning off, SSE-S3 |
| CloudFront distribution | `bilance-frontend` | S3 origin with Origin Access Control (the console wizard added the bucket policy), default root object `index.html`, no WAF, pay-as-you-go |
| Error pages | 403 and 404 -> `/index.html`, response code 200 | Single-page-app fallback, replaces the rewrite in `vercel.json`. 5xx errors are deliberately not rewritten, so real outages stay visible |
| IAM role | `bilance-frontend-deploy` | Assumed by GitHub Actions through OIDC (below) |
| IAM identity provider | `token.actions.githubusercontent.com` | Audience `sts.amazonaws.com` |

### Deploy role (GitHub OIDC, no stored keys)

The workflow asks GitHub for a short-lived token and exchanges it for AWS
credentials, so no AWS access key is stored in GitHub. The role's trust policy
only accepts tokens for this repository on the `main` branch:

- `aud` = `sts.amazonaws.com`
- `sub` = `repo:dung-vo01/bilance:ref:refs/heads/main`

Because of that `sub`, the job must **not** use a GitHub `environment:`, which
would change the token's subject and be rejected.

Inline policy on the role (least privilege, replace the placeholders):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::bilance-frontend-01"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::bilance-frontend-01/*"
    },
    {
      "Effect": "Allow",
      "Action": "cloudfront:CreateInvalidation",
      "Resource": "arn:aws:cloudfront::<account-id>:distribution/<distribution-id>"
    }
  ]
}
```

### GitHub repository variables

Settings -> Secrets and variables -> Actions -> **Variables** (repository
variables, not environment variables; none of them are secret):

| Variable | Value |
| --- | --- |
| `AWS_DEPLOY_ROLE_ARN` | ARN of `bilance-frontend-deploy` |
| `S3_BUCKET` | `bilance-frontend-01` |
| `CLOUDFRONT_DISTRIBUTION_ID` | the distribution ID (`E...`) |
| `VITE_API_URL` | the API host URL, without `/api` |

### What the deploy job does

1. Builds the app with `VITE_API_URL` baked in.
2. Uploads `assets/` (content-hashed file names) with
   `Cache-Control: public,max-age=31536000,immutable`. This runs first and old
   files are kept, so a page that opened just before a deploy can still load
   its bundles.
3. Uploads `index.html` and the other root files with `Cache-Control: no-cache`
   and `--delete`, so removed files disappear.
4. Invalidates `/index.html` in CloudFront.

### Operating it

- **CORS:** the CloudFront URL must be listed in `CORS_ORIGINS` on the API
  (comma-separated, no trailing slash), alongside the Vercel URL. A new
  frontend address means a new entry there, otherwise the browser blocks every
  API call.
- **Manual upload** (for a first test or an emergency): build with
  `VITE_API_URL` set, then upload the **contents** of `frontend/dist` to the
  bucket in the S3 console, including the `assets` folder.
- **A deploy did not show up:** check the Actions run, then hard-refresh. If
  `AssumeRoleWithWebIdentity` fails, the cause is the role ARN or the trust
  policy `sub`; if the invalidation fails with `AccessDenied`, check the
  distribution ARN in the inline policy.
- **Custom domain:** not set up, which is why the address is the generated
  `*.cloudfront.net` name. Adding one means an alternate domain name on the
  distribution plus a certificate from ACM in `us-east-1` (the same domain
  would also unlock SES production access for email).

### Cost

S3 storage and CloudFront traffic for a site this small are pennies at most,
and CloudFront has an always-free monthly allowance. Unlike the backend ideas
that depend on credits, this part has no teardown deadline.

### Teardown

Delete the CloudFront distribution (disable it first and wait), empty and
delete the bucket, delete the IAM role and the GitHub identity provider, remove
the CloudFront URL from `CORS_ORIGINS`, and delete the `deploy-frontend-aws`
job and the four repository variables.

## Guest cleanup (Lambda + EventBridge Scheduler)

Guest accounts expire after `GUEST_ACCOUNT_TTL_HOURS`. A scheduled Lambda calls
the API once a day to delete the expired ones:

```
EventBridge Scheduler (daily 03:00AM) -> Lambda -> POST /api/internal/cleanup-guests -> database
                                         |
                                         +-- reads the shared secret from SSM Parameter Store
```

The Lambda knows nothing about guests or the database. It only sends an
authenticated request; the route is described in
[`backend/README.md`](../backend/README.md#internal-routes).

### Resources

| Resource | Name / value | Notes |
| --- | --- | --- |
| SSM parameter | `/bilance/internal-api-secret` | SecureString, standard tier, default `alias/aws/ssm` key. Same value as `INTERNAL_API_SECRET` on the API |
| Lambda function | `bilance-guest-cleanup` | Python 3.13, arm64, 128 MB, **timeout 90 s**, not in a VPC (it must reach the API over the internet) |
| Environment variables | `API_URL`, `SECRET_PARAM` | `API_URL` is the full URL of `/api/internal/cleanup-guests`; `SECRET_PARAM` is the parameter name above |
| Execution role | `bilance-guest-cleanup-role-...` | `AWSLambdaBasicExecutionRole` (logs) plus the inline policy below |
| Schedule | `bilance-guest-cleanup-daily` | `cron(0 3 * * ? *)`, time zone Europe/Helsinki, target the Lambda with payload `{}`, retry policy 1 hour / 2 attempts, no dead-letter queue |

Inline policy `read-internal-api-secret` on the execution role. It allows
reading that one parameter and nothing else (no KMS permission is needed for
the default `aws/ssm` key):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "ssm:GetParameter",
      "Resource": "arn:aws:ssm:eu-north-1:<account-id>:parameter/bilance/internal-api-secret"
    }
  ]
}
```

### How the handler behaves

Code: [`lambdas/guest_cleanup/lambda_function.py`](lambdas/guest_cleanup/lambda_function.py)
(handler `lambda_function.lambda_handler`, standard library plus `boto3`, which
the Lambda runtime already includes).

- Fetches the secret, sends `POST` with the `X-Internal-Secret` header and a
  custom `User-Agent`, and logs `Deleted N guest accounts`.
- Any non-2xx response raises, so the run is marked as failed (visible in the
  function's `Errors` metric and logs). Lambda retries a failed asynchronous
  run twice by itself; the Scheduler retry policy only covers failures to hand
  the event to Lambda.
- The API runs on a free-tier host that sleeps when idle, so the first call can
  take 30 to 60 seconds to get an answer. The HTTP timeout (75 s) is kept below
  the Lambda timeout (90 s) so a slow wake-up fails with a clear error.
- The secret and request headers are never logged.

### Operating it

- **Change the code:** edit the file in the repo, paste it into the function's
  code editor in the console and click Deploy. The repo copy is the source of
  truth.
- **Rotate the secret:** generate a new one
  (`python -c "import secrets; print(secrets.token_urlsafe(32))"`), update
  `INTERNAL_API_SECRET` on the API and the SSM parameter. The Lambda reads the
  parameter on every run, so it needs no redeploy.
- **Test:** in the function, run Test with `{}`. Expect `{"deleted": N}`.
- **Check a scheduled run:** Monitor -> View CloudWatch logs
  (`/aws/lambda/bilance-guest-cleanup`), or look for `POST
  /api/internal/cleanup-guests` in the API logs.

### Cost

Everything here is within the free tier: Lambda (one run a day), EventBridge
Scheduler, a standard SSM parameter and a few KB of CloudWatch logs. Do not
shorten the schedule for testing and leave it: a 5-minute rate also keeps the
sleeping API awake.

### Teardown

Delete the schedule, the Lambda function, its execution role (and the
`/aws/lambda/bilance-guest-cleanup` log group) and the SSM parameter.
