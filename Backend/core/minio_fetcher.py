"""
MinIO fetcher service for retrieving documents from object storage
"""
from typing import Optional, BinaryIO, Any
from pathlib import Path
from minio import Minio
from minio.error import S3Error
import os
import tempfile


class MinIOFetcher:
    """Service for fetching documents from MinIO object storage"""
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        secure: bool = True
    ):
        """
        Initialize MinIO fetcher.
        
        Args:
            endpoint: MinIO endpoint (e.g., 'minio.example.com:9000')
            access_key: Access key
            secret_key: Secret key
            bucket_name: Default bucket name
            secure: Use HTTPS
        """
        self.endpoint = endpoint or os.getenv('MINIO_ENDPOINT', 'localhost:9000')
        self.access_key = access_key or os.getenv('MINIO_ACCESS_KEY')
        self.secret_key = secret_key or os.getenv('MINIO_SECRET_KEY')
        self.bucket_name = bucket_name or os.getenv('MINIO_BUCKET', 'documents')
        self.secure = secure
        
        # Initialize MinIO client
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=os.getenv('MINIO_SECURE', 'false').lower() == 'true',
        )
        
        print(f"🪣 MinIO client initialized:")
        print(f"   Endpoint: {self.endpoint}")
        print(f"   Bucket: {self.bucket_name}")
        print(f"   Secure: {self.secure}")
    
    def check_connection(self) -> bool:
        """
        Check if connection to MinIO is working.
        
        Returns:
            True if connection successful
        """
        try:
            # Try to check if bucket exists
            self.client.bucket_exists(self.bucket_name)
            print(f"✅ MinIO connection successful")
            return True
        except S3Error as e:
            print(f"❌ MinIO connection failed: {e}")
            return False
        except Exception as e:
            print(f"❌ MinIO connection error: {e}")
            return False
    
    def download_file(
        self, 
        object_name: str, 
        destination_path: Optional[str] = None,
        bucket_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Download file from MinIO to local path.
        
        Args:
            object_name: Object name in MinIO (e.g., 'docs/file.pdf')
            destination_path: Local destination path (optional)
            bucket_name: Bucket name (uses default if not provided)
            
        Returns:
            Path to downloaded file, or None if failed
        """
        bucket = bucket_name or self.bucket_name
        
        try:
            # Create temp file if no destination provided
            if destination_path is None:
                # Extract extension from object name
                ext = Path(object_name).suffix
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix=ext
                )
                destination_path = temp_file.name
                temp_file.close()
            
            # Ensure parent directory exists
            Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            self.client.fget_object(bucket, object_name, destination_path)
            
            print(f"✅ Downloaded: {object_name} → {destination_path}")
            return destination_path
            
        except S3Error as e:
            print(f"❌ MinIO download error: {e}")
            return None
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None
    
    def get_file_stream(
        self, 
        object_name: str, 
        bucket_name: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get file as stream (for large files).
        
        Args:
            object_name: Object name in MinIO
            bucket_name: Bucket name (uses default if not provided)
            
        Returns:
            BaseHTTPResponse object (file stream), or None if failed
        """
        bucket = bucket_name or self.bucket_name
        
        try:
            response = self.client.get_object(bucket, object_name)
            return response
        except S3Error as e:
            print(f"❌ MinIO stream error: {e}")
            return None
        except Exception as e:
            print(f"❌ Stream error: {e}")
            return None
        
    async def fetch_document(
        self, 
        file_url: str, 
        bucket_name: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Fetch document content as bytes from MinIO.
        
        This is an async wrapper for document synchronization.
        
        Args:
            file_url: Full file URL or object name
            bucket_name: Bucket name (uses default if not provided)
            
        Returns:
            Document content as bytes, or None if failed
        """
        # Extract object name from URL if needed
        # URLs from database might be like: 'https://minio.com:9000/bucket/path/file.pdf'
        # or just 'path/file.pdf'
        object_name = file_url
        
        # If it's a full URL, extract just the object path
        if file_url.startswith('http://') or file_url.startswith('https://'):
            from urllib.parse import urlparse
            parsed = urlparse(file_url)
            # Remove leading bucket name if present in path
            path_parts = parsed.path.strip('/').split('/', 1)
            if len(path_parts) > 1 and path_parts[0] == (bucket_name or self.bucket_name):
                object_name = path_parts[1]
            else:
                object_name = parsed.path.strip('/')
        
        bucket = bucket_name or self.bucket_name
        
        try:
            # Get file stream
            response = self.client.get_object(bucket, object_name)
            
            # Read all data
            data = response.read()
            response.close()
            response.release_conn()
            
            print(f"✅ Fetched: {object_name} ({len(data)} bytes)")
            return data
            
        except S3Error as e:
            print(f"❌ MinIO fetch error for {object_name}: {e}")
            return None
        except Exception as e:
            print(f"❌ Fetch error for {object_name}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def file_exists(
        self, 
        object_name: str, 
        bucket_name: Optional[str] = None
    ) -> bool:
        """
        Check if file exists in MinIO.
        
        Args:
            object_name: Object name
            bucket_name: Bucket name
            
        Returns:
            True if file exists
        """
        bucket = bucket_name or self.bucket_name
        
        try:
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False
        except Exception:
            return False
    
    def get_file_metadata(
        self, 
        object_name: str, 
        bucket_name: Optional[str] = None
    ) -> Optional[dict]:
        """
        Get file metadata from MinIO.
        
        Args:
            object_name: Object name
            bucket_name: Bucket name
            
        Returns:
            Dictionary with metadata, or None if failed
        """
        bucket = bucket_name or self.bucket_name
        
        try:
            stat = self.client.stat_object(bucket, object_name)
            return {
                'object_name': stat.object_name,
                'size': stat.size,
                'last_modified': stat.last_modified,
                'content_type': stat.content_type,
                'etag': stat.etag,
                'metadata': stat.metadata
            }
        except S3Error as e:
            print(f"❌ MinIO metadata error: {e}")
            return None
        except Exception as e:
            print(f"❌ Metadata error: {e}")
            return None
    
    def list_objects(
        self, 
        prefix: str = '', 
        bucket_name: Optional[str] = None
    ) -> list:
        """
        List objects in bucket with optional prefix.
        
        Args:
            prefix: Object name prefix filter
            bucket_name: Bucket name
            
        Returns:
            List of object names
        """
        bucket = bucket_name or self.bucket_name
        
        try:
            objects = self.client.list_objects(bucket, prefix=prefix)
            object_list = [obj.object_name for obj in objects]
            print(f"📋 Found {len(object_list)} objects with prefix '{prefix}'")
            return object_list
        except S3Error as e:
            print(f"❌ MinIO list error: {e}")
            return []
        except Exception as e:
            print(f"❌ List error: {e}")
            return []