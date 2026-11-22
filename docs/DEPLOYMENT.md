# Deployment Guide: Resume Reviewer

This guide shows how to deploy the app to Railway or Render (both free tier).

## Prerequisites

- GitHub account with this repo
- OpenRouter API key (free tier: https://openrouter.ai)

## Option 1: Deploy to Railway (Recommended)

Railway is the simplest—they auto-detect the Dockerfile and just work.

### Steps

1. Go to https://railway.app
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Select this repository
4. Railway auto-detects the Dockerfile and builds automatically
5. Once deployed, go to **Settings** → **Variables**
6. Add: `OPENROUTER_API_KEY=sk-or-v1-xxxxx` (your actual key)
7. Click **"Redeploy"**
8. App is live! Check the domain in the Railway dashboard

### Environment Variables (Railway)
- `OPENROUTER_API_KEY` — Your OpenRouter API key (required)
- `STREAMLIT_SERVER_HEADLESS=true` — Already set in Dockerfile
- `STREAMLIT_LOGGER_LEVEL=info` — Already set in Dockerfile

### Logs
- View in Railway dashboard under the service logs tab
- JSON logs are also stored in `/app/logs/` (ephemeral on free tier)

---

## Option 2: Deploy to Render

Render also supports Docker, but requires a bit more setup.

### Steps

1. Go to https://render.com
2. Click **"New +"** → **"Web Service"**
3. Select **"Deploy an existing image"** or **"Connect to repository"**
4. If connecting to GitHub repo:
   - Select repository
   - Render reads `render.yaml` automatically
5. Set environment: `OPENROUTER_API_KEY=sk-or-v1-xxxxx`
6. Deploy

### Persistent Storage (Optional)
If you want logs to persist:
- Create a disk in Render dashboard, mount to `/app/logs`
- Render YAML handles this automatically

### Logs
- View in Render dashboard under "Logs" tab
- Local logs are in `/app/logs/resume_app.json`

---

## Option 3: Local Docker Deployment

Test locally before deploying to cloud.

```bash
# Build image
docker build -t resume-reviewer .

# Run with environment variable
docker run -p 8501:8501 \
  -e OPENROUTER_API_KEY=sk-or-v1-xxxxx \
  -v $(pwd)/chroma_db:/app/chroma_db \
  -v $(pwd)/logs:/app/logs \
  resume-reviewer

# App is at http://localhost:8501
```

Or use docker-compose:
```bash
# Set API key in .env first
echo "OPENROUTER_API_KEY=sk-or-v1-xxxxx" > .env

# Run
docker-compose up

# App is at http://localhost:8501
```

---

## Troubleshooting

### "API Key Missing" Error
**Solution:** Set `OPENROUTER_API_KEY` in your deployment environment (Railway/Render dashboard).

### App Crashes on Startup
**Check:**
1. Logs in Railway/Render dashboard
2. Is Python 3.11+ available?
3. Are all dependencies installed? (check requirements.txt)

### ChromaDB "Database locked" Error
**Solution:** This shouldn't happen on Railway/Render (single instance). If it does:
1. Force redeploy to restart the container
2. The app auto-recovers from backup on next start

### "All free AI models failed"
**Causes:**
- OpenRouter free tier is rate-limited or temporarily down
- Invalid API key
- Resume too long (try shortening it)

**Solution:** Wait a few minutes and try again. Check OpenRouter status at https://openrouter.io/

---

## Monitoring

### Health Checks
Both Railway and Render are configured with health checks at `/_stcore/health`.

### Logs
- **Railway:** Dashboard → Logs tab (live streaming)
- **Render:** Dashboard → Logs tab (live streaming)
- **Local:** `logs/resume_app.json` (JSON format)

### Key Metrics to Watch
- Startup time (should be <30s after first indexing)
- API response times (usually 10-30s)
- Error rate (should be <5%)

---

## Maintenance

### Updating Dependencies
1. Modify `requirements.txt`
2. Push to GitHub
3. Railway/Render auto-redeploy
4. Or manually redeploy in dashboard

### Backing Up Data
- ChromaDB: Auto-backed up on app startup to `chroma_db_backups/`
- Logs: Download from dashboard or `/app/logs/` if persistent disk enabled

### Scaling
- Current setup: single instance, 512MB RAM (free tier)
- If you need multi-user support later: migrate to PostgreSQL + async API (future sprint)

---

## Free Tier Limits

| Service | Railway | Render |
|---------|---------|--------|
| Max memory | 512 MB | 512 MB |
| Max CPU | 0.5 vCPU | Shared |
| Storage | Ephemeral | Ephemeral (optional disks) |
| Monthly uptime | ~95% | ~95% |
| Cost | Free | Free |

Apps on free tier may "spin down" after inactivity (~15min). This is normal.

---

## Next Steps

1. ✅ Deployed? Great! Test it by:
   - Uploading a test resume
   - Checking logs for errors
   - Testing with a job description

2. Want to customize?
   - Edit knowledge files in `knowledge/` → redeploy
   - Adjust rubric scoring in `scoring.py` → redeploy
   - Change UI colors in `app.py` → redeploy

3. Issues? Check:
   - Logs (Railway/Render dashboard)
   - GitHub issues in the repo
   - OpenRouter status (https://openrouter.io/)

---

**Questions?** Check the main README.md or review TECHNICAL_BLUEPRINT.md for architecture details.
