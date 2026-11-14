from functools import lru_cache

import boto3

from app.core.config import settings


@lru_cache
def get_ses_client():
    return boto3.client(
        "sesv2",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_SES_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SES_SECRET_ACCESS_KEY,
    )
