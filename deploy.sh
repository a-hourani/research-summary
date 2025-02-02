#!/bin/bash

# Default values
PACKAGE=false
DEPLOY=false
TEARDOWN=false
S3_BUCKET=""

# Get AWS Region
AWS_REGION=$(aws configure get region)
if [[ -z "$AWS_REGION" ]]; then
    echo "AWS region is not set. Please configure AWS CLI or set AWS_REGION manually."
    exit 1
fi

# Usage function
usage() {
    echo "Usage: $0 [-p|--package] [-d|--deploy] [-t|--teardown] -b|--bucket <S3_BUCKET>"
    exit 1
}


# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -p|--package) PACKAGE=true ;;
        -d|--deploy) DEPLOY=true ;;
        -t|--teardown) TEARDOWN=true ;;
        -b|--bucket)
            S3_BUCKET="$2"
            shift ;;
        *) usage ;;
    esac
    shift
done

# Ensure an S3 bucket is provided if packaging
if [[ "$PACKAGE" = true && -z "$S3_BUCKET" ]]; then
    echo "Error: S3 bucket must be provided with -b|--bucket when packaging."
    usage
fi

# Define constants
LAMBDA_DIR="lambda"
PACKAGE_DIR="package"
ZIP_FILE="lambda.zip"
STACK_NAME="arxiv-summarizer"

if [[ "$PACKAGE" = true ]]; then
    echo "Packaging Lambda function..."
    
    # Step 1: Navigate to the lambda directory
    cd "$LAMBDA_DIR" || { echo "Failed to navigate to $LAMBDA_DIR"; exit 1; }

    # Step 2: Create the package directory
    mkdir -p "$PACKAGE_DIR"

    # Step 3: Install dependencies into the package directory
    pip install \
        --platform manylinux2014_x86_64 \
        --target "$PACKAGE_DIR" \
        --implementation cp \
        --python-version 3.9 \
        --only-binary=:all: \
        -r requirements.txt || { echo "Failed to install dependencies"; exit 1; }

    # Step 4: Copy Lambda function and prompt file into the package directory
    cp requestor_lambda_function.py lambda_function.py md_to_html.py prompt.txt template.html "$PACKAGE_DIR/" || { echo "Failed to copy files"; exit 1; }

    # Step 5: Zip the package directory
    cd "$PACKAGE_DIR" || { echo "Failed to navigate to $PACKAGE_DIR"; exit 1; }
    zip -r "../$ZIP_FILE" . || { echo "Failed to create zip file"; exit 1; }
    cd ..

    # Step 6: Upload to S3
    echo "Uploading to S3 bucket: $S3_BUCKET..."
    aws s3 cp "$ZIP_FILE" "s3://$S3_BUCKET/$ZIP_FILE" || { echo "Failed to upload to S3"; exit 1; }

    # Step 7: Clean up
    rm -rf "$PACKAGE_DIR" "$ZIP_FILE"

    # Step 8: Return to the root directory
    cd ..
    echo "Lambda package created and uploaded successfully."
fi

if [[ "$TEARDOWN" = true ]]; then
    echo "Tearing down CloudFormation stack..."
    aws cloudformation delete-stack --stack-name "$STACK_NAME" || { echo "Failed to delete CloudFormation stack"; exit 1; }
    echo "CloudFormation stack deletion initiated."
fi

if [[ "$DEPLOY" = true ]]; then
    echo "Deploying CloudFormation stack..."
    aws cloudformation deploy \
        --template-file cloudformation.yaml \
        --stack-name "$STACK_NAME" \
        --capabilities CAPABILITY_NAMED_IAM \
        --parameter-overrides S3Bucket="$S3_BUCKET" || { echo "CloudFormation deployment failed"; exit 1; }
    echo "CloudFormation stack deployed successfully."

    API_ID=$(aws apigateway get-rest-apis \
            --region "$AWS_REGION" \
            --query "items[?name=='ArxivSummarizerAPI'].id" \
            --output text)

    if [[ -n "$API_ID" && "$API_ID" != "None" ]]; then
        API_URL="https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/summarize"
        echo "API Endpoint: $API_URL"
    else
        echo "Failed to retrieve API Gateway ID."
    fi

    # Fetch the API Key
    API_KEY=$(aws apigateway get-api-keys \
        --name-query "ArxivSummarizerApiKey" \
        --include-value \
        --query "items[0].value" \
        --output text)

    if [[ -n "$API_KEY" && "$API_KEY" != "None" ]]; then
        echo "API Key: $API_KEY"
    else
        echo "Failed to retrieve API Key."
    fi
fi

