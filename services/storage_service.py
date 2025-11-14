"""
Storage Service Layer  
Handles file uploads to cloud storage
Note: Requires GCS or S3 configuration
"""
import os
import uuid
import logging
from typing import Optional, BinaryIO
from datetime import timedelta

logger = logging.getLogger(__name__)

# GCS configuration
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "rnrltradehub-documents")
GCS_PROJECT_ID = os.getenv("GCS_PROJECT_ID")


class StorageService:
    """Cloud storage service for file uploads."""
    
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.docx', '.xlsx'}
    
    @staticmethod
    def validate_file(filename: str, file_size: int) -> tuple[bool, Optional[str]]:
        """
        Validate file before upload.
        Returns (is_valid, error_message)
        """
        # Check file size
        if file_size > StorageService.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum of {StorageService.MAX_FILE_SIZE / (1024*1024)}MB"
        
        # Check extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in StorageService.ALLOWED_EXTENSIONS:
            return False, f"File type {ext} not allowed. Allowed types: {', '.join(StorageService.ALLOWED_EXTENSIONS)}"
        
        return True, None
    
    @staticmethod
    async def upload_file(
        file_content: BinaryIO,
        filename: str,
        folder: str = "documents"
    ) -> Optional[str]:
        """
        Upload file to cloud storage.
        Returns the file URL if successful, None otherwise.
        """
        try:
            # Generate unique filename
            ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4()}{ext}"
            blob_name = f"{folder}/{unique_filename}"
            
            if GCS_BUCKET_NAME and GCS_PROJECT_ID:
                # Use Google Cloud Storage
                from google.cloud import storage
                
                client = storage.Client(project=GCS_PROJECT_ID)
                bucket = client.bucket(GCS_BUCKET_NAME)
                blob = bucket.blob(blob_name)
                
                # Upload file
                blob.upload_from_file(file_content)
                
                # Make publicly accessible (or use signed URLs)
                blob.make_public()
                
                logger.info(f"File uploaded to GCS: {blob_name}")
                return blob.public_url
            
            else:
                # Mock upload for development
                mock_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{blob_name}"
                logger.warning(f"[MOCK UPLOAD] File: {filename}, URL: {mock_url}")
                return mock_url
        
        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {e}")
            return None
    
    @staticmethod
    async def generate_signed_url(blob_name: str, expiration_hours: int = 1) -> Optional[str]:
        """
        Generate a signed URL for secure file access.
        Returns signed URL if successful, None otherwise.
        """
        try:
            if GCS_BUCKET_NAME and GCS_PROJECT_ID:
                from google.cloud import storage
                
                client = storage.Client(project=GCS_PROJECT_ID)
                bucket = client.bucket(GCS_BUCKET_NAME)
                blob = bucket.blob(blob_name)
                
                # Generate signed URL
                url = blob.generate_signed_url(
                    expiration=timedelta(hours=expiration_hours),
                    method='GET'
                )
                
                logger.info(f"Generated signed URL for: {blob_name}")
                return url
            
            else:
                # Mock signed URL
                mock_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{blob_name}?signed=true"
                logger.warning(f"[MOCK SIGNED URL] {mock_url}")
                return mock_url
        
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {blob_name}: {e}")
            return None
    
    @staticmethod
    async def delete_file(blob_name: str) -> bool:
        """
        Delete file from cloud storage.
        Returns True if successful, False otherwise.
        """
        try:
            if GCS_BUCKET_NAME and GCS_PROJECT_ID:
                from google.cloud import storage
                
                client = storage.Client(project=GCS_PROJECT_ID)
                bucket = client.bucket(GCS_BUCKET_NAME)
                blob = bucket.blob(blob_name)
                
                blob.delete()
                
                logger.info(f"File deleted from GCS: {blob_name}")
                return True
            
            else:
                # Mock deletion
                logger.warning(f"[MOCK DELETE] File: {blob_name}")
                return True
        
        except Exception as e:
            logger.error(f"Failed to delete file {blob_name}: {e}")
            return False
    
    @staticmethod
    async def upload_document(
        file_content: BinaryIO,
        filename: str,
        document_type: str,
        partner_id: Optional[str] = None
    ) -> Optional[str]:
        """Upload a business document."""
        folder = f"documents/{document_type}"
        if partner_id:
            folder = f"{folder}/{partner_id}"
        
        return await StorageService.upload_file(file_content, filename, folder)
    
    @staticmethod
    async def upload_kyc_document(
        file_content: BinaryIO,
        filename: str,
        partner_id: str,
        doc_type: str
    ) -> Optional[str]:
        """Upload KYC document."""
        folder = f"kyc/{partner_id}/{doc_type}"
        return await StorageService.upload_file(file_content, filename, folder)
    
    @staticmethod
    async def upload_certification(
        file_content: BinaryIO,
        filename: str,
        partner_id: str,
        certification_id: str
    ) -> Optional[str]:
        """Upload certification document."""
        folder = f"certifications/{partner_id}/{certification_id}"
        return await StorageService.upload_file(file_content, filename, folder)
