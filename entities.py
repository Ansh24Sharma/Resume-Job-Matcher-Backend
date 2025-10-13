import csv
import re
import spacy
from spacy.matcher import PhraseMatcher
from typing import List
from preprocess import clean_text, normalize_tokens
 
# -------------------------------
# Load spaCy model (English NER)
# -------------------------------
nlp = spacy.load("en_core_web_sm")
 
# -------------------------------
# Load cleaned skills list from CSV
# -------------------------------
with open("data/skills.csv", "r", encoding="utf-8") as f:
    all_skills = [row[0].strip().lower() for row in csv.reader(f) if row and row[0].strip()]
 
SKILLS = [skill for skill in all_skills if len(skill) > 2 and not skill.isdigit()]
print(f"Filtered skills inline: {len(SKILLS)} skills loaded")
 
# Create a PhraseMatcher for faster matching
skill_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp.make_doc(skill) for skill in SKILLS]
skill_matcher.add("SKILL", patterns) 
 
# -------------------------------
# Skills Extraction (Hybrid: CSV + NER)
# -------------------------------
def extract_skills(text: str) -> list:
    text_clean = clean_text(text)
    text_normalized = " ".join(normalize_tokens(text_clean)).lower()
 
    found_skills = set()
 
    # ---- 1) Match from CSV (PhraseMatcher) ----
    doc = nlp(text_normalized)
    matches = skill_matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        found_skills.add(span.text.lower())
 
    # ---- 2) Regex-based normalization for common variants ----
    skill_variations = {
        r'\bcore\s+java\b': 'java',
        r'\bjava\s*script\b': 'javascript',
        r'\bnode\.?js\b': 'nodejs',
        r'\breact\.?js\b': 'react',
        r'\bspring\s+boot\b': 'spring boot',
        r'\bhibernate/jpa\b': ['hibernate', 'jpa'],
        r'\bmy\s*sql\b': 'mysql',
        r'\bpost\s*gre\s*sql\b': 'postgresql',
        r'\bmongo\s*db\b': 'mongodb',
        r'\bc\+\+\b': 'c++',
        r'\bc#\b': 'c#',
        r'\b\.net\b': '.net',
        r'\brest\s*(?:api|ful)?\b': 'rest',
        r'\bci/cd\b': 'ci/cd'
    }
    for pattern, mapped_skills in skill_variations.items():
        if re.search(pattern, text_normalized):
            if isinstance(mapped_skills, list):
                for mapped_skill in mapped_skills:
                    found_skills.add(mapped_skill)
            else:
                found_skills.add(mapped_skills)
 
    # ---- 3) Fallback with spaCy NER (ORG/PRODUCT/WORK_OF_ART often contain tools/skills) ----
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART"]:
            found_skills.add(ent.text.lower())
 
    # ---- 4) Final formatting ----
    formatted_skills = []
    for skill in found_skills:
        if skill.upper() in ["AWS", "API", "SQL", "HTML", "CSS", "XML", "JSON", "AI", "ML", "NLP", "JPA", "REST"]:
            formatted_skills.append(skill.upper())
        elif skill.lower() in ["javascript", "nodejs"]:
            formatted_skills.append(skill.title())
        elif skill.lower() == "c++":
            formatted_skills.append("C++")
        elif skill.lower() == "c#":
            formatted_skills.append("C#")
        elif skill.lower() == ".net":
            formatted_skills.append(".NET")
        elif skill.lower() in ["react", "angular", "vue", "django", "flask", "laravel", "spring"]:
            formatted_skills.append(skill.title())
        elif "spring boot" in skill.lower():
            formatted_skills.append("Spring Boot")
        else:
            formatted_skills.append(skill.title())
 
    return list(sorted(set(formatted_skills)))
 

# Enhanced degree patterns with more variations
DEGREE_CANONICAL = {
    r"\bbachelor\s+of\s+technology\b|\bb\.?\s*tech\b|\bbtech\b": "B.Tech",
    r"\bbachelor\s+of\s+engineering\b|\bb\.?\s*e\.?\b|\bbe\b": "B.E",
    r"\bbachelor\s+of\s+science\b|\bb\.?\s*sc\b|\bbsc\b": "B.Sc",
    r"\bbachelor\s+of\s+arts\b|\bb\.?\s*a\.?\b|\bba\b": "B.A",
    r"\bbachelor\s+of\s+computer\s+applications\b|\bbca\b": "BCA",
    r"\bmaster\s+of\s+technology\b|\bm\.?\s*tech\b|\bmtech\b": "M.Tech",
    r"\bmaster\s+of\s+engineering\b|\bm\.?\s*e\.?\b|\bme\b": "M.E",
    r"\bmaster\s+of\s+science\b|\bm\.?\s*sc\b|\bmsc\b": "M.Sc",
    r"\bmaster\s+of\s+arts\b|\bm\.?\s*a\.?\b|\bma\b": "M.A",
    r"\bmba\b|\bmaster\s+of\s+business\s+administration\b": "MBA",
    r"\bmaster\s+of\s+computer\s+applications\b|\bmca\b": "MCA",
    r"\bph\.?d\b|\bdoctor\s+of\s+philosophy\b": "Ph.D",
    r"\bdiploma\b": "Diploma",
    r"\bcertificate\b": "Certificate",
    # Add more specific Indian degree patterns
    r"\bb\.?\s*com\b|\bbcom\b": "B.Com",
    r"\bm\.?\s*com\b|\bmcom\b": "M.Com",
    r"\bb\.?\s*ed\b|\bbed\b": "B.Ed",
    r"\bm\.?\s*ed\b|\bmed\b": "M.Ed",
}
 
SPECIALIZATION_MAP = {
    r"computer\s+science|c\.?\s*s\.?|cse|cs(?:\s+engineering)?": "Computer Science",
    r"information\s+technology|i\.?\s*t\.?|it(?:\s+engineering)?": "Information Technology",
    r"electrical(?:\s+engineering)?|eee|electrical\s+&\s+electronics": "Electrical Engineering",
    r"mechanical(?:\s+engineering)?|mech": "Mechanical Engineering",
    r"civil(?:\s+engineering)?": "Civil Engineering",
    r"electronics(?:\s+engineering)?|ece|electronics\s+&\s+communication": "Electronics Engineering",
    r"artificial\s+intelligence|ai": "Artificial Intelligence",
    r"machine\s+learning|ml": "Machine Learning",
    r"data\s+science": "Data Science",
    r"software(?:\s+engineering)?": "Software Engineering",
    r"computer\s+applications": "Computer Applications",
    r"business\s+administration": "Business Administration",
    r"commerce": "Commerce",
    r"science": "Science",
    r"arts": "Arts",
    r"engineering": "Engineering",
}
 
# Enhanced experience patterns
EXPERIENCE_PATTERNS = [
    r"(\d+)\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
    r"experience\s*:?\s*(\d+)\s*\+?\s*(?:years?|yrs?)",
    r"(\d+)\s*\+?\s*(?:years?|yrs?)",
    r"(\d+)\+\s*(?:years?|yrs?)",
    r"over\s+(\d+)\s+(?:years?|yrs?)",
    r"more\s+than\s+(\d+)\s+(?:years?|yrs?)",
    r"(\d+)\s+to\s+\d+\s+(?:years?|yrs?)",
]

 
def normalize_text_for_matching(text: str) -> str:
    """Normalize text for better pattern matching"""
    return re.sub(r'[^\w\s]', ' ', text.lower()).strip()
 
 
def canonical_degree_from_text(text: str) -> List[str]:
    """Extract and canonicalize degrees from text"""
    txt = normalize_text_for_matching(text)
    out = []
    
    for patt, canon in DEGREE_CANONICAL.items():
        matches = re.finditer(patt, txt, re.IGNORECASE)
        for match in matches:
            # Look for specialization in the surrounding context
            context_start = max(0, match.start() - 100)
            context_end = min(len(txt), match.end() + 100)
            context = txt[context_start:context_end]
            
            spec = None
            for sp_patt, sp_canon in SPECIALIZATION_MAP.items():
                if re.search(sp_patt, context, re.IGNORECASE):
                    spec = sp_canon
                    break
            
            degree_name = f"{canon} ({spec})" if spec else canon
            if degree_name not in out:
                out.append(degree_name)
    
    return out
 

def extract_education(text: str) -> List[str]:
    """Enhanced education extraction with multiple approaches"""
    if not text:
        return []
 
    results = []
    
    # Method 1: Direct degree extraction from full text
    degrees = canonical_degree_from_text(text)
    results.extend(degrees)
    
    # Method 2: Look for education sections
    education_sections = re.findall(
        r'(?:education|qualification|academic|degree).*?(?=\n\n|\n[A-Z]|\n\d+\.|\Z)', 
        text, 
        re.IGNORECASE | re.DOTALL
    )
    
    for section in education_sections:
        section_degrees = canonical_degree_from_text(section)
        for deg in section_degrees:
            if deg not in results:
                results.append(deg)
    
    # Method 3: NER approach for institutions
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ("ORG", "FAC"):
            ent_text = ent.text.strip()
            # Check if it's likely an educational institution
            if re.search(r"(university|college|institute|school|iit|nit|bits)", ent_text, re.I):
                if ent_text not in results:
                    results.append(ent_text)
    
    # Method 4: Line-by-line analysis for missed degrees
    lines = text.split('\n')
    for line in lines:
        line_degrees = canonical_degree_from_text(line)
        for deg in line_degrees:
            if deg not in results:
                results.append(deg)
 
    return list(set(results))
 

def extract_experience_list(text: str) -> List[str]:
    """Enhanced experience extraction with NER context and number word extraction"""
    if not text:
        return []
 
    out = []
    text_lower = text.lower()
    
    # Process with spaCy for NER context
    doc = nlp(text)
    
    # Word-to-number mapping for converting written numbers
    word_to_num = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
    }
    
    # Enhanced experience patterns including word numbers
    enhanced_patterns = [
        r"(\d+)\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
        r"experience\s*:?\s*(\d+)\s*\+?\s*(?:years?|yrs?)",
        r"(\d+)\s*\+?\s*(?:years?|yrs?)",
        r"(\d+)\+\s*(?:years?|yrs?)",
        r"over\s+(\d+)\s+(?:years?|yrs?)",
        r"more\s+than\s+(\d+)\s+(?:years?|yrs?)",
        r"(\d+)\s+to\s+\d+\s+(?:years?|yrs?)",
        # Word number patterns
        r"(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\s+(?:years?|yrs?)\s+(?:of\s+)?experience",
        r"experience\s*:?\s*(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\s+(?:years?|yrs?)",
        r"(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\s+(?:years?|yrs?)",
        r"over\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\s+(?:years?|yrs?)",
    ]
    
    # Method 1: NER-based context-aware extraction
    experience_keywords = ['experience', 'work', 'working', 'worked', 'employment', 'career', 'professional']
    
    for sent in doc.sents:
        sent_text = sent.text.lower()
        
        # Check if sentence contains experience-related keywords
        has_experience_context = any(keyword in sent_text for keyword in experience_keywords)
        
        if has_experience_context:
            # Look for numeric entities in experience context
            for ent in sent.ents:
                if ent.label_ == "CARDINAL":  # Numbers
                    try:
                        num_value = int(ent.text)
                        if 0 < num_value < 50:
                            # Check surrounding context for year indicators
                            context_words = sent_text.split()
                            ent_words = ent.text.lower().split()
                            
                            for i, word in enumerate(context_words):
                                if any(ent_word in word for ent_word in ent_words):
                                    # Check next few words for year indicators
                                    next_words = context_words[i:i+3]
                                    if any(indicator in ' '.join(next_words) for indicator in ['year', 'years', 'yr', 'yrs']):
                                        val = f"{num_value} years"
                                        if val not in out:
                                            out.append(val)
                    except ValueError:
                        continue
            
            # Also check with regex patterns in experience context
            for pattern in enhanced_patterns:
                matches = re.findall(pattern, sent_text)
                for match in matches:
                    try:
                        if match.isdigit():
                            years = int(match)
                        else:
                            years = word_to_num.get(match.lower(), 0)
                        
                        if years > 0 and years < 50:
                            val = f"{years} years"
                            if val not in out:
                                out.append(val)
                    except (ValueError, AttributeError):
                        continue
    
    # Method 2: Traditional regex patterns with context checking
    for pattern in enhanced_patterns:
        for match in re.finditer(pattern, text_lower):
            # Get surrounding context (50 characters before and after)
            start = max(0, match.start() - 50)
            end = min(len(text_lower), match.end() + 50)
            context = text_lower[start:end]
            
            # Check if context contains experience-related keywords
            has_context = any(keyword in context for keyword in experience_keywords)
            
            if has_context:
                matched_text = match.group(1)
                try:
                    if matched_text.isdigit():
                        years = int(matched_text)
                    else:
                        years = word_to_num.get(matched_text.lower(), 0)
                    
                    if years > 0 and years < 50:
                        val = f"{years} years"
                        if val not in out:
                            out.append(val)
                except (ValueError, AttributeError):
                    continue
    
    # Method 4: Look in experience sections specifically
    experience_sections = re.findall(
        r'(?:experience|work|employment|career).*?(?=\n\n|\n[A-Z]|\n\d+\.|\Z)', 
        text_lower, 
        re.IGNORECASE | re.DOTALL
    )
    
    for section in experience_sections:
        for pattern in enhanced_patterns:
            matches = re.findall(pattern, section)
            for match in matches:
                try:
                    if match.isdigit():
                        years = int(match)
                    else:
                        years = word_to_num.get(match.lower(), 0)
                    
                    if years > 0 and years < 50:
                        val = f"{years} years"
                        if val not in out:
                            out.append(val)
                except (ValueError, AttributeError):
                    continue
    
    # Method 5: Date range analysis (e.g., "2020-2023" implies 3 years)
    date_ranges = re.findall(r'(\d{4})\s*[-–]\s*(\d{4})', text)
    for start_year, end_year in date_ranges:
        try:
            years_diff = int(end_year) - int(start_year)
            if 0 < years_diff < 20:  # Reasonable range
                # Check if this date range is in experience context
                date_pattern = f"{start_year}.*{end_year}"
                for match in re.finditer(date_pattern, text):
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].lower()
                    
                    if any(keyword in context for keyword in experience_keywords):
                        val = f"{years_diff} years"
                        if val not in out:
                            out.append(val)
                        break
        except ValueError:
            continue
    
    return out
 
# -------------------------------
# Main Entity Extractor
# -------------------------------
def extract_entities(text: str) -> dict:
    """Extract all entities from text with debugging info"""
    
    # Add some debugging
    print(f"[DEBUG] Text length: {len(text)} characters")
    print(f"[DEBUG] First 200 chars: {text[:200]}")
    
    entities = {
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience": extract_experience_list(text),
    }
    
    print(f"[DEBUG] Extracted entities: {entities}")
    return entities