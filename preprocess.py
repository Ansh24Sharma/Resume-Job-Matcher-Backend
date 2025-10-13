# preprocess.py
import spacy
import re
 
# Load spaCy model (en_core_web_sm is enough here)
nlp = spacy.load("en_core_web_sm")
 
def clean_text(text: str) -> str:
    """
    Clean and normalize raw resume/job text.
    """
    if not text:
        return ""
 
    # Lowercase
    text = text.lower()
 
    # Remove unwanted chars (punctuation, newlines, tabs)
    text = re.sub(r"[^a-z0-9\s\+\.#]", " ", text)
 
    # Remove multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
 
    return text
 
 
def normalize_tokens(text: str) -> list:
    """
    Tokenize + lemmatize + keep meaningful words only.
    """
    doc = nlp(text)
    tokens = []
    for token in doc:
        if token.is_stop or token.is_punct or len(token.text) < 2:
            continue
        tokens.append(token.lemma_.lower())
    return list(set(tokens))  # remove duplicates
 