#!/bin/bash

# AWS Lambda deployment script for TTS Proxy
set -e

echo "🚀 Deploying TTS Proxy to AWS Lambda..."

# Configuration
FUNCTION_NAME="elevenlabs-tts-proxy"
REGION="us-east-1"  # Change to your preferred region
ROLE_NAME="lambda-execution-role"

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️ No .env file found. Make sure to set environment variables manually."
fi

# Validate required environment variables
if [ -z "$ELEVENLABS_API_KEY" ] || [ -z "$ELEVENLABS_VOICE_ID" ] || [ -z "$VAPI_SECRET" ]; then
    echo "❌ Missing required environment variables:"
    echo "   ELEVENLABS_API_KEY: ${ELEVENLABS_API_KEY:+Set}${ELEVENLABS_API_KEY:-Not set}"
    echo "   ELEVENLABS_VOICE_ID: ${ELEVENLABS_VOICE_ID:+Set}${ELEVENLABS_VOICE_ID:-Not set}"
    echo "   VAPI_SECRET: ${VAPI_SECRET:+Set}${VAPI_SECRET:-Not set}"
    echo "Please set these variables in your .env file or environment."
    exit 1
fi

# Create deployment package
echo "📦 Creating deployment package..."
rm -rf deployment-package
mkdir deployment-package

# Copy application files
cp main.py deployment-package/
cp lambda_function.py deployment-package/

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements-aws.txt -t deployment-package/

# Create deployment zip
echo "🗜️ Creating deployment archive..."
cd deployment-package
zip -r ../lambda-deployment.zip .
cd ..

# Check if function exists
echo "🔍 Checking if Lambda function exists..."
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION &>/dev/null; then
    echo "📝 Updating existing function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda-deployment.zip \
        --region $REGION
else
    echo "🆕 Creating new function..."
    
    # Create IAM role if it doesn't exist
    echo "🔐 Setting up IAM role..."
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }' 2>/dev/null || echo "Role already exists"
    
    # Attach basic execution policy
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole 2>/dev/null || echo "Policy already attached"
    
    # Get role ARN
    ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
    
    # Wait for role to be ready
    echo "⏳ Waiting for IAM role to be ready..."
    sleep 10
    
    # Create Lambda function
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://lambda-deployment.zip \
        --timeout 30 \
        --memory-size 512 \
        --region $REGION
fi

# Set environment variables
echo "⚙️ Setting environment variables..."
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment Variables="{
        \"ELEVENLABS_API_KEY\":\"$ELEVENLABS_API_KEY\",
        \"ELEVENLABS_VOICE_ID\":\"$ELEVENLABS_VOICE_ID\",
        \"ELEVENLABS_MODEL_ID\":\"${ELEVENLABS_MODEL_ID:-eleven_multilingual_v2}\",
        \"VAPI_SECRET\":\"$VAPI_SECRET\",
        \"DEMO_MODE\":\"${DEMO_MODE:-false}\"
    }" \
    --region $REGION

# Create API Gateway (if not exists)
echo "🌐 Setting up API Gateway..."
API_ID=""

# Check if API already exists
EXISTING_API=$(aws apigatewayv2 get-apis --region $REGION --query "Items[?Name=='elevenlabs-tts-api'].ApiId" --output text)

if [ -n "$EXISTING_API" ] && [ "$EXISTING_API" != "None" ]; then
    echo "📍 Using existing API Gateway: $EXISTING_API"
    API_ID=$EXISTING_API
else
    echo "🆕 Creating new API Gateway..."
    API_ID=$(aws apigatewayv2 create-api \
        --name "elevenlabs-tts-api" \
        --protocol-type HTTP \
        --query 'ApiId' --output text --region $REGION)
    
    # Create integration
    INTEGRATION_ID=$(aws apigatewayv2 create-integration \
        --api-id $API_ID \
        --integration-type AWS_PROXY \
        --integration-uri arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):function:$FUNCTION_NAME \
        --payload-format-version "2.0" \
        --query 'IntegrationId' --output text --region $REGION)
    
    # Create routes
    aws apigatewayv2 create-route \
        --api-id $API_ID \
        --route-key "ANY /" \
        --target integrations/$INTEGRATION_ID \
        --region $REGION
    
    aws apigatewayv2 create-route \
        --api-id $API_ID \
        --route-key "ANY /{proxy+}" \
        --target integrations/$INTEGRATION_ID \
        --region $REGION
    
    # Create stage
    aws apigatewayv2 create-stage \
        --api-id $API_ID \
        --stage-name "prod" \
        --auto-deploy \
        --region $REGION
fi

# Add Lambda permission for API Gateway
echo "🔐 Setting up API Gateway permissions..."
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id api-gateway-invoke-$(date +%s) \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$(aws sts get-caller-identity --query Account --output text):$API_ID/*" \
    --region $REGION 2>/dev/null || echo "Permission already exists"

echo ""
echo "✅ Deployment complete!"
echo "🔗 API Gateway URL: https://$API_ID.execute-api.$REGION.amazonaws.com"
echo "💰 Estimated cost: $1-5/month for typical usage"
echo ""
echo "🧪 Test your deployment:"
echo "curl -X POST https://$API_ID.execute-api.$REGION.amazonaws.com/tts \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"X-VAPI-SECRET: $VAPI_SECRET\" \\"
echo "  -d '{\"message\":{\"type\":\"voice-request\",\"text\":\"שלום עולם\",\"sampleRate\":24000}}' \\"
echo "  --output test-audio.pcm"
echo ""

# Cleanup
rm -rf deployment-package lambda-deployment.zip

echo "🧹 Cleanup complete!"
