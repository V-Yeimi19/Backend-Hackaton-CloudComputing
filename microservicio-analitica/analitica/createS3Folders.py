import boto3
import json
import urllib3

s3 = boto3.client('s3')
http = urllib3.PoolManager()

def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")
    
    response_data = {}
    
    try:
        if event['RequestType'] in ['Create', 'Update']:
            bucket_name = event['ResourceProperties']['BucketName']
            folders = event['ResourceProperties']['Folders']
            
            for folder in folders:
                print(f"Creating folder: {folder} in bucket: {bucket_name}")
                s3.put_object(Bucket=bucket_name, Key=folder)
            
            response_data['Message'] = f"Folders created successfully in {bucket_name}"
        
        elif event['RequestType'] == 'Delete':
            response_data['Message'] = "Delete operation - no action needed"
        
        send_response(event, context, "SUCCESS", response_data)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        response_data['Error'] = str(e)
        send_response(event, context, "FAILED", response_data)

def send_response(event, context, status, response_data):
    response_body = json.dumps({
        "Status": status,
        "Reason": f"See CloudWatch Log Stream: {context.log_stream_name}",
        "PhysicalResourceId": context.log_stream_name,
        "StackId": event['StackId'],
        "RequestId": event['RequestId'],
        "LogicalResourceId": event['LogicalResourceId'],
        "Data": response_data
    })
    
    headers = {'Content-Type': 'application/json'}
    
    http.request('PUT', event['ResponseURL'], 
                 body=response_body.encode('utf-8'),
                 headers=headers)