from ingestion.preprocessing.docling_parser import extract_with_docling
import sys

if __name__ == "__main__":
    file_path = sys.argv[1]
    output_path = sys.argv[2]
    text = extract_with_docling(file_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)