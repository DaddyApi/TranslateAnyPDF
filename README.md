# TranslateAnyPDF - Python Client & Batch Tester

This directory contains Python scripts to interact with the **TranslateAnyPDF API**, available on the RapidAPI marketplace. Translate your PDF documents into multiple languages while striving to maintain the original layout and formatting!

Our service focuses on delivering high-quality translations that respect the structure of your documents.

**This client allows you to:**
*   Translate individual PDF files.
*   Analyze PDFs to get page count, character count, and other metadata.
*   Batch translate a single PDF into multiple languages for testing and evaluation.

## Features of the TranslateAnyPDF API

*   🌟 **Superior Layout Preservation:** Our core focus! We work hard to keep your document's structure coherent post-translation.
*   🌐 **Multiple Language Support:** Translate your documents to and from a wide range of languages.
*   ⚙️ **Asynchronous Processing:** Submit your PDF, poll for status, and get a download link when ready.
*   📊 **Tiered Processing:** Choose from `small`, `medium`, or `large` tiers to match your document's size and complexity.
*   🔎 **PDF Analysis Utility:** Get insights into your PDF before translating.

## Setup

### Requirements
*   Python 3.7+
*   `requests` library (install with `pip install requests`)

### Installation
1.  Clone this repository or download the scripts from the `github_client` directory.
2.  Navigate to the `github_client` directory:
    ```bash
    cd github_client
    ```

### Get Your RapidAPI Key
1.  Subscribe to the TranslateAnyPDF API on RapidAPI: [Link to your API on RapidAPI]
2.  Once subscribed, you will find your `X-RapidAPI-Key` in your RapidAPI dashboard.
3.  You can provide this key to the scripts either via the `--api_key` command-line argument or by setting the `RAPIDAPI_KEY` environment variable.

## Using the Client (`app.py`)

The `app.py` script is the main client for translating single files or analyzing them.

**1. Translate a PDF:**

```bash
python3 app.py translate path/to/your/document.pdf <target_language_code> <tier> --api_key YOUR_RAPIDAPI_KEY
```

*   **`path/to/your/document.pdf`**: The PDF file you want to translate.
*   **`<target_language_code>`**: The language to translate into (e.g., `es` for Spanish, `fr` for French, `de` for German). See `SUPPORTED_TARGET_LANGUAGES` in `app.py` for a list.
*   **`<tier>`**: The processing tier (`small`, `medium`, or `large`).
*   **`--api_key YOUR_RAPIDAPI_KEY`**: Your personal key from RapidAPI.
*   **`--output_file path/to/save/translated.pdf`** (Optional): Specify where to save the translated PDF. Defaults to a `translated_pdfs` subdirectory with a generated name.

**Example:**
```bash
python3 app.py translate ../test_pdfs/actual_small_sample.pdf es small --api_key YOUR_KEY_HERE
```

**2. Analyze a PDF:**

```bash
python3 app.py analyze path/to/your/document.pdf --api_key YOUR_KEY_HERE
```

*   This will return metadata about the PDF, such as page count, character count, word count, and text extractability.

**Example:**
```bash
python3 app.py analyze ../test_pdfs/actual_small_sample.pdf --api_key YOUR_KEY_HERE
```

## Batch Translation Testing (`batch_translate_test.py`)

The `batch_translate_test.py` script is designed for testing the translation of a single PDF into multiple languages. This is particularly useful for evaluating font rendering and translation quality across different languages.

**Prerequisites:**
*   A `languages.csv` file in the root directory of the project (or specify its path). This file should have a header `language_code` and list the language codes you want to test, one per line. A sample `languages.csv` containing all languages included.

**Usage:**
```bash
python3 batch_translate_test.py --input_pdf path/to/your/test_document.pdf --api_key YOUR_RAPIDAPI_KEY
```

*   **`--input_pdf`**: The PDF to translate into multiple languages. Defaults to `../test_pdfs/actual_small_sample.pdf` relative to the `api_rapidapi` directory.
*   **`--api_key YOUR_RAPIDAPI_KEY`**: Your personal key.
*   **`--tier`** (Optional): Translation tier (`small`, `medium`, `large`). Defaults to `small`.
*   **`--output_dir`** (Optional): Base directory to save translated PDFs. Defaults to `./language_test_outputs/`. Each language will get its own subfolder.
*   **`--languages_csv`** (Optional): Path to your `languages.csv` file. Defaults to looking for `languages.csv` (relative to the script's location).

**Example:**
```bash
# Assuming languages.csv is in the project root (pdf_translator_2/languages.csv)
# and using the default example PDF from api_rapidapi/test_pdfs/
python3 batch_translate_test.py --api_key YOUR_KEY_HERE
```
This will create folders like `language_test_outputs/es/`, `language_test_outputs/fr/`, etc., each containing the translated version of your input PDF.

## API & Service Information

*   **RapidAPI Marketplace:** Find pricing, subscribe, and manage your API key here: [Link to your API on RapidAPI - YOU NEED TO ADD THIS LINK!]
*   The API is asynchronous. You submit a job, poll for status, and then download the result.
*   For best layout preservation, use PDFs with selectable text. Scanned image-based PDFs are not suitable for layout-preserving translation with this service.

## Support & Feedback

While this client script is provided for convenience, direct support for the script itself is limited.
For issues or feedback related to the **TranslateAnyPDF API service**, please use the support channels provided on the RapidAPI marketplace or visit our website.

## ✨ Visit TranslateAnyPDF.com! ✨

Interested in learning more about our translation technology, upcoming features (like our user-friendly web application!), or discussing higher volume needs?

➡️ **Check out our main site: [https://translateanypdf.com](https://translateanypdf.com)**

We're committed to improving document translation and value your feedback!
