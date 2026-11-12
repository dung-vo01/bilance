# Infrastructure

AWS pieces that sit next to the API. They are currently created by hand in the
AWS console (region `eu-north-1`); the plan is to describe them as code
(Terraform or CDK) later, and this file documents what exists until then.

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
