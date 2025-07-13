# AWS Lambda Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites
1. **AWS CLI installed and configured**:
   ```bash
   # Install AWS CLI (if not already installed)
   # Windows: Download from https://aws.amazon.com/cli/
   # Mac: brew install awscli
   # Linux: sudo apt install awscli
   
   # Configure AWS CLI
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, Region (us-east-1), and output format (json)
   ```

2. **Python and pip installed** (for installing dependencies)

3. **Environment variables set** (already done in your .env file ✅)

### Deployment Options

#### Option A: PowerShell (Windows - Recommended for you)
```powershell
# Run in PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\deploy-aws.ps1
```

#### Option B: Bash (Linux/Mac/WSL)
```bash
# Make script executable
chmod +x deploy-aws.sh

# Run deployment
./deploy-aws.sh
```

## 📋 Your Current Environment Variables

✅ **Already configured in your .env file:**
- `ELEVENLABS_API_KEY`: sk_10ee7f013abfae55c23f515f3d6f4842bb7b2ec17e48a63c
- `ELEVENLABS_VOICE_ID`: o2S4rL1CbE73BVNO97p6  
- `ELEVENLABS_MODEL_ID`: eleven_v3
- `VAPI_SECRET`: 1a66039a-9ff9-4f33-bd4f-4023692dd78e
- `DEMO_MODE`: false

## 🎯 What the deployment script does:

1. **📦 Packages your application** with all dependencies
2. **🔐 Creates IAM role** for Lambda execution
3. **⚡ Creates Lambda function** with your code
4. **🌐 Sets up API Gateway** as HTTP endpoint
5. **⚙️ Configures environment variables** from your .env file
6. **🔗 Returns your API URL** for testing

## 💰 Expected AWS Costs

| Usage Level | Monthly Cost | Details |
|-------------|--------------|---------|
| **Development** | $0-1 | < 1,000 requests |
| **Light Production** | $1-5 | 1,000-50,000 requests |
| **Medium Production** | $5-15 | 50,000-500,000 requests |

**Much cheaper than Render ($25/month)!**

## 🧪 Testing Your Deployment

After deployment, you'll get an API URL like:
`https://abc123def.execute-api.us-east-1.amazonaws.com`

Test with curl:
```bash
curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/tts \
  -H "Content-Type: application/json" \
  -H "X-VAPI-SECRET: 1a66039a-9ff9-4f33-bd4f-4023692dd78e" \
  -d '{"message":{"type":"voice-request","text":"שלום עולם","sampleRate":24000}}' \
  --output test-audio.pcm
```

## 🔧 Troubleshooting

### Common Issues:

1. **AWS CLI not configured**:
   ```bash
   aws configure
   # Enter your credentials
   ```

2. **Permission denied**:
   ```bash
   # Linux/Mac:
   chmod +x deploy-aws.sh
   
   # Windows PowerShell:
   Set-ExecutionPolicy RemoteSigned
   ```

3. **Missing dependencies**:
   ```bash
   pip install -r requirements-aws.txt
   ```

4. **Function already exists error**:
   - Script will automatically update existing function
   - Or delete and recreate: `aws lambda delete-function --function-name elevenlabs-tts-proxy`

### Monitor your function:
- **AWS Console** → Lambda → elevenlabs-tts-proxy → Monitor tab
- **CloudWatch Logs** for detailed error messages

## 🎯 Next Steps After Deployment

1. **Test the endpoint** with your actual VAPI integration
2. **Monitor costs** in AWS Billing dashboard  
3. **Set up CloudWatch alarms** for high usage (optional)
4. **Consider multiple regions** for global users (optional)

## 🔄 Updating Your Deployment

To update your code:
```bash
# Just run the deployment script again
./deploy-aws.ps1  # Windows
# or
./deploy-aws.sh   # Linux/Mac
```

The script will automatically update your existing Lambda function.

## 📞 Support

If you encounter issues:
1. Check the deployment script output for error messages
2. Verify AWS CLI configuration: `aws sts get-caller-identity`
3. Check CloudWatch logs in AWS Console
4. Ensure your .env file has all required variables

Your TTS proxy will be much more cost-effective on AWS Lambda! 🚀
