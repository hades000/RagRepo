"""
PDF text extraction with multiple fallback methods
"""
from typing import List, Dict, Any
import fitz  # PyMuPDF
from pathlib import Path


def extract_pdf_content(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract text content from PDF using PyMuPDF (primary) with pypdf fallback.
    
    Returns:
        List of dictionaries with 'content', 'page', and 'source'
    """
    extracted_content = []
    
    # Try PyMuPDF first (best for complex PDFs)
    try:
        doc = fitz.open(file_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            # Extract text only (table extraction requires different approach)
            page_content = str(text) if text else ""
            
            if page_content and page_content.strip():
                extracted_content.append({
                    'content': page_content,
                    'page': page_num + 1,
                    'source': file_path
                })
        
        doc.close()
        
        if extracted_content:
            print(f"✅ PyMuPDF extracted {len(extracted_content)} pages")
            return extracted_content
        
        print(f"⚠️ PyMuPDF found no content, trying fallback...")
        
    except Exception as e:
        print(f"❌ PyMuPDF extraction failed: {e}, trying fallback...")
    
    # Fallback to pypdf
    try:
        from pypdf import PdfReader
        
        reader = PdfReader(file_path)
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            
            if text and text.strip():
                extracted_content.append({
                    'content': text,
                    'page': page_num + 1,
                    'source': file_path
                })
        
        if extracted_content:
            print(f"✅ pypdf extracted {len(extracted_content)} pages")
            return extracted_content
        
        print(f"⚠️ pypdf found no content")
        
    except Exception as e:
        print(f"❌ pypdf extraction failed: {e}")
    
    # If all methods failed
    if not extracted_content:
        print(f"❌ All PDF extraction methods failed for {file_path}")
    
    return extracted_content


def extract_text_content(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract content from plain text file.
    
    Returns:
        List with single dictionary containing file content
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.strip():
            return [{
                'content': content,
                'page': 1,
                'source': file_path
            }]
        
        return []
        
    except Exception as e:
        print(f"❌ Text file extraction failed: {e}")
        return []