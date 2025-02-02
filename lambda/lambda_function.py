import os
import json
import boto3
import requests
import pdfplumber
from openai import OpenAI
from botocore.exceptions import ClientError
import io

from md_to_html import markdown_to_html

BUCKET = os.environ['S3_BUCKET']
SECRET_NAME = os.environ['SECRET_NAME']

secrets = boto3.client('secretsmanager')

def get_secret(secret_name):
    try:
        response = secrets.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])['private_key']
    except ClientError as e:
        raise e

def get_prompt():
    with open('prompt.txt', 'r') as f:
        return f.read()

def upload_file_to_s3(file_key, file_content, content_type):
    s3 = boto3.client('s3')
    
    try:
        s3.put_object(
            Bucket=BUCKET,
            Key=file_key,
            Body=file_content,
            ContentType=content_type  # Ensure it's served as an HTML file
        )
        return f"File successfully uploaded to s3://{BUCKET}/{file_key}"
    except Exception as e:
        return f"Error uploading file: {str(e)}"
    
def get_html_from_s3(file_key):
    s3 = boto3.client('s3')
    
    try:
        # Get the HTML file from S3
        file_obj = s3.get_object(Bucket=BUCKET, Key=file_key)
        html_content = file_obj['Body'].read().decode('utf-8')
        return html_content
    
    except Exception as e:
        return f"Error retrieving file: {str(e)}"
    

def lambda_handler(event, context):
    print(event)    
    try:
        request_id = event["requestId"]
        arxiv_url = event["arxivUrl"]
        file_key_html = f"results/{request_id}.html"
        file_key_md = f"results/{request_id}.md"


        # Get OpenAI API Key
        os.environ["OPENAI_API_KEY"] = get_secret(SECRET_NAME)
        
        # Convert arXiv URL to PDF URL
        pdf_url = arxiv_url.replace('/abs/', '/pdf/') + '.pdf'
        
        # Download PDF
        response = requests.get(pdf_url)
        response.raise_for_status()

        # Extract text from PDF
        text = ""
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        
        # Truncate text to fit model context
        truncated_text = text[:50000]

        print(f"original length: {len(text)}")
        print(f"truncated length: {len(truncated_text)}")

        # Get and format prompt
        prompt_template = get_prompt()
        prompt = prompt_template.replace('{$file_content}', truncated_text)
        
        client = OpenAI()

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": prompt
                    }
                ]
                }
            ],
            response_format={
                "type": "text"
            },
            temperature=1,
            max_completion_tokens=5000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        md_summary = response.choices[0].message.content

        print(f"md_summary preview: md_summary[:100]")

        line_breaks = '\n\n'
        md_summary += f'{line_breaks}[View original paper]({arxiv_url})'

        html_summary = markdown_to_html(md_summary)

        with open("template.html", "r", encoding="utf-8") as file:
            html_template = file.read()

        html_summary = html_template.replace("{{CONTENT}}", html_summary)

        print(f"html_summary preview: md_summary[:100]")
        
        upload_file_to_s3(
            file_key_html, 
            html_summary,
            'text/html'
        )
        
        upload_file_to_s3(
            file_key_md, 
            md_summary,
            'text/markdown'
        )
        
        return "done"
    
    except Exception as e:
        raise e
        
    
# if __name__ == "__main__":
#     print(
#         lambda_handler(
#                 {
#                     "body": "{\"arxivUrl\": \"https://arxiv.org/abs/2408.07712\"}"
#                 },
#                 None
#             )
#     )
    