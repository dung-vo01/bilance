#!/usr/bin/env bash
# Deploys a new API image on the EC2 instance. Not run by hand: the
# deploy-backend-aws CI job sends it to the instance through SSM Run Command
# (see .github/workflows/ci.yml and infra/README.md).
#
# Usage: deploy.sh <full image reference, e.g. 123456789012.dkr.ecr.eu-north-1.amazonaws.com/bilance-api:abc123>
set -euo pipefail

IMAGE="${1:?usage: deploy.sh <image>}"
REGISTRY="${IMAGE%%/*}"
REGION="eu-north-1"
NAME="bilance-api"

# The instance role (AmazonEC2ContainerRegistryReadOnly) allows pulling.
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY"

docker pull "$IMAGE"

# Replace the running container. The API runs the database migrations
# (alembic upgrade head) on start, so it can take a few seconds to answer.
docker rm -f "$NAME" 2>/dev/null || true
docker run -d --name "$NAME" --restart unless-stopped \
  --network bilance \
  --env-file /etc/bilance/api.env \
  -p 80:5000 \
  "$IMAGE"

# Fail the deploy if the new container does not come up healthy.
for _ in $(seq 1 30); do
  if curl -fsS http://localhost/api/config > /dev/null; then
    echo "API is up: $IMAGE"
    docker image prune -f > /dev/null
    exit 0
  fi
  sleep 2
done

echo "API did not become healthy within 60 s" >&2
docker logs --tail 50 "$NAME" >&2
exit 1
