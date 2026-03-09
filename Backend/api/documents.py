"""
Document viewing API endpoints (view-only, no downloads)
"""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import RedirectResponse, FileResponse
from utils.response import success_response, error_response
from api.deps import get_current_user
from models.database import db_manager
from pathlib import Path
import os
from minio import Minio
from minio.error import S3Error
from datetime import timedelta

router = APIRouter()

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', '')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', '')
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'coreiq-documents')
MINIO_SECURE = os.getenv('MINIO_SECURE', 'false').lower() == 'true'

minio_client = None
if MINIO_ACCESS_KEY and MINIO_SECRET_KEY:
    try:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        print("MinIO client initialized")
    except Exception as e:
        print(f"MinIO initialization failed: {e}")

def get_document_metadata(doc_id: str, user_id: str):
    """Fetch document metadata with access check"""
    if db_manager is None:
        raise RuntimeError("Database manager not initialized")

    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT d.id, d.filename, d.file_url, d.storage_type, d.mime_type,
                   d.file_size, d.upload_timestamp, d.user_id, d.original_path
            FROM rag_documents d
            LEFT JOIN rag_document_access da ON d.id = da.document_id
            WHERE d.id = %s
              AND (d.user_id = %s OR da.user_id = %s)
            LIMIT 1
        """, (doc_id, user_id, user_id))
        return cursor.fetchone()


def get_document_chunks(doc_id: str):
    """Get all text chunks from a document"""
    # Note: You'll need to store chunk data with doc_id in vector store metadata
    # For now, return empty array - implement based on your storage
    return []


@router.get('/documents/{doc_id}')
async def get_document_info(doc_id: str, user: dict = Depends(get_current_user)):
    """
    Get document metadata (for viewing info only).

    Returns:
        Document metadata including filename, size, upload date, etc.
    """
    try:
        user_id = user.get('id')

        if not user_id:
            return error_response("Unauthorized", 401)

        doc = get_document_metadata(doc_id, user_id)

        if not doc:
            return error_response("Document not found or access denied", 404)

        return success_response(
            data={
                'id': doc['id'],
                'filename': doc['filename'],
                'file_size': doc['file_size'],
                'mime_type': doc['mime_type'],
                'upload_timestamp': doc['upload_timestamp'].isoformat() if doc['upload_timestamp'] else None,
                'storage_type': doc['storage_type'],
                'can_view': True,  # Always true if they have access
            },
            message="Document metadata retrieved"
        )

    except Exception as e:
        print(f"Error fetching document: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to retrieve document: {str(e)}", 500)


@router.get('/documents/{doc_id}/view')
async def view_document(doc_id: str, user: dict = Depends(get_current_user)):
    """
    View document content (inline rendering).
    For MinIO: returns a signed URL redirect
    For Local: serves the file directly
    """
    try:
        user_id = user.get('id')

        if not user_id:
            return error_response("Unauthorized", 401)

        doc = get_document_metadata(doc_id, user_id)

        if not doc:
            return error_response("Document not found or access denied", 404)

        file_url = doc['file_url']
        mime_type = doc['mime_type'] or 'application/octet-stream'
        storage_type = doc['storage_type']

        # Handle MinIO/S3 storage
        if storage_type in ['MINIO', 'S3'] and minio_client:
            try:
                # file_url should be the object key in MinIO (e.g., "gmp_6.pdf")
                object_name = file_url

                # Generate a presigned URL for viewing (valid for 1 hour)
                presigned_url = minio_client.presigned_get_object(
                    MINIO_BUCKET,
                    object_name,
                    expires=timedelta(hours=1),
                    response_headers={
                        'Content-Type': mime_type,
                        'Content-Disposition': f'inline; filename="{doc["filename"]}"'
                    }
                )

                # Redirect to the presigned URL
                return RedirectResponse(url=presigned_url)

            except S3Error as e:
                print(f"MinIO error: {e}")
                return error_response(f"Document not found in storage: {str(e)}", 404)

        # Handle local storage
        elif storage_type == 'LOCAL' and file_url:
            file_path = Path(file_url)
            if file_path.exists():
                return FileResponse(
                    path=str(file_path),
                    media_type=mime_type,
                    filename=doc['filename'],
                )
            else:
                return error_response("File not found on server", 404)

        else:
            return error_response("Document viewing not available", 404)

    except Exception as e:
        print(f"Error viewing document: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to view document: {str(e)}", 500)


@router.get('/documents/{doc_id}/chunks')
async def get_document_passages(
    doc_id: str,
    user: dict = Depends(get_current_user),
    page: int = Query(default=1),
    limit: int = Query(default=20),
):
    """
    Get all text passages/chunks from a document.

    Returns:
        List of text chunks with metadata
    """
    try:
        user_id = user.get('id')

        if not user_id:
            return error_response("Unauthorized", 401)

        # Check access
        doc = get_document_metadata(doc_id, user_id)
        if not doc:
            return error_response("Document not found or access denied", 404)

        # Get chunks (implement based on your vector store)
        chunks = get_document_chunks(doc_id)

        total = len(chunks)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_chunks = chunks[start_idx:end_idx]

        return success_response(
            data={
                'chunks': paginated_chunks,
                'total': total,
                'page': page,
                'limit': limit,
                'has_more': end_idx < total
            },
            message=f"Retrieved {len(paginated_chunks)} chunks"
        )

    except Exception as e:
        print(f"Error fetching chunks: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to retrieve chunks: {str(e)}", 500)
