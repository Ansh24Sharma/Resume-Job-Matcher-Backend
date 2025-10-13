import os
import re
import pdfplumber
from entities import extract_entities
from service.resumes_service import insert_resume
from service.jobs_service import insert_job
 
 
def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a single PDF file using pdfplumber,
    preserving line breaks and formatting for better entity extraction.
    """
    text_lines = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text with better formatting preservation
                page_text = page.extract_text(
                    x_tolerance=2,  # Slightly more tolerance for character spacing
                    y_tolerance=2,  # Slightly more tolerance for line spacing
                    layout=True,    # Try to preserve layout
                    x_density=7.25, # Default density for character extraction
                    y_density=13    # Default density for line extraction
                )
                
                if page_text:
                    # Clean up the text while preserving structure
                    lines = page_text.split('\n')
                    cleaned_lines = []
                    
                    for line in lines:
                        # Remove excessive whitespace but preserve some structure
                        cleaned_line = ' '.join(line.split())
                        if cleaned_line:  # Only add non-empty lines
                            cleaned_lines.append(cleaned_line)
                    
                    if cleaned_lines:
                        text_lines.extend(cleaned_lines)
                        text_lines.append('')  # Add separator between pages
                
                print(f"[INFO] Processed page {page_num + 1}, extracted {len(page_text) if page_text else 0} characters")
    
    except Exception as e:
        print(f"[ERROR] Failed to extract text from {file_path}: {str(e)}")
        return ""
    
    # Join all lines with newlines
    full_text = '\n'.join(text_lines).strip()
    
    # Remove excessive consecutive newlines (more than 2)
    full_text = re.sub(r'\n{3,}', '\n\n', full_text)
    
    print(f"[INFO] Total extracted text length: {len(full_text)} characters")
    print(f"[INFO] First 300 characters: {full_text[:300]}")
    
    return full_text


def extract_text_from_uploaded_file(file_obj) -> str:
    """
    Extract text from an uploaded PDF file object.
    This version works with FastAPI's UploadFile.
    """
    text_lines = []
    
    try:
        # Reset file pointer to beginning
        file_obj.seek(0)
        
        with pdfplumber.open(file_obj) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text with better formatting preservation
                page_text = page.extract_text(
                    x_tolerance=2,
                    y_tolerance=2, 
                    layout=True,
                    x_density=7.25,
                    y_density=13
                )
                
                if page_text:
                    # Clean up the text while preserving structure
                    lines = page_text.split('\n')
                    cleaned_lines = []
                    
                    for line in lines:
                        # Remove excessive whitespace but preserve some structure
                        cleaned_line = ' '.join(line.split())
                        if cleaned_line:  # Only add non-empty lines
                            cleaned_lines.append(cleaned_line)
                    
                    if cleaned_lines:
                        text_lines.extend(cleaned_lines)
                        text_lines.append('')  # Add separator between pages
                
                print(f"[INFO] Processed page {page_num + 1}, extracted {len(page_text) if page_text else 0} characters")
    
    except Exception as e:
        print(f"[ERROR] Failed to extract text from uploaded file: {str(e)}")
        return ""
    
    # Join all lines with newlines
    full_text = '\n'.join(text_lines).strip()
    
    # Remove excessive consecutive newlines (more than 2)
    import re
    full_text = re.sub(r'\n{3,}', '\n\n', full_text)
    
    print(f"[INFO] Total extracted text length: {len(full_text)} characters")
    print(f"[INFO] First 300 characters: {full_text[:300]}")
    
    return full_text
 
 
def load_pdfs_from_folder(folder_path: str, type_: str = "resume"):
    """
    Load multiple PDFs from a folder and insert into DB.
    type_ = "resume" or "job"
    """
    if not os.path.exists(folder_path):
        print(f"[ERROR] Folder not found: {folder_path}")
        return
    
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    print(f"[INFO] Found {len(pdf_files)} PDF files in {folder_path}")
    
    for fname in pdf_files:
        file_path = os.path.join(folder_path, fname)
        print(f"[INFO] Processing {fname}...")
 
        raw_text = extract_text_from_pdf(file_path)
        if not raw_text or len(raw_text.strip()) < 50:
            print(f"⚠️ Skipped {fname}: No sufficient text found (length: {len(raw_text)}).")
            continue
 
        print(f"[INFO] Extracting entities from {fname}...")
        entities = extract_entities(raw_text)
        print(f"[INFO] Entities extracted: {entities}")
 
        try:
            if type_ == "resume":
                insert_resume(fname, raw_text, entities)
                print(f"✅ [SUCCESS] Inserted resume {fname}")
            elif type_ == "job":
                insert_job(fname, raw_text, entities)
                print(f"✅ [SUCCESS] Inserted job {fname}")
        except Exception as e:
            print(f"❌ [ERROR] Failed to insert {fname}: {str(e)}")
            continue
 
    print(f"[INFO] Completed processing {len(pdf_files)} files")


# Additional utility function for debugging
def preview_pdf_text(file_path: str, num_lines: int = 20) -> str:
    """
    Extract and preview first few lines of PDF text for debugging
    """
    text = extract_text_from_pdf(file_path)
    lines = text.split('\n')[:num_lines]
    return '\n'.join(lines)