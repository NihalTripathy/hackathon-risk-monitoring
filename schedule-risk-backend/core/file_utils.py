"""
File utility functions for duplicate detection
"""

import hashlib
from typing import Optional


def compute_file_hash(file_path: str) -> str:
    """
    Compute SHA256 hash of file content
    
    Args:
        file_path: Path to file
        
    Returns:
        SHA256 hash as hexadecimal string (64 characters)
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_content_hash(content: bytes) -> str:
    """
    Compute SHA256 hash of byte content
    
    Args:
        content: File content as bytes
        
    Returns:
        SHA256 hash as hexadecimal string (64 characters)
    """
    return hashlib.sha256(content).hexdigest()

