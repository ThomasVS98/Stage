from ingestion.preprocessing.docling_parser import extract_with_docling
import sys


def main() -> None:
    """
    CLI entrypoint voor documentextractie via Docling.

    Verwacht twee argumenten:
    1. inputbestand (pad)
    2. outputbestand (pad)

    Leest het inputbestand, extraheert tekst en schrijft deze naar het outputbestand.
    """
    file_path = sys.argv[1]
    output_path = sys.argv[2]
    text = extract_with_docling(file_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
