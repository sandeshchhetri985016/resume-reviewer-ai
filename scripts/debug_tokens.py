from scoring import extract_keywords, normalize_tech_text
s = 'Responsibilities include building and maintaining REST APIs.'
print('normalized:', normalize_tech_text(s))
print('keywords:', extract_keywords(s, top_n=50))
