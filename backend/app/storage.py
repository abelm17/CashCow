from functools import lru_cache
import os

def get_s3_bucket() -> str | None:
    return os.environ.get("S3_BUCKET", "").strip() or None

@lru_cache(maxsize=4)
def _client_for_region(region: str | None):
    import boto3
    from botocore.config import Config

    return boto3.session.Session().client(
        "s3",
        region_name=region,
        config=Config(
            connect_timeout=1,
            read_timeout=1,
            retries={"mode": "standard", "total_max_attempts": 1},
        ),
    )

def get_s3_client():
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    return _client_for_region(region)
