import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from scoring import analyze_ats_gap
import json

examples = []

# Example 1: Software Engineer
resume_se = '''
PROFESSIONAL SUMMARY
Software Engineer with 5+ years building backend services and APIs.

SKILLS
Python, Django, Flask, PostgreSQL, Docker, AWS (EC2, S3), Git, REST API

EXPERIENCE
Senior Software Engineer, Acme Corp
Jan 2020 - Present
- Built RESTful APIs in Python/Django serving 100k users
- Reduced API latency by 45% and improved test coverage to 90%
- Deployed services to AWS using Docker and CI/CD pipelines
'''

jd_se = '''
We are hiring a Software Engineer.
Must have: Python, AWS, Docker
Preferred: React, Kubernetes
Responsibilities include building and maintaining REST APIs and working with PostgreSQL.
'''
examples.append(("Software Engineer", resume_se, jd_se))

# Example 2: Data Scientist
resume_ds = '''
SKILLS
Python, pandas, scikit-learn, TensorFlow, SQL, Spark, AWS

EXPERIENCE
Data Scientist, DataCo
Feb 2018 - Present
- Developed ML models predicting churn with 0.82 AUC
- Built ETL pipelines with Spark and SQL
- Deployed models to AWS SageMaker
'''

jd_ds = '''
Data Scientist
Required: Python, SQL, machine learning, Spark
Nice to have: TensorFlow or PyTorch, AWS
Responsibilities: productionizing ML models and building ETL pipelines.
'''
examples.append(("Data Scientist", resume_ds, jd_ds))

# Example 3: Cloud Engineer
resume_cloud = '''
SKILLS
AWS (EC2, S3, Lambda), Terraform, Docker, Kubernetes, Linux, CI/CD

EXPERIENCE
Cloud Engineer, CloudWorks
Mar 2019 - Present
- Provisioned infrastructure with Terraform and managed Kubernetes clusters
- Implemented CI/CD pipelines and automated deployments
'''

jd_cloud = '''
Cloud Engineer
Must have: Terraform, AWS, Kubernetes
Preferred: Docker, CI/CD experience
Responsibilities: automate infra and manage cloud platforms.
'''
examples.append(("Cloud Engineer", resume_cloud, jd_cloud))

# Example 4: Nursing (non-technical domain)
resume_nurse = '''
SKILLS
Patient care, Medication administration, Wound care, Electronic Medical Records (EMR), Communication

EXPERIENCE
Registered Nurse, Mercy Hospital
Jan 2017 - Present
- Delivered patient-centered care on a 30-bed medical ward
- Administered medications and coordinated with multidisciplinary teams
'''

jd_nurse = '''
Registered Nurse
Required: Registered Nurse with experience in patient care and medication administration
Preferred: EMR experience, wound care
Responsibilities: provide bedside care, administer medications, document in EMR.
'''
examples.append(("Registered Nurse", resume_nurse, jd_nurse))

# Run examples
for title, resume, jd in examples:
    print("\n=== Example:", title, "===")
    res = analyze_ats_gap(resume, jd)
    print(json.dumps(res, indent=2))
