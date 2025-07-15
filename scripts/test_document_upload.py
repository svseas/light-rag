#!/usr/bin/env python3
"""Test script for document upload and processing."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logfire

from backend.core.config import configure_logfire, setup_directories
from backend.models.documents import DocumentCreate
from backend.services.document_service import document_service


async def test_document_upload():
    """Test document upload with PDF files."""
    print("LightRAG Document Upload Test")
    print("=" * 30)
    
    # Configure logfire
    configure_logfire()
    setup_directories()
    
    # Get uploads directory
    uploads_dir = Path("uploads")
    pdf_files = list(uploads_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in uploads directory")
        return
    
    # Test with first PDF file
    test_file = pdf_files[0]
    print(f"Testing with: {test_file.name}")
    
    try:
        # Get file info
        file_size = test_file.stat().st_size
        print(f"File size: {file_size:,} bytes")
        
        # Create document data
        document_data = DocumentCreate(
            name=test_file.name,
            original_format=test_file.suffix,
            file_path=str(test_file),
            file_size=file_size,
        )
        
        print(f"Creating document: {document_data.name}")
        
        # Upload document
        with logfire.span("test_document_upload"):
            result = await document_service.create_document(document_data)
            
            print(f"Document uploaded successfully!")
            print(f"Document ID: {result.document_id}")
            print(f"Status: {result.processing_status}")
            print(f"Message: {result.message}")
            
            # Wait a moment for processing
            await asyncio.sleep(2)
            
            # Check processing status
            print("\nChecking processing status...")
            processing = await document_service.get_processing_status(result.document_id)
            print(f"Status: {processing.status}")
            print(f"Progress: {processing.progress:.1%}")
            
            if processing.error_message:
                print(f"Error: {processing.error_message}")
            
            # Get document content
            if processing.status == "completed":
                print("\nRetrieving processed document...")
                document = await document_service.get_document(result.document_id)
                
                if document.content_md:
                    print(f"Content length: {len(document.content_md)} characters")
                    print(f"Content preview: {document.content_md[:200]}...")
                else:
                    print("No content available")
            
    except Exception as e:
        print(f"Error during upload: {e}")
        logfire.error("Document upload test failed", error=str(e))


async def main():
    """Main test function."""
    await test_document_upload()


if __name__ == "__main__":
    asyncio.run(main())