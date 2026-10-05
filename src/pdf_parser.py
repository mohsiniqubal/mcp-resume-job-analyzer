from pathlib import Path

import pymupdf


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from all pages of a PDF resume.
    """

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    text_parts = []

    with pymupdf.open(path) as document:

        if len(document) == 0:
            raise ValueError("The PDF contains no pages.")

        for page in document:
            text = page.get_text("text")

            if text:
                text_parts.append(text.strip())

    extracted_text = "\n\n".join(text_parts).strip()

    if not extracted_text:
        raise ValueError(
            "No text could be extracted from this PDF. "
            "It may be a scanned/image-only PDF."
        )

    return extracted_text