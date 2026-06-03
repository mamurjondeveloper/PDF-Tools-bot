import asyncio
import logging
from PIL import Image

logger = logging.getLogger(__name__)

def _images_to_pdf_sync(image_paths: list[str], output_path: str) -> None:
    """Synchronously converts a list of images into a single PDF."""
    if not image_paths:
        raise ValueError("No images provided for PDF conversion.")
        
    opened_images = []
    try:
        for path in image_paths:
            img = Image.open(path)
            # Convert to RGB mode (required for saving as PDF, handles RGBA/PNG)
            if img.mode != "RGB":
                img = img.convert("RGB")
            opened_images.append(img)
            
        if not opened_images:
            raise ValueError("Failed to open or convert any images.")
            
        # Save as PDF
        primary_img = opened_images[0]
        other_imgs = opened_images[1:]
        
        primary_img.save(
            output_path,
            "PDF",
            save_all=True,
            append_images=other_imgs,
            quality=100
        )
    finally:
        for img in opened_images:
            try:
                img.close()
            except Exception as e:
                logger.error(f"Error closing image: {e}")

async def images_to_pdf(image_paths: list[str], output_path: str) -> None:
    """Asynchronously converts multiple images to a single PDF, preserving order."""
    await asyncio.to_thread(_images_to_pdf_sync, image_paths, output_path)
