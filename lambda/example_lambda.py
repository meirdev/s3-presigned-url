import json
import mimetypes
import os
import secrets
import string

import boto3

BUCKET_REGION = os.environ["BUCKET_REGION"]
BUCKET_NAME = os.environ["BUCKET_NAME"]

EXPIRES_IN = 1000
MAX_CONTENT_LENGTH = 104857600  # 100MB


s3_client = boto3.client("s3", region_name=BUCKET_REGION)


def handler(event, context):
    body = json.loads(event["body"])

    if body["action"] == "upload":
        key = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))

        content_type = mimetypes.guess_type(body["key"])
        if content_type[0] is None:
            content_type = "application/octet-stream"
        else:
            content_type = content_type[0]

        url = s3_client.generate_presigned_post(
            Bucket=BUCKET_NAME,
            Key=key,
            Fields={"Content-Type": content_type, "x-amz-meta-filename": body["key"]},
            Conditions=[
                {"Content-Type": content_type},
                ["Content-Length-Range", 0, MAX_CONTENT_LENGTH],
                {"x-amz-meta-filename": body["key"]},
            ],
            ExpiresIn=EXPIRES_IN,
        )

    elif body["action"] == "download":
        url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": BUCKET_NAME, "Key": body["key"]},
            ExpiresIn=EXPIRES_IN,
        )

    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid action"})
        }

    return {
        "statusCode": 200,
        "body": json.dumps(url)
    }
