import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

print("Paste resume (press ENTER on empty line to finish):")

lines = []
while True:
    line = input()
    if line == "":
        break
    lines.append(line)

resume = "\n".join(lines)

print("\nResume received:")
print(resume)
print("Length:", len(resume))

prompt = f"""
You are an AI that returns ONLY raw JSON.

Do NOT use markdown.
Do NOT wrap in ```.

Return ONLY valid JSON.

Schema:
{{
  "strengths": [],
  "weaknesses": [],
  "score": 0
}}

Resume:
{resume}
"""

response = client.chat.completions.create(
    model="openrouter/free",
    messages=[
        {"role": "user", "content": prompt}
    ]
)

raw_output = response.choices[0].message.content

print("\nRaw output:")
print(raw_output)

# -----------------------------
# SAFE JSON CLEANING (important)
# -----------------------------
cleaned = re.sub(r"```json|```", "", raw_output).strip()

try:
    result = json.loads(cleaned)

    print("\nStrengths:")
    print(result["strengths"])

    print("\nWeaknesses:")
    print(result["weaknesses"])

    print("\nScore:", result["score"])

except json.JSONDecodeError:
    print("\n❌ Failed to parse JSON. Model output was not valid JSON.")