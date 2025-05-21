# api_rapidapi/github_client/batch_translate_test.py
import os
import csv
import logging
from pathlib import Path
import argparse
from app import translate_pdf, SUPPORTED_TARGET_LANGUAGES # Import from your existing app.py

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- Configuration ---
DEFAULT_INPUT_PDF = "example.pdf" # Default test PDF
DEFAULT_TIER = "small"
DEFAULT_OUTPUT_DIR_BASE = Path.cwd() / "language_test_outputs"

def run_batch_translation_test(api_key: str, input_pdf: Path, tier: str, output_dir_base: Path, languages_csv_path: Path):
    log.info("--- Starting Batch Language Translation Test ---")
    log.info(f"Input PDF: {input_pdf}")
    log.info(f"Tier: {tier}")
    log.info(f"Base Output Directory: {output_dir_base}")
    log.info(f"Languages CSV: {languages_csv_path}")

    if not api_key:
        log.error("RapidAPI Key is required. Please provide it via --api_key argument or set the RAPIDAPI_KEY environment variable.")
        return

    if not input_pdf.exists():
        log.error(f"Input PDF {input_pdf} not found. Aborting.")
        return
    
    if not languages_csv_path.exists():
        log.error(f"Languages CSV file {languages_csv_path} not found. Aborting.")
        return

    languages_to_test = []
    try:
        with open(languages_csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            if 'language_code' not in reader.fieldnames:
                log.error("CSV file must contain a 'language_code' header.")
                return
            for row in reader:
                languages_to_test.append(row['language_code'])
        log.info(f"Found {len(languages_to_test)} languages to test: {languages_to_test}")
    except Exception as e:
        log.error(f"Failed to read or parse languages CSV: {e}")
        return

    if not languages_to_test:
        log.info("No languages found in CSV to test.")
        return

    for lang_code in languages_to_test:
        log.info(f"\\n--- Testing Language: {lang_code} ---")
        
        # Validate against the list in app.py if you want an additional check,
        # though your API should handle invalid lang codes gracefully anyway.
        if lang_code not in SUPPORTED_TARGET_LANGUAGES:
            log.warning(f"Language code '{lang_code}' from CSV is not in app.py's SUPPORTED_TARGET_LANGUAGES list. Attempting anyway...")

        lang_output_dir = output_dir_base #/ lang_code
        # lang_output_dir.mkdir(parents=True, exist_ok=True)
        output_pdf_path = lang_output_dir / f"translated_{input_pdf.stem}_{lang_code}{input_pdf.suffix}"

        try:
            success = translate_pdf(
                api_key=api_key,
                pdf_path=input_pdf,
                target_lang=lang_code,
                tier=tier,
                output_path=output_pdf_path
            )
            if success:
                log.info(f"Successfully translated and saved for language '{lang_code}' to {output_pdf_path}")
            else:
                log.error(f"Translation failed for language '{lang_code}'. Check previous logs.")
        except Exception as e:
            log.error(f"An unexpected error occurred while processing language {lang_code}: {e}", exc_info=True)
        
        log.info(f"--- Finished Testing Language: {lang_code} ---")

    log.info("\\n--- Batch Language Translation Test Finished ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch translate a PDF into multiple languages using TranslateAnyPDF API.")
    parser.add_argument("--api_key", type=str, default=os.getenv("RAPIDAPI_KEY"), help="Your RapidAPI Key. Can also be set via RAPIDAPI_KEY env var.")
    parser.add_argument("--input_pdf", type=Path, default=DEFAULT_INPUT_PDF, help=f"Path to the PDF file to translate. Default: {DEFAULT_INPUT_PDF}")
    parser.add_argument("--tier", type=str, default=DEFAULT_TIER, choices=['small', 'medium', 'large'], help=f"Processing tier for the translation. Default: {DEFAULT_TIER}")
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR_BASE, help=f"Base directory to save translated PDFs. Default: {DEFAULT_OUTPUT_DIR_BASE}")
    parser.add_argument("--languages_csv", type=Path, default=Path(__file__).parent.parent.parent / "languages.csv", help="Path to the CSV file containing language codes. Default: ../../languages.csv")

    args = parser.parse_args()

    run_batch_translation_test(
        api_key=args.api_key,
        input_pdf=args.input_pdf.resolve(),
        tier=args.tier,
        output_dir_base=args.output_dir.resolve(),
        languages_csv_path=args.languages_csv.resolve()
    ) 