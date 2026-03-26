from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options,
            backend = PyPdfiumDocumentBackend
        ),
        InputFormat.DOCX: None
    }
)

def extract_with_docling(file_path:str) -> str:
    try:
        result = converter.convert(file_path)

        text = result.document.export_to_markdown()

        return text.strip()
    
    except Exception as e:
        print(f"[DOCLING] Fout bij het verwerken van {file_path}: {e}")
        return ""