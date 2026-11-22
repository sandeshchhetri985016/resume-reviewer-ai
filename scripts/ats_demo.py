import sys, os
# Ensure project root is on sys.path when running from scripts/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)
from scoring import analyze_ats_gap

resume = '''
PROFESSIONAL EXPERIENCE
Software Engineer at Acme Corp

SKILLS
Python, Django, PostgreSQL, AWS, Docker

- Built REST APIs using Python and Django
- Deployed services on AWS EC2 and S3
- Containerized applications with Docker
'''

jd = '''
We are hiring a Software Engineer.
Must have: Python, AWS, Docker
Preferred: React, Kubernetes
Responsibilities include building and maintaining REST APIs.
'''

result = analyze_ats_gap(resume, jd)
import json
print(json.dumps(result, indent=2))
