# Troubleshooting Guide

## Common Issues & Solutions

### 1. "API Key Missing" Error on Startup

**What you see:**
```
❌ API Key Missing

Set your OpenRouter API key before running this app:

`OPENROUTER_API_KEY=sk-or-v1-xxxxx`
```

**Causes:**
- `OPENROUTER_API_KEY` environment variable not set
- Empty or invalid key

**Solutions:**

**Local (development):**
```bash
# Create .env file
echo "OPENROUTER_API_KEY=sk-or-v1-xxxxx" > .env

# Run app
streamlit run app.py
```

**Railway/Render:**
1. Go to your deployment dashboard
2. Find "Variables" or "Environment" section
3. Add `OPENROUTER_API_KEY=sk-or-v1-xxxxx`
4. Save and redeploy

**Docker:**
```bash
docker run -e OPENROUTER_API_KEY=sk-or-v1-xxxxx ...
```

---

### 2. "File too large" or "File too small" Errors

**What you see:**
```
❌ File Error: File too large (12.5MB > 10MB). Max size: 10MB.
```

**Causes:**
- PDF file exceeds 10MB limit
- File is corrupted or not actually a PDF

**Solutions:**
1. Compress PDF (use online tools or local: `gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -o output.pdf input.pdf`)
2. Split multi-page PDFs into smaller files
3. Use online PDF compression: https://smallpdf.com/compress-pdf

**To change limit:** Edit `app.py`, line ~160:
```python
MAX_FILE_SIZE_MB = 10  # Change to 15, 20, etc.
```

---

### 3. "PDF corrupted or unreadable" Error

**What you see:**
```
❌ PDF Error: PDF corrupted or unreadable: [error details]
```

**Causes:**
- PDF file is corrupted
- File is not actually a PDF (wrong extension)
- OCR-heavy PDFs with unsupported encoding

**Solutions:**
1. Try opening PDF in Adobe Reader locally—if it doesn't open, it's corrupted
2. Try recreating the PDF (copy text → paste into Word → save as PDF)
3. For scanned PDFs: try https://www.ilovepdf.com/repair_pdf

---

### 4. "All free AI models failed"

**What you see:**
```
❌ All free AI models failed. This is a temporary issue with the free tier service. 
Please try again in a few moments.
```

**Causes (in order of likelihood):**
1. OpenRouter free tier is temporarily down or rate-limited
2. Your API key is invalid or expired
3. Resume is too long (>50,000 characters)
4. Network connectivity issue

**Solutions:**

**Step 1:** Check OpenRouter status
- Visit https://status.openrouter.ai/ (if available)
- Or visit https://openrouter.ai/activity
- If all models show "❌", OpenRouter has an outage—wait 15-30 min

**Step 2:** Verify API key
```bash
# Test API key with curl
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer sk-or-v1-xxxxx"
```
Should return a list of models. If error, key is invalid.

**Step 3:** Shorten resume
- If resume is >50,000 chars, truncate it
- Check size: look at "Resume Length:" in logs

**Step 4:** Check logs
- Local: `logs/resume_app.json`
- Railway/Render: Dashboard → Logs tab
- Look for `"event": "log"` entries to see which models were tried

---

### 5. "Resume too short" or "Resume too long"

**What you see:**
```
❌ Validation Error: Resume too long (>50000 chars). Please shorten it.
```

**Limits:**
- Min: 100 characters (very short resume)
- Max: 50,000 characters (~10 pages)
- Job description max: 10,000 characters (~2 pages)

**Solutions:**
1. **If too short:** Add more details to resume (experience, skills, education)
2. **If too long:** 
   - Remove old/irrelevant experience
   - Condense descriptions
   - Focus on last 10 years of experience

**To change limits:** Edit `app.py`, lines ~158-161:
```python
MAX_RESUME_CHARS = 50000  # Change to 100000 for longer
MIN_RESUME_CHARS = 100    # Change to 50 for shorter
```

---

### 6. ChromaDB "Database locked" Error

**What you see:**
```
[RAG] Error: database is locked
```

**Causes:**
- Rare on single-instance (local or deployed)
- Usually happens if app crashes mid-write
- On deployed apps: previous container still running

**Solutions:**

**Local:**
1. Stop the app (Ctrl+C)
2. Wait 5 seconds
3. Restart: `streamlit run app.py`

**Deployed (Railway/Render):**
1. Go to dashboard
2. Click "Redeploy" or restart container
3. App auto-recovers from backup on next start

**Manual recovery:**
If restarting doesn't work, delete ChromaDB and let it re-index:
```bash
rm -rf chroma_db/
streamlit run app.py  # Will re-build index (~5 sec)
```

---

### 7. App Runs Slowly or "Takes Forever"

**What you see:**
- Streamlit spinner spins for >60 seconds
- "🧠 Building knowledge index..." takes minutes

**Causes:**
1. **First run:** App indexes 18 knowledge files (~5-10 sec on decent CPU)
2. **API latency:** OpenRouter models are slow on free tier (~10-30 sec)
3. **Slow internet:** Upload/download delays
4. **Low memory:** CPU/RAM constrained (Railway/Render free tier)

**Typical timelines:**
- First run: 15-20 sec (one-time indexing)
- Subsequent runs: 20-40 sec (API call + processing)
- On slow connection: +10-20 sec

**Solutions:**
1. **Be patient** on first run—it's normal
2. **Use wired internet** instead of WiFi
3. **Close other apps** to free up RAM
4. **Restart app** if it freezes (clear Streamlit cache: Ctrl+F5)

---

### 8. Logs Not Appearing or Downloaded Logs are Empty

**What you see:**
- "Download Debug Logs" button doesn't work
- Downloaded log file is empty

**Causes:**
- Logs directory doesn't exist
- Log file hasn't been written yet
- Permissions issue

**Solutions:**

**Local:**
```bash
# Check if logs exist
ls -la logs/

# If empty, run app once to generate logs
streamlit run app.py
# Upload a resume, then check logs again
```

**Deployed:**
- On Railway/Render free tier, logs are ephemeral (not persisted)
- To persist logs, use a paid plan with persistent disks
- View logs directly in Railway/Render dashboard instead

---

### 9. Upload a PDF, Nothing Happens (App Freezes)

**What you see:**
- Upload PDF
- Spinner shows "🧠 Building knowledge index..." forever
- No errors

**Causes:**
1. RAG engine is indexing (one-time, should be ~5 sec)
2. Network is very slow
3. App crashed silently

**Solutions:**
1. **Wait 30 seconds** first—it might be slow
2. Check browser console for errors (F12 → Console tab)
3. Check app logs in terminal/dashboard
4. Restart app and try again

---

### 10. Score Doesn't Make Sense (Too High / Too Low)

**What you see:**
- Resume gets 95/100 but seems wrong
- Resume gets 15/100 but looks good

**Causes:**
- Rubric is deterministic (no AI involved in scoring)
- Scoring is strict about structure/formatting
- Scoring values years of quantified experience

**The Rubric (what matters):**
1. **Formatting (15%):** Section headings, bullet points, contact info
2. **ATS Readiness (20%):** Keyword density, required sections
3. **Experience Quality (25%):** Years in roles, progression, consistency
4. **Achievements (20%):** Quantified metrics (%, $, team size)
5. **Skills Relevance (20%):** Skills section, education, soft+hard balance

**Improve score by:**
- ✅ Adding clear section headings (## Experience, ## Skills)
- ✅ Using bullet points (not paragraphs)
- ✅ Adding numbers ($, %, team sizes, metrics)
- ✅ Listing relevant skills
- ✅ Adding education section

**See breakdown:** Click "📏 Rubric Scoring" to view detailed scores per category

---

### 11. "No specific knowledge chunks matched the resume"

**What you see:**
```
No specific knowledge chunks matched the resume. Use general best practices.
```

**Causes:**
- Resume domain didn't match any of 18 career fields
- Domain classification failed

**Solution:**
This is expected for niche careers. The app will still provide general resume feedback.

**To add a new domain:**
1. Create `knowledge/your_domain.txt` with career guidance
2. Add domain to `DOMAIN_DESCRIPTIONS` in `rag_engine.py`
3. Restart app

---

### 12. ATS Gap Analysis Shows No Keywords

**What you see:**
```
Keyword Coverage: 0%
No critical missing keywords found
```

**Causes:**
1. Job description is too vague or conversational
2. Resume uses different terminology than JD
3. Both are very short

**Solutions:**
1. Use a more detailed JD (e.g., from LinkedIn)
2. Manually add relevant skills to resume
3. Use synonyms: "debugging" → add "troubleshooting", "problem-solving"

**Note:** ATS gap is **exact-string matching only** (not semantic). Works best on structured requirements, not marketing copy.

---

### 13. "Processing error" or Unexpected Errors

**What you see:**
```
❌ Processing error: [some error]
```

**Solutions:**
1. Check logs (see #8)
2. Try again—might be temporary
3. Report the error on GitHub with:
   - Error message
   - Logs from `logs/resume_app.json`
   - What you were doing when it happened

---

## How to Get Help

1. **Check this guide** — most issues are here
2. **View logs** — `logs/resume_app.json` (local) or dashboard (deployed)
3. **Restart app** — fixes most temporary issues
4. **Check OpenRouter status** — https://openrouter.ai/
5. **Report bug on GitHub** — include logs and error details

---

## Advanced Debugging

### Enable Verbose Logging
App automatically logs to `logs/resume_app.json` in JSON format.

**View logs:**
```bash
# Local
tail -f logs/resume_app.json | jq .

# Or view raw
cat logs/resume_app.json
```

### Test RAG Pipeline
```bash
python scripts/rag_demo.py
```

### Test ATS Scoring
```bash
python scripts/ats_demo.py
```

### Test Raw API
```bash
# Set API key first
export OPENROUTER_API_KEY=sk-or-v1-xxxxx

python -c "
from openai import OpenAI
client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key='sk-or-v1-xxxxx')
resp = client.chat.completions.create(
    model='openrouter/free',
    messages=[{'role': 'user', 'content': 'Say hello'}]
)
print(resp.choices[0].message.content)
"
```

---

**Still stuck?** Open an issue on GitHub with logs attached!
