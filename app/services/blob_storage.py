"""
Vercel Blob Storage Service for card images.

This service handles uploading and managing card images in Vercel Blob storage.
Images are fetched from eBay listing URLs and stored with consistent naming.

Environment Variables:
- BLOB_READ_WRITE_TOKEN: Vercel Blob API token (required)

Usage:
    from app.services.blob_storage import BlobStorageService

    service = BlobStorageService()
    blob_url = await service.upload_card_image(card_id=123, source_url="https://i.ebayimg.com/...")
"""

import os
import httpx
import hashlib
from typing import Optional
from urllib.parse import urlparse


class BlobStorageService:
    """Service for uploading images to Vercel Blob storage."""

    def __init__(self):
        self.token = os.getenv("BLOB_READ_WRITE_TOKEN")
        self.base_url = "https://blob.vercel-storage.com"

    def is_configured(self) -> bool:
        """Check if Vercel Blob is properly configured."""
        return bool(self.token)

    async def upload_card_image(
        self,
        card_id: int,
        source_url: str,
        card_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Download image from source URL and upload to Vercel Blob.

        Args:
            card_id: The card's database ID
            source_url: URL to fetch the image from (e.g., eBay image URL)
            card_name: Optional card name for better file naming

        Returns:
            The Vercel Blob URL if successful, None otherwise
        """
        if not self.is_configured():
            print("Vercel Blob not configured - missing BLOB_READ_WRITE_TOKEN")
            return None

        try:
            # Download the image
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(source_url, follow_redirects=True)
                response.raise_for_status()
                image_data = response.content
                content_type = response.headers.get("content-type", "image/jpeg")

            # Generate a consistent filename
            # Use hash of card_id to ensure unique but reproducible names
            file_ext = self._get_extension(content_type, source_url)
            filename = f"cards/{card_id}{file_ext}"

            # Upload to Vercel Blob
            blob_url = await self._upload_to_blob(
                filename=filename,
                data=image_data,
                content_type=content_type,
            )

            return blob_url

        except Exception as e:
            print(f"Error uploading card image {card_id}: {e}")
            return None

    async def upload_listing_image(
        self,
        listing_id: int,
        source_url: str,
    ) -> Optional[str]:
        """
        Upload a listing image to Vercel Blob.

        Args:
            listing_id: The listing's database ID
            source_url: URL to fetch the image from

        Returns:
            The Vercel Blob URL if successful, None otherwise
        """
        if not self.is_configured():
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(source_url, follow_redirects=True)
                response.raise_for_status()
                image_data = response.content
                content_type = response.headers.get("content-type", "image/jpeg")

            file_ext = self._get_extension(content_type, source_url)
            # Use hash for listings to avoid conflicts
            url_hash = hashlib.md5(source_url.encode()).hexdigest()[:8]
            filename = f"listings/{listing_id}-{url_hash}{file_ext}"

            return await self._upload_to_blob(
                filename=filename,
                data=image_data,
                content_type=content_type,
            )

        except Exception as e:
            print(f"Error uploading listing image {listing_id}: {e}")
            return None

    async def _upload_to_blob(
        self,
        filename: str,
        data: bytes,
        content_type: str,
    ) -> Optional[str]:
        """Upload data to Vercel Blob storage."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.put(
                    f"{self.base_url}/{filename}",
                    content=data,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": content_type,
                        "x-api-version": "7",
                        # Allow public access
                        "x-cache-control-max-age": "31536000",  # 1 year cache
                    },
                )
                response.raise_for_status()
                result = response.json()
                return result.get("url")

        except Exception as e:
            print(f"Error uploading to Vercel Blob: {e}")
            return None

    def _get_extension(self, content_type: str, url: str) -> str:
        """Determine file extension from content type or URL."""
        # Try content type first
        type_to_ext = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }
        if content_type in type_to_ext:
            return type_to_ext[content_type]

        # Fall back to URL extension
        parsed = urlparse(url)
        path = parsed.path.lower()
        for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            if path.endswith(ext):
                return ext if ext != ".jpeg" else ".jpg"

        # Default to jpg
        return ".jpg"


# Singleton instance
_blob_service: Optional[BlobStorageService] = None


def get_blob_service() -> BlobStorageService:
    """Get or create the blob storage service singleton."""
    global _blob_service
    if _blob_service is None:
        _blob_service = BlobStorageService()
    return _blob_service
