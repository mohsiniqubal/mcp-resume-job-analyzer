from pathlib import Path

from pdf_parser import extract_text_from_pdf


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def main():

    pdf_files = list(DATA_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No PDF resume found in:")
        print(DATA_DIR)
        return

    if len(pdf_files) > 1:
        print("Multiple PDF files found:")
        for index, pdf in enumerate(pdf_files, start=1):
            print(f"{index}. {pdf.name}")

        print()
        print("Please keep only the resume PDF for this test.")
        return

    pdf_path = pdf_files[0]

    print("Reading resume:")
    print(pdf_path)
    print()

    text = extract_text_from_pdf(str(pdf_path))

    print("PDF extraction successful!")
    print("=" * 60)

    print(text[:3000])

    print()
    print("=" * 60)
    print(f"Extracted characters: {len(text)}")


if __name__ == "__main__":
    main()