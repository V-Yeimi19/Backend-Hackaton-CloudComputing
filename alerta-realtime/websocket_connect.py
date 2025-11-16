import json
import os
import boto3
from datetime import datetime

CONNECTIONS_TABLE = os.environ["CONNECTIONS_TABLE"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(CONNECTIONS_TABLE)

def lambda_handler(event, context):
    print("Event OnConnect:", json.dumps(event))

    connection_id = event["requestContext"]["connectionId"]
    now = datetime.utcnow().isoformat()

    try:
        table.put_item(
            Item={
                "connectionId": connection_id,
                "connectedAt": now,
            }
        )
        return {
            "statusCode": 200,
            "body": "Connected."
        }
    except Exception as e:
        print("Error saving connection:", e)
        return {
            "statusCode": 500,
            "body": "Failed to connect."
        }