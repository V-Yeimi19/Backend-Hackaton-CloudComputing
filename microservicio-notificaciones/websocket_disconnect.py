import json
import os
import boto3

CONNECTIONS_TABLE = os.environ["CONNECTIONS_TABLE"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(CONNECTIONS_TABLE)

def lambda_handler(event, context):
    print("Event OnDisconnect:", json.dumps(event))

    connection_id = event["requestContext"]["connectionId"]

    try:
        table.delete_item(
            Key={
                "connectionId": connection_id
            }
        )
        return {
            "statusCode": 200,
            "body": "Disconnected."
        }
    except Exception as e:
        print("Error deleting connection:", e)
        return {
            "statusCode": 500,
            "body": "Failed to disconnect."
        }
