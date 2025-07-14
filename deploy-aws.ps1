# AWS Lambda deployment script for Deepdub TTS Proxy (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying Deepdub TTS Proxy to AWS Lambda..." -ForegroundColor Green

# Configuration
$FUNCTION_NAME = "deepdub-tts-proxy"
$REGION = "us-east-1"  # Change to your preferred region
$ROLE_NAME = "lambda-execution-role"

# Load environment variables from .env file
if (Test-Path ".env") {
    Write-Host "📝 Loading environment variables from .env file..." -ForegroundColor Yellow
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
        }
    }
} else {
    Write-Host "⚠️ No .env file found. Make sure to set environment variables manually." -ForegroundColor Yellow
}

# Get environment variables
$DEEPDUB_API_KEY = $env:DEEPDUB_API_KEY
$DEEPDUB_VOICE_PROMPT_ID = $env:DEEPDUB_VOICE_PROMPT_ID
$VAPI_SECRET = if ($env:VAPI_SECRET) { $env:VAPI_SECRET } else { "deepdub-secret-2025" }
$DEMO_MODE = if ($env:DEMO_MODE) { $env:DEMO_MODE } else { "false" }

# Validate required environment variables
if (-not $DEEPDUB_API_KEY -or -not $DEEPDUB_VOICE_PROMPT_ID -or -not $VAPI_SECRET) {
    Write-Host "❌ Missing required environment variables:" -ForegroundColor Red
    Write-Host "   DEEPDUB_API_KEY: $(if ($DEEPDUB_API_KEY) { 'Set' } else { 'Not set' })" -ForegroundColor Red
    Write-Host "   DEEPDUB_VOICE_PROMPT_ID: $(if ($DEEPDUB_VOICE_PROMPT_ID) { 'Set' } else { 'Not set' })" -ForegroundColor Red
    Write-Host "   VAPI_SECRET: $(if ($VAPI_SECRET) { 'Set' } else { 'Not set' })" -ForegroundColor Red
    Write-Host "Please set these variables in your .env file or environment." -ForegroundColor Red
    exit 1
}

# Create deployment package
Write-Host "📦 Creating deployment package..." -ForegroundColor Yellow
if (Test-Path "deployment-package") { Remove-Item -Recurse -Force "deployment-package" }
New-Item -ItemType Directory -Name "deployment-package" | Out-Null

# Copy application files
Copy-Item "main.py" "deployment-package/"
Copy-Item "lambda_function.py" "deployment-package/"

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements-aws.txt -t deployment-package/

# Create deployment zip
Write-Host "🗜️ Creating deployment archive..." -ForegroundColor Yellow
Compress-Archive -Path "deployment-package/*" -DestinationPath "lambda-deployment.zip" -Force

# Check if function exists
Write-Host "🔍 Checking if Lambda function exists..." -ForegroundColor Yellow
$functionExists = $false
try {
    aws lambda get-function --function-name $FUNCTION_NAME --region $REGION | Out-Null
    $functionExists = $true
} catch {}

if ($functionExists) {
    Write-Host "📝 Updating existing function..." -ForegroundColor Green
    aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file fileb://lambda-deployment.zip --region $REGION
} else {
    Write-Host "🆕 Creating new function..." -ForegroundColor Green
    
    # Create IAM role if it doesn't exist
    Write-Host "🔐 Setting up IAM role..." -ForegroundColor Yellow
    $rolePolicy = @"
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}
"@
    
    try {
        aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document $rolePolicy | Out-Null
    } catch {
        Write-Host "Role already exists" -ForegroundColor Yellow
    }
    
    # Attach basic execution policy
    try {
        aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole | Out-Null
    } catch {
        Write-Host "Policy already attached" -ForegroundColor Yellow
    }
    
    # Get role ARN
    $ROLE_ARN = aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text
    
    # Wait for role to be ready
    Write-Host "⏳ Waiting for IAM role to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Create Lambda function
    aws lambda create-function --function-name $FUNCTION_NAME --runtime python3.11 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://lambda-deployment.zip --timeout 30 --memory-size 512 --region $REGION
}

# Set environment variables
Write-Host "⚙️ Setting environment variables..." -ForegroundColor Yellow
$envVars = @{
    DEEPDUB_API_KEY = $DEEPDUB_API_KEY
    DEEPDUB_VOICE_PROMPT_ID = $DEEPDUB_VOICE_PROMPT_ID
    VAPI_SECRET = $VAPI_SECRET
    DEMO_MODE = $DEMO_MODE
} | ConvertTo-Json -Compress

aws lambda update-function-configuration --function-name $FUNCTION_NAME --environment "Variables=$envVars" --region $REGION

# Create API Gateway
Write-Host "🌐 Setting up API Gateway..." -ForegroundColor Yellow
$API_ID = ""

# Check if API already exists
$EXISTING_API = aws apigatewayv2 get-apis --region $REGION --query "Items[?Name=='deepdub-tts-api'].ApiId" --output text

if ($EXISTING_API -and $EXISTING_API -ne "None") {
    Write-Host "📍 Using existing API Gateway: $EXISTING_API" -ForegroundColor Green
    $API_ID = $EXISTING_API
} else {
    Write-Host "🆕 Creating new API Gateway..." -ForegroundColor Green
    $API_ID = aws apigatewayv2 create-api --name "deepdub-tts-api" --protocol-type HTTP --query 'ApiId' --output text --region $REGION
    
    # Get account ID
    $ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
    
    # Create integration
    $INTEGRATION_ID = aws apigatewayv2 create-integration --api-id $API_ID --integration-type AWS_PROXY --integration-uri "arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:$FUNCTION_NAME" --payload-format-version "2.0" --query 'IntegrationId' --output text --region $REGION
    
    # Create routes
    aws apigatewayv2 create-route --api-id $API_ID --route-key "ANY /" --target "integrations/$INTEGRATION_ID" --region $REGION | Out-Null
    aws apigatewayv2 create-route --api-id $API_ID --route-key "ANY /{proxy+}" --target "integrations/$INTEGRATION_ID" --region $REGION | Out-Null
    
    # Create stage
    aws apigatewayv2 create-stage --api-id $API_ID --stage-name "prod" --auto-deploy --region $REGION | Out-Null
}

# Add Lambda permission for API Gateway
Write-Host "🔐 Setting up API Gateway permissions..." -ForegroundColor Yellow
$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
$statementId = "api-gateway-invoke-$(Get-Date -Format 'yyyyMMddHHmmss')"

try {
    aws lambda add-permission --function-name $FUNCTION_NAME --statement-id $statementId --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*" --region $REGION | Out-Null
} catch {
    Write-Host "Permission already exists" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "🔗 API Gateway URL: https://$API_ID.execute-api.$REGION.amazonaws.com" -ForegroundColor Cyan
Write-Host "💰 Estimated cost: $1-5/month for typical usage" -ForegroundColor Green
Write-Host ""
Write-Host "🧪 Test your deployment:" -ForegroundColor Yellow
Write-Host "curl -X POST https://$API_ID.execute-api.$REGION.amazonaws.com/tts \\" -ForegroundColor Gray
Write-Host "  -H `"Content-Type: application/json`" \\" -ForegroundColor Gray
Write-Host "  -H `"X-VAPI-SECRET: $VAPI_SECRET`" \\" -ForegroundColor Gray
Write-Host "  -d '{`"message`":{`"type`":`"voice-request`",`"text`":`"שלום עולם`",`"sampleRate`":24000}}' \\" -ForegroundColor Gray
Write-Host "  --output test-audio.pcm" -ForegroundColor Gray
Write-Host ""

# Cleanup
Remove-Item -Recurse -Force "deployment-package"
Remove-Item -Force "lambda-deployment.zip"

Write-Host "🧹 Cleanup complete!" -ForegroundColor Green
