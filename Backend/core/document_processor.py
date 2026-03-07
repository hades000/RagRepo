"""
Document processing: upload, extraction, chunking
"""
import os
from typing import List, Optional, Tuple
from pathlib import Path
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from werkzeug.utils import secure_filename
from config import Config
from utils.pdf_extractor import extract_pdf_content, extract_text_content


class DocumentProcessor:
    """Handle document upload and processing"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """
        Validate uploaded file.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return False, "No filename provided"
        
        if not Config.allowed_file(filename):
            return False, f"File type not allowed. Allowed types: {', '.join(Config.ALLOWED_EXTENSIONS)}"
        
        if file_size > Config.MAX_FILE_SIZE:
            max_mb = Config.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File size exceeds {max_mb}MB limit"
        
        return True, ""
    
    def save_upload(self, file, user_id: str) -> Tuple[str, str]:
        """
        Save uploaded file to disk.
        
        Returns:
            Tuple of (file_path, filename)
        """
        filename = secure_filename(file.filename)
        # Add user_id prefix to avoid conflicts
        unique_filename = f"{user_id}_{filename}"
        file_path = Config.UPLOAD_FOLDER / unique_filename
        
        file.save(str(file_path))
        return str(file_path), filename
    
    def extract_content(self, file_path: str) -> List[dict]:
        """
        Extract content from file based on extension.
        
        Returns:
            List of dicts with 'content', 'page', 'source'
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            return extract_pdf_content(file_path)
        elif file_ext == '.txt':
            return extract_text_content(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def create_documents(
        self, 
        extracted_content: List[dict], 
        filename: str,
        user_id: str
    ) -> List[Document]:
        """
        Create LangChain Document objects from extracted content.
        
        Args:
            extracted_content: List of dicts from extract_content()
            filename: Original filename
            user_id: User ID for metadata
        
        Returns:
            List of Document objects
        """
        documents = []
        
        for item in extracted_content:
            doc = Document(
                page_content=item['content'],
                metadata={
                    'filename': filename,
                    'page': item['page'],
                    'user_id': user_id,
                    'source': filename  # For display purposes
                }
            )
            documents.append(doc)
        
        return documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks.
        
        Args:
            documents: List of Document objects
        
        Returns:
            List of chunked Document objects
        """
        return self.text_splitter.split_documents(documents)
    
    def process_document(
        self, 
        content: bytes, 
        filename: str,
        metadata: Optional[dict] = None
    ) -> List[Document]:
        """
        Process document content directly (for MinIO-fetched documents).
        
        Args:
            content: Document content as bytes
            filename: Original filename
            metadata: Additional metadata dict
        
        Returns:
            List of chunked Document objects
        """
        try:
            # Extract extension to determine processor
            ext = Path(filename).suffix.lower()
            
            # Save content temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                # Extract content based on file type
                extracted = self.extract_content(tmp_path)
                
                # Create documents with metadata
                documents = []
                for item in extracted:
                    doc_metadata = {
                        'filename': filename,
                        'page': item.get('page', 0),
                        'source': filename,
                        **(metadata or {})
                    }
                    
                    doc = Document(
                        page_content=item['content'],
                        metadata=doc_metadata
                    )
                    documents.append(doc)
                
                # Chunk documents
                chunks = self.chunk_documents(documents)
                
                print(f"📄 Processed {filename}: {len(chunks)} chunks created")
                return chunks
                
            finally:
                # Clean up temp file
                import os
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Error processing document {filename}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def process_file(
        self, 
        file, 
        user_id: str
    ) -> Tuple[List[Document], str, int, str]:
        """
        Complete file processing pipeline.
        
        Args:
            file: Werkzeug FileStorage object
            user_id: User ID
        
        Returns:
            Tuple of (chunks, filename, file_size, file_path)
        
        Raises:
            ValueError: If validation fails or processing errors occur
        """
        # Get file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        # Validate
        is_valid, error_msg = self.validate_file(file.filename, file_size)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Save file
        file_path, filename = self.save_upload(file, user_id)
        
        try:
            # Extract content
            extracted_content = self.extract_content(file_path)
            
            if not extracted_content:
                raise ValueError("No content could be extracted from the file")
            
            # Create documents
            documents = self.create_documents(extracted_content, filename, user_id)
            
            # Chunk documents
            chunks = self.chunk_documents(documents)
            
            if not chunks:
                raise ValueError("No text chunks created from document")
            
            print(f"✅ Processed {filename}: {len(chunks)} chunks created")
            
            return chunks, filename, file_size, file_path
            
        except Exception as e:
            # Clean up file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
    
    def cleanup_file(self, file_path: str):
        """Remove uploaded file from disk"""
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Removed file: {file_path}")