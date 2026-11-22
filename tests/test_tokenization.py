import unittest
from scoring import normalize_tech_text, extract_keywords, analyze_ats_gap

class TokenizationTests(unittest.TestCase):
    def test_normalize_tech_text_replacements(self):
        s = "C++ and AWS Cloud and React.js"
        out = normalize_tech_text(s)
        # Ensure key tech terms are normalized/represented
        self.assertIn("cplusplus", out)
        self.assertIn("aws", out)
        self.assertIn("reactjs", out)

    def test_punctuation_heavy_terms(self):
        s = "C# .NET node.js" 
        out = normalize_tech_text(s)
        self.assertIn("csharp", out)
        # .NET maps to dotnet or dot_net depending on mapping
        self.assertTrue("dotnet" in out or "dot_net" in out)
        self.assertIn("nodejs", out)

    def test_extract_keywords_frequency_order(self):
        s = "Python AWS AWS Docker Docker Docker"
        toks = extract_keywords(s, top_n=3)
        # Expect most frequent first
        self.assertEqual(toks, ["docker", "aws", "python"]) 

    def test_analyze_ats_gap_filters_fragments(self):
        jd = "Must have: Docker, Kubernetes\nPreferred: React"
        # Intentionally include noisy fragments in resume
        resume = "Experience: worked with docker and ities and kubernetesrnetes"
        res = analyze_ats_gap(resume, jd)
        # Ensure 'ities' not present anywhere
        all_lists = []
        for k in ("matched_skills", "missing_critical", "missing_optional", "required_skills", "preferred_skills"):
            all_lists.extend(res.get(k, []))
        self.assertNotIn("ities", all_lists)
        # Docker should be matched
        self.assertIn("docker", [m.lower() for m in res.get("matched_skills", [])])

if __name__ == '__main__':
    unittest.main()
