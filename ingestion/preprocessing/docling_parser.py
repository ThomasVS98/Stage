from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from utils.logging import get_logger
import gc

_converter = None


def get_converter() -> DocumentConverter:
    """
    Initialiseert en cachet een DocumentConverter instantie.

    Configureert parsing opties voor PDF (zonder OCR, met tabelherkenning)
    en hergebruikt deze converter om performance te verbeteren.

    Returns:
        DocumentConverter: Geconfigureerde converter voor document parsing.
    """
    global _converter
    if _converter is None:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = True

        _converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options, backend=PyPdfiumDocumentBackend
                ),
                InputFormat.DOCX: None,
            }
        )
    return _converter


logger = get_logger(__name__)


def extract_with_docling(file_path: str) -> str:
    """
    Extraheert tekst uit een documentbestand met behulp van Docling.

    Ondersteunt o.a. PDF en DOCX en converteert de inhoud naar Markdown.
    Gebruikt een gecachete converter voor performantie.

    Args:
        file_path (str): Pad naar het te verwerken bestand.

    Returns:
        str: Geëxtraheerde tekst in Markdown formaat, of lege string bij fout.
    """
    try:
        converter = get_converter()
        result = converter.convert(file_path)

        text = result.document.export_to_markdown()
        del result

        return text.strip()

    except Exception as e:
        logger.exception("Fout bij het verwerken van %s: %s", file_path, e)
        return ""

    finally:
        gc.collect()
