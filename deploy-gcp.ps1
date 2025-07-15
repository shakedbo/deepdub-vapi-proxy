# Google Cloud TTS Lambda Deployment Script
Write-Host "🚀 Deploying Google Cloud TTS to AWS Lambda..." -ForegroundColor Green

# Check if files exist
$requiredFiles = @("main.py", "requirements.txt", "tts-to-vapi-0b203e1fbd41.json")
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Required file missing: $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ All required files found" -ForegroundColor Green

# Create deployment package
Write-Host "📦 Creating deployment package..." -ForegroundColor Yellow
Remove-Item "deployment.zip" -ErrorAction SilentlyContinue
Compress-Archive -Path $requiredFiles -DestinationPath "deployment.zip" -Force

if (Test-Path "deployment.zip") {
    Write-Host "✅ Deployment package created: deployment.zip" -ForegroundColor Green
    $size = (Get-Item "deployment.zip").Length / 1KB
    Write-Host "📊 Package size: $([math]::Round($size, 2)) KB" -ForegroundColor Cyan
} else {
    Write-Host "❌ Failed to create deployment package" -ForegroundColor Red
    exit 1
}

# Deploy to Lambda
Write-Host "🌩️ Updating Lambda function..." -ForegroundColor Yellow
try {
    aws lambda update-function-code --function-name deepdub-tts-proxy --zip-file fileb://deployment.zip
    Write-Host "✅ Lambda function code updated" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to update Lambda function: $_" -ForegroundColor Red
    exit 1
}

# Update environment variables
Write-Host "⚙️ Updating environment variables..." -ForegroundColor Yellow
try {
    aws lambda update-function-configuration --function-name deepdub-tts-proxy --environment Variables='{
        "GOOGLE_APPLICATION_CREDENTIALS": "tts-to-vapi-0b203e1fbd41.json",
        "VOICE_NAME": "he-IL-Wavenet-A", 
        "VOICE_LANGUAGE": "he-IL",
        "VAPI_SECRET": "1a66039a-9ff9-4f33-bd4f-4023692dd78e",
        "DEMO_MODE": "false"
    }'
    Write-Host "✅ Environment variables updated" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to update environment variables: $_" -ForegroundColor Red
}

# Test deployment
Write-Host "🧪 Testing deployment..." -ForegroundColor Yellow
Write-Host "Health endpoint: https://3wik39wypl.execute-api.us-east-1.amazonaws.com/health" -ForegroundColor Cyan
Write-Host "TTS endpoint: https://3wik39wypl.execute-api.us-east-1.amazonaws.com/tts" -ForegroundColor Cyan

Write-Host "🎉 Deployment completed!" -ForegroundColor Green
Write-Host "💡 Test with: python test_deepdub.py" -ForegroundColor Cyan
