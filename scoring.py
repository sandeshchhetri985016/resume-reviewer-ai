"""
scoring.py — Deterministic Rubric-Based Resume Scoring

Instead of relying solely on the LLM to assign scores, this module
pre-analyzes the resume text using regex patterns and heuristics,
then produces a rubric-based score that is more defensible and
less arbitrary.

The LLM still generates qualitative feedback (strengths, weaknesses,
improvements), but the SCORE comes from this rubric.

Scoring Categories (weighted):
  - Formatting:         15%  (sections, bullets, structure)
  - ATS Readiness:      20%  (keyword density, job title, sections)
  - Experience Quality: 25%  (years, roles, progression)
  - Achievement Density: 20% (quantified bullets vs total)
  - Skills Relevance:   20%  (domain keyword match)
"""

import re
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import Counter

# Synonyms for normalizing tech terms across resumes and JDs
# Skill Concept Ontology — maps surface phrases to canonical concepts
# This is the "concept layer" missing from pure keyword matching.
# Both JDs and resumes are normalized through this before comparison.
SKILL_CONCEPTS = {
    # Cloud / Infrastructure
    "aws": ["aws", "amazon web services", "amazon webservices", "aws cloud", "amazon s3", "simple storage service", "ec2", "elastic compute cloud", "lambda"],
    "azure": ["azure", "microsoft azure", "azure cloud"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "docker": ["docker", "containerization", "container", "containerised", "containerized"],
    "kubernetes": ["kubernetes", "k8s", "kube"],
    "terraform": ["terraform", "infrastructure as code", "cloudformation"],
    "ci_cd": ["ci/cd", "cicd", "ci cd pipeline", "continuous integration", "continuous deployment", "continuous delivery"],
    # OS / Systems
    "windows_server": ["windows server", "windows server administration", "server 2019", "server 2022", "active directory", "ad ds", "group policy"],
    "windows_client": ["windows 10", "windows 11", "windows os", "windows operating system", "workstation"],
    "linux": ["linux", "redhat", "rhel", "ubuntu", "centos", "debian", "suse"],
    # Networking
    "networking": ["networking", "network", "network infrastructure", "network troubleshooting", "lan", "wan", "tcp/ip", "dns", "dhcp"],
    "firewall": ["firewall", "firewall rules", "firewall administration", "palo alto", "cisco asa", "fortinet", "fortigate"],
    "vlan": ["vlan", "virtual lan", "vlan configuration"],
    "vpn": ["vpn", "virtual private network", "site to site", "remote access"],
    "switching": ["switching", "network switching", "switch configuration", "cisco switch"],
    "routing": ["routing", "router", "network routing", "bgp", "ospf", "bgp"],
    # Cloud storage / backup
    "storage": ["storage", "backup", "backup monitoring", "disaster recovery", "s3", "blob storage", "nas", "san"],
    # Identity / Auth
    "identity": ["jwt", "jwt authentication", "oauth", "sso", "single sign on", "active directory", "azure ad", "password policy"],
    # Monitoring / Observability
    "monitoring": ["monitoring", "prometheus", "grafana", "new relic", "datadog", "observability", "health monitoring", "spring actuator"],
    # Databases
    "sql": ["sql", "mysql", "postgresql", "postgres", "database", "relational database", "flyway"],
    "nosql": ["nosql", "mongodb", "dynamodb", "firestore", "cassandra"],
    # Programming Languages
    "python": ["python", "django", "flask", "fastapi"],
    "java": ["java", "spring", "spring boot", "hibernate"],
    "javascript": ["javascript", "js", "node", "nodejs", "express", "react", "vue", "angular"],
    "typescript": ["typescript", "ts"],
    "php": ["php", "laravel", "codeigniter"],
    # Frontend
    "react": ["react", "react js", "reactjs", "next js", "nextjs"],
    "html_css": ["html", "css", "html5", "css3", "sass", "scss"],
    # Mobile
    "react_native": ["react native", "expo"],
    "ios": ["ios", "swift", "swiftui", "xcode"],
    "android": ["android", "kotlin", "java"],
    # ITSM / Support
    "itsm": ["itsm", "itil", "service desk", "help desk", "helpdesk", "ticket", "ticketing", "freshservice", "zendesk", "jira"],
    "office365": ["office365", "office 365", "microsoft 365", "o365", "exchange", "exchange server", "sharepoint"],
    "teamviewer": ["teamviewer", "remote support", "remote desktop", "rdp"],
    # Soft skills / methods
    "agile": ["agile", "scrum", "kanban", "sdlc", "software development life cycle"],
    "communication": ["communication", "verbal", "written", "interpersonal", "stakeholder"],
}

SYNONYM_MAP = {
    "amazon web services": "aws",
    "amazon webservices": "aws",
    "aws cloud": "aws",
    "amazon s3": "s3",
    "simple storage service": "s3",
    "ec2": "aws ec2",
    "elastic compute cloud": "aws ec2",
    "lambda": "aws lambda",
    "javascript": "js",
    "typescript": "ts",
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "project management": "project manager",
    "pm": "project manager",
    "amazon web services certified": "aws certified",
    "software engineering": "software engineer",
    "software developer": "software engineer",
    "frontend": "front end",
    "front-end": "front end",
    "backend": "back end",
    "back-end": "back end",
    "fullstack": "full stack",
    "full-stack": "full stack",
    "machine learning": "machine learning ml",
    "artificial intelligence": "ai",
    "deep learning": "deep learning dl",
    "react": "react js",
    "reactjs": "react js",
    "nodejs": "node js",
    "nextjs": "next js",
    "vuejs": "vue js",
    "angular": "angular js",
    "postgresql": "postgres",
    "postgres": "postgres",
    "github": "git",
    "gitlab": "git",
    "bitbucket": "git",
    "devops": "dev ops",
    "ci/cd": "ci cd pipeline",
    "cicd": "ci cd pipeline",
    "rest api": "restful api",
    "restful": "rest api",
    "containerization": "docker",
    "container": "docker",
    "terraform": "infrastructure as code",
    "cloudformation": "infrastructure as code",
    "microsoft excel": "excel",
    "ms excel": "excel",
    "microsoft word": "word",
    "ms word": "word",
    "powerpoint": "power point",
    "autocad": "cad",
    "computer-aided design": "cad",
    "computer aided design": "cad",
    "customer relationship management": "crm",
    "enterprise resource planning": "erp",
}

# Known technical terms that must survive punctuation cleaning
TECH_TERMS_WITH_PUNCTUATION = {
    "c++": "cplusplus",
    "c#": "csharp",
    "f#": "fsharp",
    ".net": "dotnet dot_net",
    "dot net": "dotnet dot_net",
    "node.js": "nodejs",
    "react.js": "reactjs",
    "vue.js": "vuejs",
    "next.js": "nextjs",
    "express.js": "expressjs",
    "three.js": "threejs",
    "d3.js": "d3js",
    "chart.js": "chartjs",
    "jquery": "jquery",
}


# ---------------------------------------------------------------------------
# Regex patterns for detecting resume elements
# ---------------------------------------------------------------------------
MEASURABLE_PATTERNS = [
    r"\d+%",                   # percentages: 25%, 100%
    r"\$[\d,]+",               # dollar amounts: $250,000
    r"\d+\+?\s*(?:clients|patients|customers|orders|items|tasks|cases|users|employees|projects|locations|sites|stakeholders|tickets|transactions|records|requests)",
    r"\d+\+?\s*(?:hours|days|weeks|months|years)",
    r"\d+\+?\s*(?:kg|lbs|tonnes|ton)",
    r"(?:managed|supervised|led|oversaw)\s+(?:a\s+)?team\s+of\s+\d+",
    r"\d+\+?\s*(?:team\s+members|staff|employees)",
    r"(?:increased|reduced|improved|decreased|achieved)\s.*\d+",
    r"(?:saved|reduced\s+by)\s.*\$[\d,]+",
    r"(?:zero|0)\s*-?\s*incident",
    r"100%\s*(?:compliance|adherence|accuracy|satisfaction)",
    r"\d+\+?\s*x\b",           # e.g. "2x", "3x faster"
    r"\d+\+?\s*million\b",     # e.g. "5 million users"
    r"\d+\+?\s*[kK]\b",        # e.g. "10k records"
    r"(?:processed|supported|served|handled|generated|delivered)\s+\d+",
]

SECTION_PATTERNS = {
    "contact":    r"(?i)(email|phone|linkedin|@\w+\.\w+|\+\d{10,})",
    "summary":    r"(?i)(professional\s+profile|career\s+summary|objective|profile\s+summary|about\s+me|professional\s+background)",
    "experience": r"(?i)(professional\s+experience|work\s+experience|employment\s+history|career\s+history|work\s+history|professional\s+background|relevant\s+experience)",
    "education":  r"(?i)(education|qualifications|academic\s+background|studies|academic\s+qualifications|education\s+and\s+qualifications)",
    "skills":     r"(?i)(core\s+skills|key\s+skills|technical\s+skills|competencies|skills\s+&|technical\s+stack|tech\s+stack|technologies|proficiencies|expertise)",
    "certs":      r"(?i)(certifications?|licenses?|accreditations?|training|courses?|first\s+aid|certifications\s+and\s+training|professional\s+certifications)",
    "projects":   r"(?i)(projects|personal\s+projects|professional\s+projects|side\s+projects|portfolio)",
    "languages":  r"(?i)(languages|language\s+proficiency)",
}

BULLET_PATTERN = r"(?:^|\n)\s*[•●\-\*▪▸➤→◆◇‣⁃⁌⁍⦿❖➢➣➤]\s+"

DATE_RANGE_PATTERN = r"(?i)(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s*\d{4}\s*[–\-—]\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Present|Current)\w*\s*\d{0,4}"

YEAR_PATTERN = r"(?i)\b((?:19|20)\d{2})\b"

# Skill-like word patterns: tech, tools, certifications, roles
SKILL_LIKE = re.compile(r"(?i)(engineer|technician|support|admin|desktop|network|hardware|software|"
                        r"system|configur|install|troubleshoot|audio|video|wireless|"
                        r"certif|train|course|degree|diploma|bachelor|master|"
                        r"python|java|sql|aws|azure|docker|kubernet|linux|"
                        r"html|css|javascript|react|angular|node|git|"
                        r"excel|word|powerpoint|office|crm|sap|"
                        r"lan|wan|router|switch|firewall|vpn|"
                        r"break.fix|patch|upgrade|os|windows|mac|linux|"
                        r"field|service|desk|help|it|tech|"
                        r"ccna|comptia|a.plus|network.plus|security.plus|microsoft|cisco)")

STOP_WORDS = {
    # Articles / pronouns / auxiliaries
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","was","are","were","be","been","being","have","has","had",
    "do","does","did","will","would","could","should","may","might","shall","can",
    "need","must","that","which","who","whom","this","these","those","it","its",
    "not","no","nor","as","if","then","than","too","very","so","up","out","about",
    "into","through","during","before","after","above","below","between","under",
    "again","further","once","here","there","when","where","why","how","all",
    "each","few","more","most","other","some","such","only","own","same","also",
    "just","because","while","although","until","unless","since","whether","yet",
    "any","every","many","much",
    # Common filler / adjectives / adverbs
    "able","accommodate","across","actually","already","always","another","around",
    "away","back","become","becomes","becoming","been","before","behind","being",
    "below","beside","besides","beyond","certain","certainly","clearly","currently",
    "daily","done","due","either","else","enough","especially","even","ever",
    "everybody","everyone","everything","everywhere","except","finally","first",
    "following","from","front","further","get","gets","getting","give","given",
    "giving","go","goes","going","gone","got","gotten","hard","hence","her","here",
    "hers","herself","him","himself","his","how","however","immediately","important",
    "indeed","instead","itself","last","later","least","less","let","like","likely",
    "little","long","look","looking","make","makes","making","man","may","maybe",
    "mean","meanwhile","merely","might","mine","moreover","mostly","much","myself",
    "near","nearly","necessary","neither","never","nevertheless","next","nobody",
    "none","nonetheless","nothing","nowwhere","off","often","okay","once","only",
    "onto","open","otherwise","ought","ours","ourselves","over","own",
    "particular","particularly","past","perhaps","please","possible","probably",
    "put","quite","rather","real","really","recently","regardless","relatively",
    "right","round","said","same","saw","say","saying","says","second","see",
    "seem","seemed","seeming","seems","seen","self","selves","sensible","serious",
    "shall","show","showed","shown","shows","side","simply","since","sincere","slight",
    "slightly","small","somebody","someday","somehow","someone","something","sometime",
    "sometimes","somewhere","soon","sorry","specific","still","straight","take",
    "taken","tell","tends","than","thank","thanks","that","theirs","them","themselves",
    "then","there","thereafter","thereby","therefore","therein","thereof","these",
    "they","thick","thin","think","thinking","third","this","those","though",
    "thought","three","through","throughout","throw","thus","today","together",
    "tomorrow","tonight","toward","towards","truly","try","trying","twice","two",
    "under","unless","unlike","until","upon","use","used","using","various","very",
    "virtue","want","wants","was","well","were","whatever","when","whenever",
    "where","whereas","wherever","whether","which","while","who","whoever","whom",
    "whose","why","wide","will","wish","within","without","would","yes","yet","you",
    "your","yours","yourself","yourselves",
    # Job posting filler / noise (Indeed, Seek, LinkedIn boilerplate)
    "description","hour","hours","location","type","per","person","job",
    "duties","understanding","familiar","basic","required","requirements","preferred",
    "qualifications","responsibilities","ability","strong",
    "excellent","good","knowledge","plus","including","include",
    "company","casual","part","time","full","salary","pay","rate","rates","aud",
    "nzd","usd","annual","weekly","fortnightly","schedule","shift","shifts",
    "day","days","week","weeks","month","months","year","years","remote","hybrid",
    "onsite","on-site","office","workplace","australia","sydney","melbourne","brisbane",
    "darwin","perth","adelaide","canberra","new","zealand","nsw","vic","qld","wa",
    "sa","act","nt","post","posted","days","ago","apply","application","resume",
    "cv","cover","letter","contact","phone","email","address","linkedin","github",
    "portfolio","references","available","notice","period","weeks","immediate",
    "start","flexible","rotating","weekends","evenings","monday","tuesday","wednesday",
    "thursday","friday","saturday","sunday","visa","sponsorship","citizen","permanent",
    "resident","english","language","communication","written","verbal","interpersonal",
    "customer","oriented","detail","self","motivated","passionate",
    "enthusiastic","proactive","reliable","professional","positive","attitude",
    "fast","learner","adaptable","multitask","pressure","deadlines","stakeholders",
    "cross","functional","diverse","inclusive","collaborate",
}


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def count_bullets(text: str) -> int:
    """Count bullet points in the resume."""
    return len(re.findall(BULLET_PATTERN, text))


def count_measurable_achievements(text: str) -> int:
    """
    Count bullets that contain measurable/quantifiable achievements.
    Returns number of bullets with at least one measurable pattern.
    """
    lines = re.split(r"\n", text)
    count = 0
    for line in lines:
        # Check if line looks like a bullet point
        if re.match(r"\s*[•●\-\*▪▸➤→◆◇‣⁃⁌⁍⦿❖➢➣➤]", line.strip()):
            # Check if it contains any measurable pattern
            for pattern in MEASURABLE_PATTERNS:
                if re.search(pattern, line):
                    count += 1
                    break  # Count each bullet only once
    return count


def detect_sections(text: str) -> Dict[str, bool]:
    """Detect which resume sections are present."""
    sections = {}
    for name, pattern in SECTION_PATTERNS.items():
        sections[name] = bool(re.search(pattern, text))
    return sections


def detect_date_ranges(text: str) -> List[str]:
    """Extract date ranges from resume."""
    return re.findall(DATE_RANGE_PATTERN, text)


def extract_section(text: str, section_name: str) -> str:
    """
    Extract the content of a specific section from resume text.
    Sections are detected by common heading patterns.
    Returns the text between this section's heading and the next heading,
    or empty string if not found.
    """
    # Build a regex that matches the section heading
    headings = SECTION_PATTERNS.get(section_name, "")
    if not headings:
        return ""

    # Find the section heading in the text
    match = re.search(headings, text)
    if not match:
        return ""

    start = match.end()

    # Find the next section heading (any known section) to end this section
    next_section = re.search(
        r"(?i)(?:^|\n)\s*(professional\s+profile|career\s+summary|"
        r"professional\s+experience|work\s+experience|employment\s+history|"
        r"education|qualifications|academic\s+background|"
        r"core\s+skills|key\s+skills|technical\s+skills|competencies|"
        r"certifications|courses?|licenses?|training|"
        r"projects|personal\s+projects|portfolio)\s*\n",
        text[start:]
    )
    if next_section:
        end = start + next_section.start()
        return text[start:end].strip()
    return text[start:].strip()


def detect_years(text: str) -> List[str]:
    """
    Extract years mentioned in WORK EXPERIENCE section only.
    Ignores education years (e.g. "Expected: Feb 2028") and project dates.
    """
    # Extract only the experience section
    exp_section = extract_section(text, "experience")
    if not exp_section:
        return set()

    # Get date ranges within experience section
    ranges = detect_date_ranges(exp_section)

    # Collect years from these ranges
    range_years = set()
    for r in ranges:
        for y in re.findall(YEAR_PATTERN, r):
            range_years.add(y)

    return sorted(range_years)


def normalize_tech_text(text: str) -> str:
    """
    Normalize text for ATS keyword matching:
    1. Replace known tech terms with punctuation-safe versions
    2. Apply synonym normalization (skip phrases containing already-normalized tech terms)
    """
    text_lower = text.lower().strip()

    # Phase 1: Replace known tech terms BEFORE punctuation stripping
    for term, replacement in TECH_TERMS_WITH_PUNCTUATION.items():
        text_lower = text_lower.replace(term, replacement)

    # Phase 2: Apply synonym normalization, but skip phrases that are
    # already-normalized tech terms to avoid double-replacement
    result = text_lower
    for phrase, normalized in SYNONYM_MAP.items():
        skip = False
        for tech_term in TECH_TERMS_WITH_PUNCTUATION:
            if tech_term in phrase or phrase in TECH_TERMS_WITH_PUNCTUATION:
                skip = True
                break
        if not skip:
            result = result.replace(phrase, normalized)

    return result


def extract_keywords(text: str, top_n: int = 30, min_freq: int = 1) -> List[str]:
    """
    Extract meaningful keywords from text using frequency analysis.
    Preserves important tech terms (C++, C#, .NET) and normalizes synonyms.

    Args:
        text: Text to extract keywords from
        top_n: Maximum number of keywords to return
        min_freq: Minimum occurrence frequency (1 = include everything)

    Returns:
        List of keyword strings, sorted by frequency descending
    """
    # Normalize tech terms and synonyms FIRST
    text_normalized = normalize_tech_text(text)

    # Remove remaining punctuation (except what we already preserved)
    text_clean = re.sub(r"[^a-zA-Z\s]", " ", text_normalized)
    words = text_clean.split()

    # Filter: remove stop words and short words
    filtered = [
        w for w in words
        if w not in STOP_WORDS
        and len(w) > 2
        and w.isalpha()
    ]

    # Count frequencies
    freq = Counter(filtered)

    # Filter by min_freq
    result = [w for w, count in freq.most_common(top_n * 2) if count >= min_freq]

    return result[:top_n]


def compute_word_count(text: str) -> int:
    """Count total words."""
    return len(text.split())


# ---------------------------------------------------------------------------
# Category scorers (each returns 0-10)
# ---------------------------------------------------------------------------

def score_formatting(text: str) -> Tuple[float, List[str]]:
    """
    Score: 15% weight
    Criteria:
      - Has clear sections (0-4 pts)
      - Has bullet points (0-3 pts)
      - Has contact information (0-3 pts)
    """
    score = 0
    notes = []

    sections = detect_sections(text)
    present = [k for k, v in sections.items() if v]

    # Section presence (0-4)
    section_score = min(4, len(present))
    score += section_score
    if len(present) >= 4:
        notes.append(f"Strong section structure ({len(present)} sections detected)")
    elif len(present) >= 2:
        notes.append(f"Basic sections present ({len(present)}/6) — consider adding Skills and Certifications")
    else:
        notes.append("Limited section structure — add Summary, Skills, and Experience sections")

    # Bullet points (0-3)
    bullets = count_bullets(text)
    if bullets >= 8:
        score += 3
        notes.append(f"Well-structured with {bullets} bullet points")
    elif bullets >= 4:
        score += 2
        notes.append(f"Has {bullets} bullet points — aim for 3-5 per role")
    elif bullets >= 1:
        score += 1
        notes.append(f"Only {bullets} bullet points — add more specific achievements")
    else:
        notes.append("No bullet points detected — use bullet format for achievements")

    # Contact info (0-3)
    if sections.get("contact"):
        score += 3
        notes.append("Contact information present")
    else:
        score += 0
        notes.append("Missing contact information")

    return min(10, score), notes


def score_ats_readiness(text: str) -> Tuple[float, List[str]]:
    """
    Score: 20% weight
    Criteria:
      - Keyword density (0-4 pts) — uses OCCURRENCES, not unique keyword count
      - Has required sections for ATS (0-4 pts)
      - Has job titles visible (0-2 pts)
    """
    score = 0
    notes = []

    # Keyword density (0-4)
    word_count = compute_word_count(text)
    keywords = extract_keywords(text, top_n=20)

    # Re-extract keywords from normalized text to count total occurrences
    text_normalized = normalize_tech_text(text)
    text_clean = re.sub(r"[^a-zA-Z\s]", " ", text_normalized)
    words = text_clean.split()

    filtered_words = [
        w for w in words
        if w not in STOP_WORDS
        and len(w) > 2
        and w.isalpha()
    ]

    # Count keyword occurrences (not unique)
    keyword_occurrences = sum(1 for w in filtered_words if w in set(keywords))
    keyword_density = keyword_occurrences / max(word_count, 1) * 100

    if keyword_density >= 12:
        score += 4
        notes.append(f"High keyword density ({keyword_density:.1f}%) — good ATS compatibility")
    elif keyword_density >= 8:
        score += 3
        notes.append(f"Moderate keyword density ({keyword_density:.1f}%)")
    elif keyword_density >= 4:
        score += 2
        notes.append(f"Low keyword density ({keyword_density:.1f}%) — add more industry-specific terms")
    else:
        score += 1
        notes.append(f"Very low keyword density ({keyword_density:.1f}%) — ATS may not rank well")

    # ATS-required sections (0-4)
    sections = detect_sections(text)
    required = ["experience", "education", "skills"]
    present_required = [s for s in required if sections.get(s)]

    if len(present_required) == 3:
        score += 4
        notes.append("All ATS-critical sections present (Experience, Education, Skills)")
    elif len(present_required) == 2:
        score += 3
        notes.append(f"Missing {set(required) - set(present_required)} — ATS may filter out")
    elif len(present_required) == 1:
        score += 1
        notes.append("Missing multiple ATS-critical sections")
    else:
        notes.append("No ATS-critical sections detected")

    # Job titles (0-2)
    role_keywords = re.findall(
        r"(?i)(?:engineer|developer|manager|coordinator|assistant|officer|analyst|specialist|consultant|lead|director|supervisor|support worker|nurse|carer|electrician|plumber|tradesperson|scientist|architect|product owner|scrum master|administrator|technician|operator)",
        text
    )
    unique_roles = set(role_keywords)
    if len(unique_roles) >= 3:
        score += 2
        notes.append(f"Multiple job titles detected: {', '.join(list(unique_roles)[:3])}")
    elif len(unique_roles) >= 1:
        score += 1
        notes.append(f"Job title(s) detected: {', '.join(unique_roles)}")
    else:
        notes.append("No clear job titles detected")

    return min(10, score), notes


def score_experience_quality(text: str) -> Tuple[float, List[str]]:
    """
    Score: 25% weight
    Criteria:
      - Years of experience (0-3 pts)
      - Number of roles (0-3 pts)
      - Career progression (0-2 pts)
      - Date range consistency (0-2 pts)
    """
    score = 0
    notes = []

    # Years (0-3)
    years = sorted(set(detect_years(text)))
    if len(years) >= 2:
        try:
            earliest = int(min(years))
            latest = int(max(years))
            span = latest - earliest
            if span >= 5:
                score += 3
                notes.append(f"{span}+ years of experience ({earliest}-{latest})")
            elif span >= 3:
                score += 2
                notes.append(f"{span} years of experience ({earliest}-{latest})")
            elif span >= 1:
                score += 1
                notes.append(f"{span} year(s) of experience ({earliest}-{latest})")
            else:
                score += 1
                notes.append("Limited date range — add more experience history")
        except ValueError:
            score += 1
    else:
        score += 1
        notes.append("Could not determine experience span")

    # Number of roles (0-3)
    date_ranges = detect_date_ranges(text)
    if len(date_ranges) >= 4:
        score += 3
        notes.append(f"{len(date_ranges)} distinct roles — strong career history")
    elif len(date_ranges) >= 2:
        score += 2
        notes.append(f"{len(date_ranges)} roles listed")
    elif len(date_ranges) >= 1:
        score += 1
        notes.append(f"Only {len(date_ranges)} role(s) — add more work history")
    else:
        notes.append("No dated roles detected")

    # Career progression (0-2)
    # Check for senior/lead/management keywords in later roles
    progression_words = re.findall(
        r"(?i)\b(senior|lead|principal|head|manager|director|supervisor|coordinator|chief)\b",
        text
    )
    if progression_words:
        score += 2
        notes.append("Career progression indicators detected (senior/lead/management)")
    else:
        # Check for multiple companies
        companies = re.findall(r"(?:at|for|with)\s+([A-Z][A-Za-z\s&]+)", text)
        if len(set(companies)) >= 3:
            score += 1
            notes.append("Multiple employers — shows progression")
        else:
            notes.append("No clear career progression — highlight growth across roles")

    # Date consistency (0-2)
    if len(date_ranges) >= 2:
        score += 2
        notes.append("Multiple dated positions — good chronological structure")
    else:
        score += 1
        notes.append("Add date ranges to all positions for better ATS parsing")

    return min(10, score), notes


def score_achievement_density(text: str) -> Tuple[float, List[str]]:
    """
    Score: 20% weight
    Criteria:
      - Achievement density (measurable / total bullets) (0-6 pts)
      - Action verbs used (0-2 pts)
      - Bullet length quality (0-2 pts)
    """
    score = 0
    notes = []

    total_bullets = count_bullets(text)
    measurable = count_measurable_achievements(text)

    # Achievement density (0-6)
    if total_bullets > 0:
        density = measurable / total_bullets
        density_pct = density * 100

        if density >= 0.5:
            score += 6
            notes.append(f"Strong achievement density: {measurable}/{total_bullets} bullets are quantified ({density_pct:.0f}%)")
        elif density >= 0.3:
            score += 4
            notes.append(f"Moderate density: {measurable}/{total_bullets} quantified ({density_pct:.0f}%) — add more metrics")
        elif density >= 0.15:
            score += 2
            notes.append(f"Low density: {measurable}/{total_bullets} quantified ({density_pct:.0f}%) — most bullets lack impact metrics")
        else:
            score += 1
            notes.append(f"Very low density: {measurable}/{total_bullets} quantified ({density_pct:.0f}%) — add numbers, percentages, and outcomes")
    else:
        notes.append("No bullet points detected")

    # Action verbs (0-2)
    action_verbs = re.findall(
        r"(?i)\b(managed|led|delivered|achieved|implemented|developed|created|improved|increased|reduced|maintained|supervised|trained|facilitated|coordinated|executed|designed|established|initiated|streamlined|optimized)\b",
        text
    )
    unique_verbs = set(v.lower() for v in action_verbs)
    if len(unique_verbs) >= 6:
        score += 2
        notes.append(f"Strong action verb usage ({len(unique_verbs)} unique verbs)")
    elif len(unique_verbs) >= 3:
        score += 1
        notes.append(f"Moderate action verb variety ({len(unique_verbs)} verbs)")
    else:
        notes.append("Limited action verb variety — use more dynamic verbs")

    # Bullet length quality (0-2)
    bullet_lines = [l.strip() for l in text.split("\n") if re.match(r"\s*[•●\-\*▪▸➤→◆◇‣⁃⁌⁍⦿❖➢➣➤]", l.strip())]
    if bullet_lines:
        avg_len = sum(len(l.split()) for l in bullet_lines) / len(bullet_lines)
        if avg_len >= 12:
            score += 2
            notes.append("Bullet points are detailed and informative")
        elif avg_len >= 8:
            score += 1
            notes.append("Bullet points are adequate — add more detail")
        else:
            notes.append("Bullet points are too brief — expand with specifics")

    return min(10, score), notes


def score_skills_relevance(text: str) -> Tuple[float, List[str]]:
    """
    Score: 20% weight
    Criteria:
      - Skills section present (0-3 pts)
      - Education section present (0-2 pts)
      - Soft skills + hard skills balance (0-5 pts)
    No domain_keywords needed — purely structural measurement.
    """
    score = 0
    notes = []

    # Skills section (0-3)
    sections = detect_sections(text)
    if sections.get("skills"):
        score += 3
        notes.append("Dedicated skills section present")
    elif sections.get("certs"):
        score += 1
        notes.append("No dedicated Skills section — certifications found but add a Skills section")
    else:
        notes.append("No skills section detected — add a dedicated Skills section")

    # Education section (0-2)
    if sections.get("education"):
        score += 2
        notes.append("Education section present")
    else:
        notes.append("No education section detected")

    # Soft + hard skills balance (0-5)
    soft_skills = re.findall(
        r"(?i)\b(communication|teamwork|leadership|problem.solving|adaptability|time.management|organization|interpersonal|empathy|patience|attention.to.detail|work ethic|reliability|flexibility|collaboration)\b",
        text
    )
    hard_skills = re.findall(
        r"(?i)\b(python|java|sql|javascript|aws|azure|docker|kubernetes|excel|word|crm|sap|quickbooks|xero|wms|pos|firewall|networking|html|css|react|angular|node|project management|agile|scrum|sdlc)\b",
        text
    )

    if soft_skills and hard_skills:
        score += 5
        notes.append(f"Good balance: {len(set(s.lower() for s in soft_skills))} soft skills, {len(set(h.lower() for h in hard_skills))} hard skills")
    elif soft_skills:
        score += 3
        notes.append("Soft skills present but add technical/hard skills")
    elif hard_skills:
        score += 3
        notes.append("Hard skills present but add soft/communication skills")
    else:
        notes.append("Add both soft and technical skills to strengthen the resume")

    return min(10, score), notes


# ---------------------------------------------------------------------------
# ATS Gap Analysis — deterministic keyword matching between resume and job description
# ---------------------------------------------------------------------------

def extract_concepts(text: str) -> Dict[str, bool]:
    """
    Convert free text into canonical skill concepts using SKILL_CONCEPTS.
    Returns dict of {concept_name: True} for all detected concepts.
    This is the 'concept layer' between raw words and final matching.
    """
    text_lower = text.lower()
    found = {}
    for concept, variants in SKILL_CONCEPTS.items():
        for variant in variants:
            if variant in text_lower:
                found[concept] = True
                break
    return found


def classify_role(job_description: str) -> str:
    """Classify job type for adaptive scoring weights."""
    jd_lower = job_description.lower()
    it_signals = ["it support", "help desk", "helpdesk", "service desk", "desktop support", "technical support", "system administrator", "sysadmin", "windows server", "active directory", "lan", "wan"]
    sw_signals = ["software engineer", "software developer", "full stack", "backend", "frontend", "devops", "cloud engineer", "sre", "data engineer"]
    it_score = sum(1 for s in it_signals if s in jd_lower)
    sw_score = sum(1 for s in sw_signals if s in jd_lower)
    if it_score >= 2 and sw_score < 2:
        return "IT_SUPPORT"
    elif sw_score >= 2 and it_score < 2:
        return "SOFTWARE_ENGINEER"
    return "GENERAL"

def get_role_weights(role_type: str) -> Dict[str, float]:
    """Return scoring weights based on role type."""
    presets = {
        "IT_SUPPORT": {"concept_coverage": 0.60, "semantic_alignment": 0.15, "evidence_strength": 0.25},
        "SOFTWARE_ENGINEER": {"concept_coverage": 0.40, "semantic_alignment": 0.35, "evidence_strength": 0.25},
        "GENERAL": {"concept_coverage": 0.45, "semantic_alignment": 0.30, "evidence_strength": 0.25},
    }
    return presets.get(role_type, presets["GENERAL"])

def compute_job_fit_score(
    resume_text: str,
    job_description: str,
    gap_result: Dict,
    semantic_matches: List[Dict],
) -> Dict:
    """
    Canonical Job Fit Score (single authoritative metric).

    Formula:
        Job Fit = w1 × Concept Coverage + w2 × Semantic Alignment + w3 × Evidence Strength

    Weights are role-adaptive (IT_SUPPORT, SOFTWARE_ENGINEER, GENERAL).

    Where:
      - Concept Coverage  = % of JD concepts detected in resume (ontology)
      - Semantic Alignment= cosine similarity of full-document embeddings
      - Evidence Strength = exact keyword match coverage %

    Returns:
        {
            "job_fit_score": 0-100,
            "breakdown": {
                "concept_coverage": float,
                "semantic_alignment": float,
                "evidence_strength": float,
            },
        }
    """
    # === Determine role type and weights ===
    role_type = classify_role(job_description)
    weights = get_role_weights(role_type)

    # === 1. Concept Coverage (adaptive) ===
    concept_cov = float(gap_result.get("concept_coverage", 0))
    concept_score = min(100, concept_cov)

    # === 2. Semantic Alignment (per-skill grounding, NOT global doc similarity) ===
    # Use phrase-level semantic matches to average best similarity per JD concept.
    # This avoids "good writing = good fit" failure mode.
    sem_hard = [m for m in semantic_matches if m.get("type") == "HARD_MATCH"]
    sem_soft = [m for m in semantic_matches if m.get("type") == "SOFT_MATCH"]
    total_sem = len(sem_hard) + len(sem_soft)
    total_jd_concepts = max(gap_result.get("total_job_keywords", 1), 1)

    if total_sem > 0:
        base = (total_sem / total_jd_concepts) * 100 if total_jd_concepts > 0 else 0
        hard_w = len(sem_hard) * 1.5
        soft_w = len(sem_soft) * 0.5
        quality = (hard_w + soft_w) / max(total_sem, 1)
        semantic_score = min(100, base * quality)
    else:
        # No semantic matches found — neutral score
        semantic_score = 50.0

    # === 3. Evidence Strength (bonus-only, not penalty-driven) ===
    # Only boosts if keywords are present; does not heavily penalize absence
    # because concept layer already captures meaning.
    evidence_score = float(gap_result.get("keyword_coverage", 0))
    evidence_score = min(100, evidence_score * 2.5)  # scale 40% cov → 100 pts bonus

    # === Fuse (adaptive weights) ===
    fit = (
        concept_score   * weights["concept_coverage"] +
        semantic_score  * weights["semantic_alignment"] +
        evidence_score  * weights["evidence_strength"]
    )
    fit = int(min(100, max(0, fit)))

    return {
        "job_fit_score": fit,
        "breakdown": {
            "concept_coverage":    round(concept_score, 1),
            "semantic_alignment":  round(semantic_score, 1),
            "evidence_strength":   round(evidence_score, 1),
        },
        "role_type": role_type,
        "weights_used": weights,
    }


def analyze_ats_gap(resume_text: str, job_description: str) -> Dict:
    """
    Compare resume keywords against job description keywords.
    Returns matched/missing/coverage data — purely deterministic, no LLM needed.

    FIXES over previous version:
    - Uses synonym normalization (AWS ↔ Amazon Web Services)
    - Preserves tech terms with punctuation (C++, C#, .NET)
    - Counts keyword OCCURRENCES, not unique keywords
    - Uses min_freq threshold instead of hard top_n cap for JD
    - Bigrams now include stop words to avoid marketing phrases
    - Only unigrams used for primary matching (bigrams as supplement)
    - Expanded JD marketing/location words added to STOP_WORDS

    Returns:
        {
            "matched_keywords": [str],
            "missing_keywords": [str],
            "keyword_coverage": float (0-100),
            "total_job_keywords": int,
            "matched_count": int,
            "missing_count": int,
        }
    """
    # JD marketing/location/generic filler words that are NOT skills
    JD_STOPWORDS = {
        "asia","pacific","emea","unanderra","adelaide","australia","locations",
        "company","providing","job","role","skills","experience",
        "desired","requirements","support","help","ticket","call",
        "dispatch","freelance","casual","basis","mode","sla","sbd","nbd",
        "greetings","interested","available","subject","line","references",
        "appreciated","throughout","nationwide","hiring","urgent","openings",
        "clipboard","shifts","manual","safely","pls","share","cv",
        "visalakshi","eilglobal","com",
        "based","setup","patches","language",
    }

    resume_keywords = set(extract_keywords(resume_text, top_n=60, min_freq=1))

    # Extract JD keywords and FILTER OUT non-skill marketing words
    raw_job_kw = set(extract_keywords(job_description, top_n=50, min_freq=1))
    job_keywords = {kw for kw in raw_job_kw if kw not in JD_STOPWORDS}

    # Bigrams as supplement only — use conservative filter to avoid marketing noise
    resume_bigrams = set()
    job_bigrams = set()

    for text, bigram_set in [(resume_text, resume_bigrams), (job_description, job_bigrams)]:
        text_norm = normalize_tech_text(text)
        words = re.sub(r"[^a-zA-Z\s]", " ", text_norm).split()

        # Build bigrams but only keep if at least one word looks like a skill term
        for i in range(len(words) - 1):
            w1, w2 = words[i], words[i+1]
            both_not_stop = w1 not in STOP_WORDS and w2 not in STOP_WORDS
            both_long = len(w1) > 2 and len(w2) > 2
            at_least_one_skill = bool(SKILL_LIKE.search(w1)) or bool(SKILL_LIKE.search(w2))
            if both_not_stop and both_long and at_least_one_skill:
                bigram_set.add(f"{w1} {w2}")

    # Combine unigrams + bigrams for coverage check
    resume_all = resume_keywords | resume_bigrams
    job_all = job_keywords | job_bigrams

    matched = sorted([kw for kw in job_all if kw in resume_all])
    missing = sorted([kw for kw in job_all if kw not in resume_all])

    total = len(job_all)
    matched_count = len(matched)
    coverage = round((matched_count / total) * 100, 1) if total > 0 else 0.0

    # Categorize missing into critical vs. nice-to-have
    # Use word-boundary regex to avoid substring matches (e.g. "sql" matching "postgresql")
    job_text_lower = job_description.lower()
    freq = {}
    for kw in job_all:
        count = len(re.findall(rf"\b{re.escape(kw)}\b", job_text_lower))
        freq[kw] = count

    critical_missing = sorted([kw for kw in missing if freq.get(kw, 0) >= 2])
    other_missing = sorted([kw for kw in missing if freq.get(kw, 0) < 2])

    # Semantic matches (phase 2 — populated in app.py after this function returns)
    semantic_matches = []

    # ── Concept-level matching (the "concept layer") ──
    resume_concepts = set(extract_concepts(resume_text).keys())
    job_concepts = set(extract_concepts(job_description).keys())
    concept_matched = resume_concepts & job_concepts
    concept_missing = job_concepts - resume_concepts
    concept_coverage = round((len(concept_matched) / max(len(job_concepts), 1)) * 100, 1)

    # Build a set of resume concepts that are semantically covered
    # This allows "Dockerized backend" to count as covering "server/network/infrastructure"
    semantically_covered_resume_concepts = set()
    for sem in semantic_matches:
        semantically_covered_resume_concepts.add(sem.get("resume", "").lower())

    # Re-classify missing keywords: if a "missing" keyword is semantically covered
    # by a resume phrase, move it to "implicitly_matched" instead of truly missing
    implicitly_matched = []
    still_missing = []
    for kw in missing:
        # Check if any semantic match's resume phrase contains this keyword concept
        is_semantically_covered = False
        for sem_concept in semantically_covered_resume_concepts:
            # Direct containment or word-level overlap
            kw_words = set(kw.lower().split())
            concept_words = set(sem_concept.split())
            if kw_words & concept_words:  # any word overlap
                is_semantically_covered = True
                break
        if is_semantically_covered:
            implicitly_matched.append(kw)
        else:
            still_missing.append(kw)

    # Recalculate coverage including semantic bridging
    effective_matched = matched_count + len(implicitly_matched)
    effective_coverage = round((effective_matched / total) * 100, 1) if total > 0 else 0.0

    return {
        "matched_keywords": matched[:30],       # cap at 30 for display
        "missing_keywords": still_missing[:30],
        "critical_missing": [kw for kw in critical_missing if kw in still_missing][:15],
        "other_missing": [kw for kw in other_missing if kw in still_missing][:15],
        "implicitly_matched": implicitly_matched[:15],  # semantically bridged
        "keyword_coverage": coverage,  # exact match only (transparency)
        "effective_coverage": effective_coverage,  # exact + semantic bridge
        "concept_coverage": concept_coverage,  # NEW: concept-level match
        "concept_matched": sorted(concept_matched)[:20],
        "concept_missing": sorted(concept_missing)[:20],
        "total_job_keywords": total,
        "matched_count": matched_count,
        "missing_count": len(still_missing),
        "semantic_matches": semantic_matches,
    }


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

def score_resume(text: str) -> Dict:
    """
    Score a resume using the deterministic rubric.
    No domain_keywords needed — all categories are purely structural measurements.

    Returns:
        {
            "rubric_score": 0-100,
            "breakdown": {
                "formatting": {"score": 0-10, "weight": 0.15, "notes": [...]},
                "ats_readiness": {"score": 0-10, "weight": 0.20, "notes": [...]},
                "experience_quality": {"score": 0-10, "weight": 0.25, "notes": [...]},
                "achievement_density": {"score": 0-10, "weight": 0.20, "notes": [...]},
                "skills_relevance": {"score": 0-10, "weight": 0.20, "notes": [...]},
            },
            "all_notes": [str],
            "stats": {
                "word_count": int,
                "bullet_count": int,
                "measurable_bullets": int,
                "sections_detected": [str],
                "years_span": int,
            }
        }
    """
    # Run all scorers
    fmt_score, fmt_notes = score_formatting(text)
    ats_score, ats_notes = score_ats_readiness(text)
    exp_score, exp_notes = score_experience_quality(text)
    ach_score, ach_notes = score_achievement_density(text)
    skill_score, skill_notes = score_skills_relevance(text)

    # Calculate weighted score
    breakdown = {
        "formatting":       {"score": fmt_score,  "weight": 0.15},
        "ats_readiness":    {"score": ats_score,  "weight": 0.20},
        "experience_quality": {"score": exp_score, "weight": 0.25},
        "achievement_density": {"score": ach_score, "weight": 0.20},
        "skills_relevance": {"score": skill_score, "weight": 0.20},
    }

    weighted_sum = sum(
        cat["score"] * cat["weight"] * 10
        for cat in breakdown.values()
    )
    rubric_score = int(min(100, max(0, weighted_sum)))

    # Collect all notes
    all_notes = fmt_notes + ats_notes + exp_notes + ach_notes + skill_notes

    # Stats
    years = detect_years(text)
    year_span = 0
    if len(years) >= 2:
        try:
            year_span = int(max(years)) - int(min(years))
        except ValueError:
            pass

    stats = {
        "word_count": compute_word_count(text),
        "bullet_count": count_bullets(text),
        "measurable_bullets": count_measurable_achievements(text),
        "sections_detected": [k for k, v in detect_sections(text).items() if v],
        "years_span": year_span,
    }

    return {
        "rubric_score": rubric_score,
        "breakdown": breakdown,
        "all_notes": all_notes,
        "stats": stats,
    }