import json

def validate_json(raw):
    try:
        data = json.loads(raw)

        required = ["summary", "strengths", "weaknesses", "improvements"]
        for r in required:
            if r not in data:
                raise ValueError(f"Missing field: {r}")

        return data

    except Exception as e:
        return None