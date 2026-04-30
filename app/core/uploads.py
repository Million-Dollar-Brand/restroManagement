import os
import uuid
from fastapi import UploadFile, HTTPException
from starlette.responses import FileResponse
from app.config import settings


async def save_upload_file(upload_file: UploadFile, subfolder: str = "temp") -> str:
    """
    Save an uploaded file to the filesystem

    Args:
        upload_file: FastAPI UploadFile object
        subfolder: Subfolder within upload dir (profiles, products, temp)

    Returns:
        Relative file path
    """
    # Validate file extension
    file_ext = os.path.splitext(upload_file.filename)[1].lower().lstrip('.')
    allowed = [ext.strip().lower() for ext in settings.allowed_extensions.split(',')]

    if file_ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed)}"
        )

    # Check file size
    contents = await upload_file.read()
    if len(contents) > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.max_file_size / 1024 / 1024:.1f}MB"
        )

    # Reset file pointer
    await upload_file.seek(0)

    # Generate unique filename
    unique_id = str(uuid.uuid4())[:8]
    safe_filename = f"{unique_id}_{upload_file.filename}"
    upload_path = os.path.join(settings.upload_dir, subfolder, safe_filename)

    # Ensure directory exists
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)

    # Save file
    with open(upload_path, "wb") as buffer:
        content = await upload_file.read()
        buffer.write(content)

    # Return relative path for storage in database
    return os.path.join(subfolder, safe_filename)


def get_file_url(file_path: str, base_url: str = "http://localhost:8000") -> str:
    """Generate full URL for uploaded file"""
    if not file_path:
        return None
    return f"{base_url}/uploads/{file_path}"


async def delete_file(file_path: str) -> bool:
    """Delete a file from filesystem"""
    if not file_path:
        return False

    full_path = os.path.join(settings.upload_dir, file_path)
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    except Exception:
        pass
    return False
