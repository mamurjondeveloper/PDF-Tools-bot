import sys
import asyncio
import logging

logger = logging.getLogger(__name__)

def _doc_to_pdf_sync(doc_path: str, output_path: str) -> None:
    """Synchronously converts a DOC/DOCX file to PDF using Microsoft Word via COM (Windows only)."""
    if sys.platform != "win32":
        raise NotImplementedError("DOC/DOCX to PDF conversion is currently only supported on Windows hosts.")
        
    import pythoncom
    # Initialize COM library for the current thread to avoid CoInitialize error
    pythoncom.CoInitialize()
    try:
        from docx2pdf import convert
        convert(doc_path, output_path)
    except Exception as e:
        logger.error(f"Failed to convert Word document to PDF: {e}", exc_info=True)
        raise RuntimeError("Microsoft Word failed to convert this document. Ensure Microsoft Word is installed and activated.")
    finally:
        pythoncom.CoUninitialize()

async def doc_to_pdf(doc_path: str, output_path: str) -> None:
    """Asynchronously converts DOC or DOCX to PDF, wrapping the COM execution in a thread."""
    await asyncio.to_thread(_doc_to_pdf_sync, doc_path, output_path)
