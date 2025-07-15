# Hebrew Male Voice Configuration Guide

## ✅ Current Configuration (Updated)
- **Voice**: `he-IL-Wavenet-B` (Male, High Quality)
- **Language**: `he-IL` (Hebrew - Israel)
- **Type**: WaveNet (Neural Network - Best Quality)

## 🎙️ Available Hebrew Male Voices (Ranked by Quality)

### 1. he-IL-Wavenet-B ⭐ (RECOMMENDED - CURRENT)
- **Type**: WaveNet Neural
- **Quality**: Highest
- **Gender**: Male
- **Natural**: Very natural sounding
- **Use**: Best for production

### 2. he-IL-Wavenet-D ⭐
- **Type**: WaveNet Neural  
- **Quality**: Highest
- **Gender**: Male
- **Natural**: Very natural sounding
- **Use**: Alternative high-quality option

### 3. he-IL-Standard-B
- **Type**: Standard
- **Quality**: Good
- **Gender**: Male
- **Natural**: Less natural than WaveNet
- **Use**: Budget-friendly option

### 4. he-IL-Standard-D
- **Type**: Standard
- **Quality**: Good
- **Gender**: Male
- **Natural**: Less natural than WaveNet
- **Use**: Budget-friendly alternative

## 🔧 How to Change Voice

### For Local Development:
Edit `.env` file:
```
VOICE_NAME=he-IL-Wavenet-B
```

### For AWS Lambda:
Update environment variable:
```bash
aws lambda update-function-configuration \
  --function-name deepdub-tts-proxy \
  --environment "Variables={VOICE_NAME=he-IL-Wavenet-B,...}"
```

## 📊 Voice Quality Comparison

| Voice | Type | Quality | Naturalness | Cost |
|-------|------|---------|-------------|------|
| he-IL-Wavenet-B | Neural | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Higher |
| he-IL-Wavenet-D | Neural | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Higher |
| he-IL-Standard-B | Standard | ⭐⭐⭐ | ⭐⭐⭐ | Lower |
| he-IL-Standard-D | Standard | ⭐⭐⭐ | ⭐⭐⭐ | Lower |

## 🎯 Recommendation
**Use `he-IL-Wavenet-B`** (currently configured) for the best Hebrew male voice quality. This voice provides:
- Natural pronunciation
- Clear articulation
- Professional sound quality
- Good emotional expression

## 🧪 Testing
Test files generated:
- `test_male_voice.pcm` - Local test
- `lambda_male_voice_test.pcm` - Lambda test

Both show the new male voice is working correctly!
