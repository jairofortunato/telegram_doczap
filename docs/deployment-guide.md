# DocZap Deployment Guide - Railway with Nixpacks

## Overview

This document outlines the deployment strategy for the DocZap Multi-Platform Bot on Railway, including the transition from Docker to Nixpacks to resolve Docker Hub authentication issues.

## Deployment Evolution

### The Docker Hub Problem

Initially, the service used Docker with a standard `python:3.11-slim` base image. However, Railway experienced widespread Docker Hub authentication issues:

```
ERROR: failed to solve: python:3.11-slim: failed to resolve source metadata for
docker.io/library/python:3.11-slim: unexpected status from HEAD request to
https://registry-1.docker.io/v2/library/python/manifests/3.11-slim: 401 Unauthorized
```

This error occurred because:
- Railway's Docker build infrastructure couldn't authenticate with Docker Hub
- The issue affected multiple deployments across the platform
- Even successful configurations (like @prontodocbot) began failing

### The Solution: Nixpacks

We solved this by switching to **Nixpacks**, Railway's preferred build system that doesn't depend on Docker Hub:

```
Docker Hub Issues → Nixpacks Solution → Successful Deployment
```

## Current Deployment Architecture

### Nixpacks Configuration

#### **Primary Configuration** (`nixpacks.toml`)

```toml
[phases.setup]
nixPkgs = ["python311", "python311Packages.pip", "ffmpeg"]

[phases.install]
cmds = [
    "python -m pip install --upgrade pip",
    "pip install -r requirements.txt"
]

[start]
cmd = "uvicorn main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 300 --timeout-graceful-shutdown 300"

[variables]
PYTHONUNBUFFERED = "1"
PORT = "8000"
```

#### **Runtime Specification** (`runtime.txt`)
```
python-3.11
```

#### **Process Definition** (`Procfile`)
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 300 --timeout-graceful-shutdown 300
```

### Build Process

```
1. Railway detects nixpacks.toml
2. Downloads Nix packages (Python 3.11 + ffmpeg)
3. Runs install commands (pip install requirements)
4. Sets environment variables
5. Starts web process with uvicorn
```

### Key Advantages

#### **No External Dependencies**
- ✅ No Docker Hub authentication required
- ✅ Uses Railway's internal package management
- ✅ Faster, more reliable builds
- ✅ Better integration with Railway platform

#### **Same Functionality**
- ✅ Python 3.11 runtime
- ✅ FFmpeg for audio processing
- ✅ All Python dependencies
- ✅ Same performance characteristics

## Deployment Configuration

### File Structure

```
telegram-doczap/
├── nixpacks.toml           # Primary build configuration
├── runtime.txt             # Python version specification
├── Procfile               # Process definition (backup)
├── requirements.txt       # Python dependencies
├── main.py               # FastAPI application
├── services/             # Service layer
├── handlers/             # Message handlers
├── utils/                # Utility functions
└── docs/                 # Documentation
```

### Environment Variables

#### **Required Variables**

```bash
# Core Configuration
PORT=8000
PYTHONUNBUFFERED=1

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_APP_SECRET=your_app_secret
WHATSAPP_API_VERSION=v18.0

# Webhook Security
WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# External Services
AI_PROCESSOR_URL=https://saude-ai-processor-production-bebd.up.railway.app
WEB_APP_URL=https://prontuarioautomatico.vercel.app
```

#### **Setting Variables in Railway**

1. **Railway Dashboard** → Your Project → Variables
2. **Add each variable** with appropriate values
3. **Deploy** - Railway automatically restarts with new variables

### Health Monitoring

#### **Health Check Endpoint**

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "service": "doczap-multi-platform",
        "telegram_enabled": bool(BOT_TOKEN),
        "whatsapp_enabled": whatsapp_service.enabled,
        "bot_running": True,
        "timestamp": datetime.utcnow().isoformat()
    }
```

#### **Railway Health Checks**
- **Endpoint**: `/health`
- **Expected Response**: `200 OK` with JSON status
- **Timeout**: 30 seconds
- **Failure Action**: Automatic restart

## Deployment Process

### Automatic Deployment

#### **Git Integration**
1. **Connect Repository** to Railway project
2. **Push commits** to main branch
3. **Automatic triggering** of build process
4. **Nixpacks execution** (setup → install → start)
5. **Health check validation**
6. **Traffic routing** to new deployment

#### **Build Logs Example**

```
=========================
Using Detected nixpacks.toml
=========================

📦 Installing Nix packages: python311, python311Packages.pip, ffmpeg

🔧 Running install phase:
   python -m pip install --upgrade pip
   pip install -r requirements.txt

✅ Successfully installed:
   - fastapi>=0.104.0
   - uvicorn[standard]>=0.24.0
   - httpx==0.24.1
   - loguru>=0.7.2
   - [... other dependencies]

🚀 Starting application:
   uvicorn main:app --host 0.0.0.0 --port 8000

INFO: Started server process [1]
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Manual Deployment

#### **Railway CLI Method**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to project
railway link

# Deploy manually
railway up --detach
```

#### **Docker Alternative** (if needed)

If Docker deployment becomes necessary again, here's the working configuration:

```dockerfile
FROM python:3.11-slim

# Install ffmpeg for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

CMD uvicorn main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 300 --timeout-graceful-shutdown 300
```

## Performance Optimization

### Resource Configuration

#### **Railway Resource Limits**
```
CPU: 1 vCPU (shared)
Memory: 512 MB (expandable to 1GB)
Network: 100GB/month bandwidth
Storage: Ephemeral (container-based)
```

#### **Application Optimization**
- **Async I/O**: All HTTP requests use async/await
- **Connection Pooling**: httpx client with connection reuse
- **Timeout Management**: Long timeouts for medical processing
- **Memory Efficiency**: Minimal memory footprint

### Scaling Considerations

#### **Horizontal Scaling**
- **Stateless Design**: Service can run multiple instances
- **External State**: All persistent data in Supabase
- **Load Balancing**: Railway handles automatic load distribution

#### **Vertical Scaling**
- **Memory**: Increase for concurrent audio processing
- **CPU**: Scale for AI processing workloads
- **Bandwidth**: Monitor for high-volume deployments

## Monitoring and Observability

### Application Logging

#### **Log Levels**
```python
# Service initialization
logger.info("🤖 DocZap multi-platform bot initialized successfully")

# Request processing
logger.info(f"📨 Received WhatsApp webhook POST: {data}")
logger.debug(f"WhatsApp send_text URL: {repr(url)}")

# Error handling
logger.error(f"❌ Failed to send WhatsApp message: {result}")
```

#### **Railway Log Access**
```bash
# View live logs
railway logs

# View logs for specific service
railway logs --service=your-service-name

# Follow logs in real-time
railway logs --follow
```

### Performance Monitoring

#### **Key Metrics**
- **Response Time**: Webhook processing latency
- **Error Rate**: Failed API calls and processing errors
- **Throughput**: Messages processed per minute
- **Resource Usage**: CPU and memory utilization

#### **Health Check Monitoring**
```bash
# Test health endpoint
curl https://your-app.railway.app/health

# Expected response
{
  "status": "healthy",
  "service": "doczap-multi-platform",
  "telegram_enabled": true,
  "whatsapp_enabled": true,
  "bot_running": true,
  "timestamp": "2024-09-24T23:50:47.367Z"
}
```

## Troubleshooting

### Common Deployment Issues

#### **Build Failures**

**Nixpacks Package Not Found**
```
Error: package 'python311' not found
```
**Solution**: Check nixpacks.toml syntax and package names

**Python Dependencies Conflict**
```
Error: pip install failed
```
**Solution**: Review requirements.txt for version conflicts

#### **Runtime Issues**

**Environment Variable Missing**
```
ValueError: TELEGRAM_BOT_TOKEN environment variable is required
```
**Solution**: Set all required environment variables in Railway dashboard

**Port Binding Issues**
```
Error: Port 8000 already in use
```
**Solution**: Railway automatically assigns ports; ensure app uses `$PORT` variable

#### **Service Connectivity**

**External API Failures**
```
httpx.ConnectError: Connection failed
```
**Solution**: Check external service URLs and network connectivity

**Database Connection Issues**
```
Error: Failed to connect to Supabase
```
**Solution**: Verify Supabase URL and service role key

### Debug Techniques

#### **Local Testing**
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN=your_token
export WHATSAPP_ACCESS_TOKEN=your_token

# Run locally
uvicorn main:app --reload --port 8000
```

#### **Railway Shell Access**
```bash
# Access running container
railway shell

# Check environment
env | grep -E "(TELEGRAM|WHATSAPP|SUPABASE)"

# Check process status
ps aux | grep uvicorn
```

#### **Log Analysis**
```bash
# Search for specific errors
railway logs | grep "ERROR"

# Filter WhatsApp-related logs
railway logs | grep "WhatsApp"

# Monitor real-time activity
railway logs --follow
```

## Security Best Practices

### Environment Security

#### **Token Management**
- **Never commit tokens** to version control
- **Use Railway environment variables** for all secrets
- **Rotate tokens regularly** (especially WhatsApp access tokens)
- **Monitor token expiration** and set up alerts

#### **Webhook Security**
```python
# WhatsApp signature verification
def verify_whatsapp_signature(body: bytes, signature: str) -> bool:
    app_secret = os.getenv('WHATSAPP_APP_SECRET', '')
    expected_signature = 'sha256=' + hmac.new(
        app_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)
```

#### **Network Security**
- **HTTPS only**: All external API calls use HTTPS
- **Input validation**: Sanitize all user inputs
- **Rate limiting**: Implement API rate limiting
- **Error handling**: Don't expose internal details in errors

### Deployment Security

#### **Access Control**
- **Railway team access**: Limit deployment permissions
- **Git repository**: Protect main branch with reviews
- **Environment variables**: Audit access to sensitive variables

#### **Monitoring**
- **Failed login attempts**: Monitor authentication failures
- **Unusual traffic patterns**: Alert on traffic spikes
- **Error rate monitoring**: Alert on high error rates

## Backup and Recovery

### Data Backup Strategy

#### **Application Code**
- **Git repository**: Primary backup in version control
- **Railway deployments**: Automatic deployment history
- **Local development**: Keep local copies synchronized

#### **Configuration**
- **Environment variables**: Document all required variables
- **Service configuration**: Keep nixpacks.toml and configs in git
- **Documentation**: Maintain deployment documentation

### Disaster Recovery

#### **Service Restoration**
1. **Redeploy** from Git repository
2. **Restore environment variables** from documentation
3. **Verify health checks** are passing
4. **Test core functionality** (send/receive messages)

#### **Rollback Strategy**
```bash
# Railway CLI rollback
railway rollback

# Or redeploy previous commit
git checkout previous-commit
railway up
```

## Future Improvements

### Planned Enhancements

#### **Infrastructure**
- **Multi-region deployment** for improved latency
- **Database connection pooling** for better performance
- **Redis integration** for session caching
- **Message queue system** for high-volume processing

#### **Monitoring**
- **APM integration** (DataDog, New Relic)
- **Custom metrics** dashboard
- **Alerting system** for critical failures
- **Performance profiling** for optimization

#### **Security**
- **Secrets management** improvement
- **Network security** hardening
- **Compliance monitoring** for healthcare data
- **Audit logging** enhancement

---

*This deployment guide reflects the current Railway deployment strategy as of September 2024, including the successful transition from Docker to Nixpacks and all associated configurations.*