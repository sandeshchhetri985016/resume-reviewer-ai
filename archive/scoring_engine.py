import re

KEYWORDS = [
    "Personal Care", "Disability Support", "Aged Care",
    "NDIS", "Infection Control", "Manual Handling",
    "Dementia Care", "Care Plan", "Medication"
]

def score_resume(text: str):
    text_lower = text.lower()

    # 1. Keyword score (0–30)
    keyword_hits = sum(1 for k in KEYWORDS if k.lower() in text_lower)
    keyword_score = int((keyword_hits / len(KEYWORDS)) * 30)

    # 2. Experience score (0–25)
    experience_years = len(re.findall(r"20\d{2}", text))
    experience_score = min(experience_years * 3, 25)

    # 3. Clarity score (0–15)
    clarity_score = 15 if "•" in text or "-" in text else 10

    # 4. Impact score (0–15)
    impact_keywords = ["achieved", "improved", "reduced", "increased"]
    impact_hits = sum(1 for k in impact_keywords if k in text_lower)
    impact_score = min(impact_hits * 5, 15)

    # 5. Structure score (0–15)
    sections = ["experience", "skills", "education"]
    structure_score = sum(3 for s in sections if s in text_lower)

    total = keyword_score + experience_score + clarity_score + impact_score + structure_score

    return {
        "score": min(total, 100),
        "breakdown": {
            "keywords": keyword_score,
            "experience": experience_score,
            "clarity": clarity_score,
            "impact": impact_score,
            "structure": structure_score
        }
    }