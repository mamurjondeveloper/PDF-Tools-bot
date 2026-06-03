import os
import asyncio
import logging
from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

def _merge_pdfs_sync(file_paths: list[str], output_path: str) -> None:
    """Synchronous implementation of PDF merging."""
    writer = PdfWriter()
    try:
        for path in file_paths:
            writer.append(path)
        with open(output_path, "wb") as f:
            writer.write(f)
    finally:
        writer.close()


async def merge_pdfs(file_paths: list[str], output_path: str) -> None:
    """Asynchronously merges multiple PDFs in the specified order."""
    await asyncio.to_thread(_merge_pdfs_sync, file_paths, output_path)

def _split_all_pages_sync(file_path: str, output_dir: str) -> list[str]:
    """Synchronous implementation of splitting every page into individual PDFs."""
    reader = PdfReader(file_path)
    generated_files = []
    
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        
        output_filename = f"page_{i + 1}.pdf"
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, "wb") as f:
            writer.write(f)
            
        generated_files.append(output_path)
        
    return generated_files

async def split_all_pages(file_path: str, output_dir: str) -> list[str]:
    """Asynchronously splits every page of a PDF into individual files."""
    return await asyncio.to_thread(_split_all_pages_sync, file_path, output_dir)

def parse_range_string(range_str: str, max_pages: int) -> list[int]:
    """Parses a user-friendly page range string (e.g., '1-3, 5, 7-9') into 0-indexed page numbers."""
    pages = []
    parts = range_str.split(",")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                start_str, end_str = part.split("-", 1)
                start = int(start_str.strip())
                end = int(end_str.strip())
                if start <= end:
                    for p in range(start, end + 1):
                        if 1 <= p <= max_pages:
                            pages.append(p - 1)
            except ValueError:
                logger.warning(f"Invalid range part: {part}")
                continue
        else:
            try:
                p = int(part)
                if 1 <= p <= max_pages:
                    pages.append(p - 1)
            except ValueError:
                logger.warning(f"Invalid page number part: {part}")
                continue
    # De-duplicate while preserving order
    return list(dict.fromkeys(pages))

def get_pdf_page_count(file_path: str) -> int:
    """Returns the total number of pages in a PDF."""
    try:
        reader = PdfReader(file_path)
        return len(reader.pages)
    except Exception as e:
        logger.error(f"Error reading PDF page count: {e}")
        raise ValueError("Invalid or corrupted PDF file.")

def _extract_pages_sync(file_path: str, pages: list[int], output_path: str) -> None:
    """Synchronous implementation of page extraction."""
    reader = PdfReader(file_path)
    writer = PdfWriter()
    
    for page_idx in pages:
        writer.add_page(reader.pages[page_idx])
        
    with open(output_path, "wb") as f:
        writer.write(f)

async def extract_pdf_pages(file_path: str, range_str: str, output_path: str) -> None:
    """Asynchronously extracts specified page ranges and writes them to a new PDF."""
    max_pages = get_pdf_page_count(file_path)
    pages = parse_range_string(range_str, max_pages)
    
    if not pages:
        raise ValueError("No valid page numbers found in range.")
        
    await asyncio.to_thread(_extract_pages_sync, file_path, pages, output_path)
