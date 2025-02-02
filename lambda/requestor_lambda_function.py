import boto3
import uuid
import json
import os

BUCKET = os.environ['S3_BUCKET']
LAMBDA_ARN = os.environ['LAMBDA_ARN']

headers = {
        'Content-Type': 'application/json',
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Api-Key"
    }

def get_html_from_s3(file_key):
    s3 = boto3.client('s3')
    
    try:
        # Get the HTML file from S3
        file_obj = s3.get_object(Bucket=BUCKET, Key=file_key)
        html_content = file_obj['Body'].read().decode('utf-8')
        return html_content
    
    except Exception as e:
        raise e
    
def lambda_handler(event, context):
    print(event)    

    body = json.loads(event['body'])

    print(f"body: {body}")    

    arxiv_url = body.get("arxivUrl")
    request_id = body.get("requestId")

    if arxiv_url:
        print('requesting...')
        # request
        request_id = str(uuid.uuid4())
        lambda_client = boto3.client('lambda')

        response = lambda_client.invoke(
            FunctionName=LAMBDA_ARN,
            InvocationType='Event', 
            Payload=json.dumps({
                "requestId": request_id, 
                "arxivUrl": arxiv_url
                })
        )

        return {
                'statusCode': 200,
                'body': json.dumps({'request_id': request_id}),
                'headers': headers
            }

    elif request_id:
        print('polling...')
        try:
            file_key = f"results/{request_id}.html"
            html_content = get_html_from_s3(file_key)
            print("content found")
            return {
                'statusCode': 200,
                'body': json.dumps({'html': html_content}),
                'headers': headers
            }
        except:
            print('pending')
            return {
                'statusCode': 202,
                'body': json.dumps({'status': 'pending'}),
                'headers': headers
            }
