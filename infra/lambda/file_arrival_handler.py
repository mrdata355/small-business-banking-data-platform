import hashlib
import os
from datetime import datetime, timezone

import boto3

TABLE = os.environ.get("MANIFEST_TABLE")


def handler(event, context):
    table = boto3.resource("dynamodb").Table(TABLE)
    processed = []

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        etag = record["s3"]["object"].get("eTag", "")
        file_id = hashlib.sha256(f"{bucket}/{key}/{etag}".encode()).hexdigest()

        table.put_item(
            Item={
                "file_id": file_id,
                "bucket": bucket,
                "object_key": key,
                "etag": etag,
                "status": "ARRIVED",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ConditionExpression="attribute_not_exists(file_id)",
        )
        processed.append(file_id)

    return {"processed": processed}
