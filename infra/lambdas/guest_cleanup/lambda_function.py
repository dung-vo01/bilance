import json
import logging
import os
import urllib.request

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Module level: runs once per cold start, reused by warm invocations.
ssm = boto3.client("ssm")
API_URL = os.environ["API_URL"]
SECRET_PARAM = os.environ["SECRET_PARAM"]


def get_secret() -> str:
    ssm_response = ssm.get_parameter(Name=SECRET_PARAM, WithDecryption=True)
    return ssm_response["Parameter"]["Value"]


def lambda_handler(event, context):
    secret = get_secret()

    request = urllib.request.Request(
        API_URL,
        method="POST",
        headers={
            "User-Agent": "bilance-guest-cleanup-lambda",
            "X-Internal-Secret": secret,
        },
    )

    # within 90 secs of this Lambda timeout, so if the request fails, we have clear error before Lambda kills the whole thing
    with urllib.request.urlopen(request, timeout=75) as response:
        data = json.loads(response.read())

    deleted = data["data"]["deleted"]

    logger.info("Deleted %d guest accounts", deleted)

    return {"deleted": deleted}
