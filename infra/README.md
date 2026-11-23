# Infrastructure

AWS pieces that sit next to the API (frontend hosting, a practice copy of the
API on EC2, and the scheduled guest cleanup). They are currently created by hand in the
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
| `VITE_API_URL` | the API host URL, without `/api`. Currently the CloudFront URL of the API on EC2 (see "Backend on EC2"); it was the Render URL before. Only the AWS frontend job reads it, so Vercel is unaffected |

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

## Backend on EC2 (practice, alongside Render)

The API also runs on a single EC2 instance, next to the Render deployment that
the live demo uses. It is an AWS practice setup with a deadline: the AWS free
plan (about $200 in credits) ends on **2027-02-12**, so tear it down or start
paying before then (see Teardown).

**Status:** working. The API is reachable over HTTPS through a CloudFront
distribution, and the **AWS-hosted frontend** (the S3 + CloudFront one) uses it,
while the Vercel frontend keeps using the Render API. The two APIs have
**separate databases**. The database is backed up nightly to S3 (see Backups).
Still to do: optionally a secret header that the API checks so only this
distribution can use the origin.

```
Browser (AWS frontend)
  --HTTPS--> CloudFront "bilance-api" (no caching, all methods, forwards headers)
  --HTTP, port 80--> EC2 instance (security group only admits CloudFront's servers)

push to main
  |
  +-- CI: backend-tests
        |
        +-- deploy-backend-aws
              1. build the image, push to ECR (tags: commit SHA, latest)
              2. SSM Run Command on the instance (no SSH) runs infra/ec2/deploy.sh
                   pull image -> replace container -> wait for /api/config

EC2 instance (Docker network "bilance")
  +-- bilance-api  (port 80 on the host -> 5000 in the container)
  +-- bilance-db   (postgres:16-alpine, not published; only reachable by bilance-api)
        data: /data/postgres  = separate 8 GiB EBS volume
```

### Resources

| Resource | Name / value | Notes |
| --- | --- | --- |
| EC2 instance | `bilance-api` | `t3.small` (2 vCPU, 2 GiB), Amazon Linux 2023 x86, `eu-north-1c`, no key pair (Session Manager only), credit specification **Standard** (no surprise burst charges), IMDSv2 only |
| Root volume | 20 GiB gp3, encrypted | Deleted with the instance |
| Data volume | `bilance-pgdata`, 8 GiB gp3, encrypted | xfs, mounted at `/data/postgres` through an `/etc/fstab` entry by UUID with `nofail`. Created separately so it survives replacing the instance |
| Swap | 2 GiB `/swapfile` | Safety net for memory spikes (the instance has no other swap) |
| Elastic IP | `13.61.208.240`, associated with `bilance-api` | A stable address, so the CloudFront origin (the instance's public DNS name) does not change if the instance is stopped and started. Billed like any public IPv4 address, and an unattached Elastic IP still costs money |
| Security group | `launch-wizard-2` | **One inbound rule:** HTTP, TCP 80, source the AWS-managed prefix list `com.amazonaws.global.cloudfront.origin-facing`, so only CloudFront's servers can connect. Port 22 is closed |
| CloudFront distribution | `bilance-api` | Custom origin = the Elastic IP's public DNS name, **HTTP only on port 80**; viewers are redirected to HTTPS; all seven HTTP methods; cache policy **CachingDisabled**, origin request policy **AllViewer** (passes `Authorization`, cookies and query strings through); no WAF; no response-headers policy, because the API sends its own CORS headers |
| Instance role | `bilance-api-instance-role` | `AmazonSSMManagedInstanceCore` (Session Manager, Run Command) and `AmazonEC2ContainerRegistryReadOnly` (pull images) |
| ECR repository | `bilance-api` | Mutable tags, lifecycle rule keeps the newest 5 images |
| Deploy role | `bilance-backend-deploy` | Assumed by GitHub Actions through OIDC, see below |

Files on the instance (mode 600, owned by root, never committed):

| File | Contents |
| --- | --- |
| `/etc/bilance/db.env` | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (password generated on the server) |
| `/etc/bilance/api.env` | The API settings: `ENVIRONMENT`, `SECRET_KEY`, `JWT_SECRET_KEY` (generated on the server), `DATABASE_URL` (host `bilance-db`), `CORS_ORIGINS`, `FRONTEND_URL`, `EMAIL_ENABLED=False`, `LOG_LEVEL` |

### Deploy role (GitHub OIDC, no stored keys)

Same pattern as the frontend role. The trust policy only accepts tokens for
`repo:dung-vo01/bilance:ref:refs/heads/main` (audience `sts.amazonaws.com`), and
the job must not use a GitHub `environment:`. Inline policy `deploy-backend-ecr-ssm`:

- `ecr:GetAuthorizationToken` (needs `*`).
- Push actions (`BatchCheckLayerAvailability`, `GetDownloadUrlForLayer`,
  `BatchGetImage`, `InitiateLayerUpload`, `UploadLayerPart`,
  `CompleteLayerUpload`, `PutImage`) on the `bilance-api` repository only.
  `docker push` checks whether the image manifest already exists before it
  uploads it, which needs `BatchGetImage`; without it the push fails at the very
  end with `403 Forbidden`.
- `ssm:SendCommand` on this one instance and on the `AWS-RunShellScript`
  document.
- `ssm:GetCommandInvocation` (needs `*`) to read the result.

GitHub repository **variables** (Settings -> Secrets and variables -> Actions ->
Variables):

| Variable | Value |
| --- | --- |
| `AWS_BACKEND_DEPLOY_ROLE_ARN` | ARN of `bilance-backend-deploy` |
| `BACKEND_INSTANCE_ID` | the instance ID (`i-...`) |

### What a deploy does

[`ec2/deploy.sh`](ec2/deploy.sh) is sent to the instance by the workflow. It logs
in to ECR with the instance role, pulls the image, removes the old container,
starts the new one with `--env-file /etc/bilance/api.env`, and polls
`http://localhost/api/config` for up to 60 seconds. If the API does not answer,
it prints the container logs and fails, and so does the GitHub job. The API runs
`alembic upgrade head` when it starts, so migrations apply on every deploy.
Replacing the container means a few seconds of downtime per deploy.

### Setting up the instance by hand (one time)

Do these in order. Most are console steps; the rest run in a Session Manager
shell (EC2 -> select the instance -> Connect -> **Session Manager**; do not use
EC2 Instance Connect, it needs port 22).

1. Create the instance role (EC2 trust, the two managed policies above), then
   launch the instance with the settings in the table (**Standard** credit
   specification, encrypted root volume, no key pair, a new security group with
   **no** inbound rules, the instance profile attached).
2. Create the 8 GiB encrypted gp3 volume in the **same availability zone** and
   attach it as `/dev/sdf` (it appears as `/dev/nvme1n1`).
3. Docker and swap:
   ```bash
   sudo dnf install -y docker
   sudo systemctl enable --now docker
   sudo usermod -aG docker ssm-user

   sudo dd if=/dev/zero of=/swapfile bs=128M count=16 status=progress
   sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```
4. Format and mount the data disk. Check `lsblk -f` first: only format a disk
   that has no filesystem (`sudo file -s /dev/nvme1n1` prints `data`).
   ```bash
   sudo mkfs -t xfs /dev/nvme1n1
   sudo mkdir -p /data/postgres
   sudo mount /dev/nvme1n1 /data/postgres
   UUID=$(sudo blkid -s UUID -o value /dev/nvme1n1)
   echo "UUID=$UUID /data/postgres xfs defaults,nofail 0 2" | sudo tee -a /etc/fstab
   sudo mount -a
   ```
5. Postgres (password generated on the server, never printed):
   ```bash
   sudo mkdir -p /etc/bilance
   PW=$(openssl rand -hex 24)
   printf "POSTGRES_USER=bilance\nPOSTGRES_PASSWORD=%s\nPOSTGRES_DB=bilance\n" "$PW" | sudo tee /etc/bilance/db.env > /dev/null
   sudo chmod 600 /etc/bilance/db.env && unset PW

   sudo docker network create bilance
   sudo docker run -d --name bilance-db --restart unless-stopped \
     --network bilance --env-file /etc/bilance/db.env \
     -v /data/postgres:/var/lib/postgresql/data postgres:16-alpine
   ```
6. The API env file (secrets generated on the server; adjust `CORS_ORIGINS` and
   `FRONTEND_URL` to the frontend that will use this API):
   ```bash
   sudo bash -c '
   set -e
   . /etc/bilance/db.env
   cat > /etc/bilance/api.env <<EOF
   ENVIRONMENT=production
   SECRET_KEY=$(openssl rand -hex 32)
   JWT_SECRET_KEY=$(openssl rand -hex 32)
   DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@bilance-db:5432/${POSTGRES_DB}
   CORS_ORIGINS=https://<frontend-origin>
   FRONTEND_URL=https://<frontend-origin>
   EMAIL_ENABLED=False
   LOG_LEVEL=INFO
   EOF
   chmod 600 /etc/bilance/api.env
   '
   ```
7. Create the ECR repository (mutable tags, keep the newest 5 images), the
   deploy role and the two GitHub variables, then merge to `main`. The first
   deploy starts the API container. (A deploy fails at the end with `403` if the
   role lacks `ecr:BatchGetImage`, see the deploy role above.)
8. Allocate an **Elastic IP** and associate it with the instance. Note the new
   public DNS name (`ec2-<ip-with-dashes>.eu-north-1.compute.amazonaws.com`).
9. Edit the security group: add one inbound rule, HTTP port 80, source the
   prefix list `com.amazonaws.global.cloudfront.origin-facing`.
10. Create the CloudFront distribution with the settings in the resource table
    (origin type **Other**, protocol **HTTP only**, **Customize cache settings**:
    redirect HTTP to HTTPS, all methods, CachingDisabled, AllViewer). Test with
    `curl.exe -s https://<distribution>.cloudfront.net/api/config` (in
    PowerShell, plain `curl` is an alias for `Invoke-WebRequest`).
11. To use it from the AWS-hosted frontend, set the repository variable
    `VITE_API_URL` to the distribution's URL (no trailing slash, no `/api`) and
    re-run the `deploy-frontend-aws` job. Make sure that frontend's origin is in
    `CORS_ORIGINS` in `/etc/bilance/api.env`.

### Backups (nightly pg_dump to S3)

```
systemd timer (02:30 UTC) -> bilance-backup.service -> /usr/local/bin/bilance-backup.sh
  1. pg_dump (custom format) inside the bilance-db container, to /tmp in the container
  2. check the file is not empty, then pg_restore --list it (proves it is readable)
  3. docker cp the verified file to the instance, aws s3 cp it to the bucket
  4. delete both temporary copies (also when something failed)
```

A failed step stops the script with a non-zero exit code, so a broken or empty
dump is never uploaded as if it were a backup.

| Resource | Name / value | Notes |
| --- | --- | --- |
| S3 bucket | `bilance-db-backups-01` (`eu-north-1`) | Private (block all public access), SSE-S3, objects under `daily/` |
| Lifecycle rule | `bilance-db-expiration-rule` | Whole bucket: expire objects after **14 days**, delete incomplete multipart uploads after 1 day |
| Role policy | `backup-bucket-access` on `bilance-api-instance-role` | `s3:ListBucket` on the bucket, `s3:PutObject` and `s3:GetObject` on its objects. **No delete permission**, so a compromised instance cannot wipe the backups; only the lifecycle rule deletes them |
| Script | [`ec2/backup.sh`](ec2/backup.sh) | Installed as `/usr/local/bin/bilance-backup.sh`, runs as root and uses the instance role (no stored keys) |
| Units | [`ec2/bilance-backup.service`](ec2/bilance-backup.service), [`ec2/bilance-backup.timer`](ec2/bilance-backup.timer) | In `/etc/systemd/system/`. The service is a one-shot job; the timer runs it daily and is `Persistent`, so a run missed while the instance was off happens at the next boot |

Install on the instance (after the files are on `main`):

```bash
B=https://raw.githubusercontent.com/dung-vo01/bilance/main/infra/ec2
sudo curl -fsSL $B/backup.sh -o /usr/local/bin/bilance-backup.sh
sudo curl -fsSL $B/bilance-backup.service -o /etc/systemd/system/bilance-backup.service
sudo curl -fsSL $B/bilance-backup.timer -o /etc/systemd/system/bilance-backup.timer
sudo chmod 755 /usr/local/bin/bilance-backup.sh
sudo systemctl daemon-reload
sudo systemctl enable --now bilance-backup.timer
```

Run one by hand and check it:

```bash
sudo /usr/local/bin/bilance-backup.sh        # or: sudo systemctl start bilance-backup.service
sudo journalctl -u bilance-backup.service -n 20 --no-pager
systemctl list-timers bilance-backup.timer   # when it runs next
aws s3 ls s3://bilance-db-backups-01/daily/
```

The files are not deployed by the CI pipeline: changing `backup.sh` or the units
in the repo means downloading them to the instance again with the commands above.
Limit: the backups live in the same AWS account and region as the database, so
they protect against disk or instance loss, not against losing the account.

#### Restore test (done on 2026-11-23)

A backup only counts once it has been restored. This restores the newest backup
into a **scratch database**, compares it with the live one and deletes it, so it
never touches real data. Run it in a Session Manager shell, for example after
changing the backup script:

```bash
KEY=$(aws s3 ls s3://bilance-db-backups-01/daily/ | sort | tail -n 1 | awk '{print $4}')
aws s3 cp "s3://bilance-db-backups-01/daily/$KEY" /var/tmp/restore-test.dump

sudo docker exec bilance-db createdb -U bilance bilance_restore_test
sudo docker cp /var/tmp/restore-test.dump bilance-db:/tmp/restore-test.dump
sudo docker exec bilance-db pg_restore -U bilance -d bilance_restore_test --no-owner /tmp/restore-test.dump

for DB in bilance bilance_restore_test; do
  echo "== $DB"
  sudo docker exec bilance-db psql -U bilance -d $DB -tA -c "SELECT 'users', count(*) FROM users UNION ALL SELECT 'tables', count(*) FROM information_schema.tables WHERE table_schema='public' UNION ALL SELECT 'migration', 0 FROM alembic_version;"
done

sudo docker exec bilance-db dropdb -U bilance bilance_restore_test
sudo docker exec bilance-db rm -f /tmp/restore-test.dump
rm -f /var/tmp/restore-test.dump
```

`pg_restore` should print nothing, and both databases should show the same user
and table counts. The first run restored a backup with 1 user and 10 tables
identically.

#### Restoring for real

Not rehearsed on the live database; it uses the same mechanism as the test. Stop
the API first so nothing holds a connection, restore into a fresh database with
the same name, then start the API again:

```bash
sudo docker stop bilance-api
sudo docker exec bilance-db dropdb -U bilance bilance
sudo docker exec bilance-db createdb -U bilance bilance
sudo docker cp /var/tmp/restore.dump bilance-db:/tmp/restore.dump   # downloaded as in the test
sudo docker exec bilance-db pg_restore -U bilance -d bilance --no-owner /tmp/restore.dump
sudo docker start bilance-api
```

If the instance or its data volume is gone, first rebuild them (setup steps 1 to
6, which creates an empty database), then restore as above before the first
deploy.

### Operating it

- **Shell:** Session Manager, as above. Nothing listens on port 22.
- **Logs:** `sudo docker logs --tail 100 bilance-api` (or `bilance-db`).
- **Database shell:** `sudo docker exec -it bilance-db psql -U bilance bilance`.
- **Make a user an admin** (this database is separate from Render's, so accounts
  must be created again here). Register through the app, then promote the
  account. The role column is an enum with **uppercase** values:
  ```bash
  sudo docker exec bilance-db psql -U bilance -d bilance -c "SELECT id, username, role FROM users;"
  sudo docker exec bilance-db psql -U bilance -d bilance -c "UPDATE users SET role = 'ADMIN' WHERE username = '<username>';"
  ```
  It should print `UPDATE 1`. Always keep the `WHERE`.
- **Health:** `curl -s localhost/api/config` on the instance;
  `sudo docker ps` shows both containers; `free -m` and `df -h` for memory and disk.
- **Change a setting:** edit `/etc/bilance/api.env`, then restart the container
  with the same `docker run` as in `deploy.sh` (or just push a deploy).
- **Rotate secrets:** changing `SECRET_KEY`/`JWT_SECRET_KEY` logs everyone out;
  changing the database password means changing it in both files and in Postgres.
- **Rebuilding the instance:** the setup above is manual, so a replacement means
  repeating steps 3 to 6 and the backup install. The data volume can be
  re-attached and re-mounted without formatting (skip `mkfs`).

### Cost

Roughly: `t3.small` about $16 a month, the two EBS volumes about $3, the public
IPv4 address (now the Elastic IP) about $3.60, ECR and CloudFront a few cents at
this traffic. Around $23 a month, covered by the free-plan credits. A monthly
AWS Budget alert is set as a safety net.

### Teardown

Before 2027-02-12 (or earlier to stop the spending):

1. Take a final backup if the data matters (run `bilance-backup.sh`, then copy
   the file out of the bucket, or snapshot `bilance-pgdata`).
2. Terminate the instance, then delete the `bilance-pgdata` volume (it is not
   removed automatically) and any snapshots.
3. **Release the Elastic IP** (it is billed if it is left allocated and
   unattached), then delete the `bilance-api` CloudFront distribution (disable
   it first and wait), the ECR repository, the `bilance-backend-deploy` and
   `bilance-api-instance-role` roles, and the security group.
   Also empty and delete the `bilance-db-backups-01` bucket and remove the
   `backup-bucket-access` policy (they go with the role).
4. Remove the `deploy-backend-aws` job and its two repository variables, and set
   `VITE_API_URL` back to the Render API URL, then re-run `deploy-frontend-aws`
   so the AWS-hosted frontend does not point at a deleted API.

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
