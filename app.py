# translate_pdf_client.py
import os
import time
import requests
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


# --- Configuration ---
# The RapidAPI Host will be specific to your API on the platform
RAPIDAPI_HOST = "translateanypdf.p.rapidapi.com" 
BASE_URL = f"https://{RAPIDAPI_HOST}"

# --- Helper Function ---
def make_api_request(api_key, method, endpoint, files=None, data=None, params=None, attempt=1, max_attempts=3):
    """Helper function to make requests to the TranslateAnyPDF API on RapidAPI with retries for timeouts."""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    log.info(f"Sending {method.upper()} request to {url} (Attempt {attempt}/{max_attempts})")
    if data: log.info(f"Form data: {data}")
    # Avoid logging full file objects for brevity/security in a client script
    if files: log.info(f"Files: {[(k, v[0] if isinstance(v, tuple) else 'file_object') for k,v in files.items()]}") 
    if params: log.info(f"URL Parameters: {params}")

    try:
        # Increased timeout, especially for uploads. 10s connect, 60s read.
        response = requests.request(method, url, headers=headers, files=files, data=data, params=params, timeout=(10, 60))
        log.info(f"Response Status Code: {response.status_code}")
        
        try:
            response_json = response.json()
            log.info(f"Response JSON: {response_json}")
        except ValueError:
            response_json = None
            log.warning(f"Response was not JSON. Response Text: {response.text[:200]}...") # Shorter log

        # Handle specific HTTP errors
        if response.status_code == 401:
            log.error("ERROR: Unauthorized (401). Your RapidAPI Key is invalid or missing.")
            return None, response.status_code
        if response.status_code == 403:
            log.error(f"ERROR: Forbidden (403). You might not have access to this tier/endpoint, or your quota is exceeded. Message: {response_json.get('message') if response_json else response.text[:100]}")
            return response_json, response.status_code
        if response.status_code == 429:
            log.error(f"ERROR: Too Many Requests (429). You have exceeded your rate limit. Message: {response_json.get('message') if response_json else response.text[:100]}")
            return response_json, response.status_code
        if 400 <= response.status_code < 500 and response.status_code not in [401,403,429]: # Other client errors
             log.error(f"ERROR: Client Error ({response.status_code}). Message: {response_json.get('message') if response_json else response.text[:100]}")
             return response_json, response.status_code
        response.raise_for_status() # Raise an exception for 5xx server errors

        return response_json, response.status_code
        
    except requests.exceptions.Timeout as e:
        log.error(f"Request timed out: {e}")
        if attempt < max_attempts:
            log.info(f"Retrying in {5*attempt} seconds...")
            time.sleep(5*attempt)
            return make_api_request(api_key, method, endpoint, files, data, params, attempt + 1, max_attempts)
    except requests.exceptions.ConnectionError as e:
        log.error(f"Connection error occurred: {e}")
    except requests.exceptions.HTTPError as e: # For 5xx errors after raise_for_status
        log.error(f"HTTP Server Error occurred: {e}")
    except requests.exceptions.RequestException as e:
        log.error(f"An unexpected error occurred with the request: {e}")
    return None, None


# --- Main Functions ---
def translate_pdf(api_key: str, pdf_path: Path, target_lang: str, tier: str, output_path: Path):
    """Initiates translation and polls until completion, then downloads the file."""
    log.info(f"--- Starting PDF Translation ---")
    log.info(f"PDF: {pdf_path.name}, Target Language: {target_lang}, Tier: {tier}")

    if not pdf_path.exists():
        log.error(f"Input PDF file {pdf_path} not found.")
        return False

    job_id = None
    
    # 1. Initiate Job
    log.info("Step 1: Initiating Translation Job...")
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        form_data = {'target_lang': target_lang}
        init_response, status_code = make_api_request(api_key, "POST", f"/translate/{tier}", files=files, data=form_data)

    if (status_code == 202 or status_code == 200) and init_response and init_response.get("job_id") and init_response.get("status"):
        job_id = init_response["job_id"]
        log.info(f"Job initiated successfully. Job ID: {job_id}, Status: {init_response.get('status')}")
    else:
        log.error(f"Failed to initiate job. Status: {status_code}, Response: {init_response if init_response else 'No response data'}")
        return False

    # 2. Poll Job Status
    log.info(f"\nStep 2: Polling Job Status for {job_id}...")
    max_polls = 60  # Poll for up to 5 minutes (60 * 5s = 300s)
    poll_interval_seconds = 5 
    download_url = None

    for i in range(max_polls):
        log.info(f"Polling attempt {i+1}/{max_polls}...")
        status_response, poll_status_code = make_api_request(api_key, "GET", f"/status/{job_id}")
        
        if not status_response: # Error already logged by make_api_request
            log.error("Polling failed: Could not get status response.")
            return False 

        current_api_status = status_response.get("status")
        log.info(f"Job {job_id} current status: {current_api_status}")

        if current_api_status == "completed":
            download_url = status_response.get("download_url")
            if not download_url:
                log.error("Job completed but no download URL provided by API!")
                return False
            log.info(f"Job {job_id} COMPLETED. Download URL: {download_url}")
            break
        elif current_api_status in ["error_tier_limit_exceeded", "error_job_not_found", 
                                      "error_missing_estimation_data", "failed", "enqueue_failed"]:
            error_msg = status_response.get('error_message', 'No specific error message provided by API.')
            log.error(f"Job {job_id} ended with status '{current_api_status}'. Error: {error_msg}")
            return False
        
        if i < max_polls - 1:
            log.info(f"Waiting {poll_interval_seconds}s before next poll...")
            time.sleep(poll_interval_seconds)
    else: # Loop finished without break
        log.warning(f"Polling finished after {max_polls} attempts. Job did not complete. Last known status: {current_api_status}")
        return False

    # 3. Download File
    if download_url:
        log.info(f"\nStep 3: Downloading translated file from {download_url}...")
        try:
            # Direct download, no special headers needed for the CDN link usually
            pdf_response = requests.get(download_url, timeout=(10, 120)) # 10s connect, 120s read for potentially large files
            pdf_response.raise_for_status() 

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f_out:
                f_out.write(pdf_response.content)
            log.info(f"Translated PDF successfully downloaded to: {output_path}")
            return True
        except requests.exceptions.Timeout:
            log.error(f"Download timed out from {download_url}.")
        except requests.exceptions.RequestException as e:
            log.error(f"Failed to download translated PDF from {download_url}. Error: {e}")
    else:
        log.error("No download URL was available after job completion, cannot download.")
        
    return False

def analyze_pdf_main(api_key: str, pdf_path: Path):
    """Main function to call the analyze-pdf endpoint."""
    log.info(f"--- Analyzing PDF: {pdf_path.name} ---")
    if not pdf_path.exists():
        log.error(f"Input PDF file {pdf_path} not found.")
        return

    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        response, status_code = make_api_request(api_key, "POST", "/analyze-pdf", files=files)

    if status_code == 200 and response and response.get('success') is True:
        log.info(f"PDF Analysis successful:")
        for key, value in response.items():
            if key != 'success':
                 log.info(f"  {key.replace('_', ' ').capitalize()}: {value}")
    elif response and response.get('success') is False:
         log.error(f"PDF Analysis returned an API error: {response.get('error_code')} - {response.get('message')}")
    elif status_code: # If there was a status_code but not a success response structure
        log.error(f"PDF Analysis failed. Status: {status_code}, Response: {response if response else 'No response data'}")
    # If status_code is None, make_api_request already logged the error

# --- CLI Argument Parser ---
def main_cli():
    parser = argparse.ArgumentParser(description="TranslateAnyPDF API Client - Translate or analyze PDF documents via RapidAPI.")
    parser.add_argument("--api_key", type=str, default=os.getenv("RAPIDAPI_KEY"), help="Your RapidAPI Key. Can also be set via RAPIDAPI_KEY environment variable.")
    
    subparsers = parser.add_subparsers(dest="action", required=True, help="Action to perform")

    # Translate action
    translate_parser = subparsers.add_parser("translate", help="Translate a PDF file.")
    translate_parser.add_argument("pdf_file", type=Path, help="Path to the PDF file to translate.")
    translate_parser.add_argument("target_lang", type=str, help="Target language code (e.g., es, fr, de, uk).")
    translate_parser.add_argument("tier", type=str, choices=['small', 'medium', 'large'], help="Processing tier for the translation.")
    translate_parser.add_argument("--output_file", type=Path, help="Path to save the translated PDF. Defaults to 'translated_TARGETLANG_inputfilename.pdf'.")

    # Analyze action
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a PDF file to get page and character counts.")
    analyze_parser.add_argument("pdf_file", type=Path, help="Path to the PDF file to analyze.")

    args = parser.parse_args()

    if not args.api_key:
        log.error("RapidAPI Key is required. Please provide it via --api_key argument or set the RAPIDAPI_KEY environment variable.")
        return

    if args.action == "translate":
        output_file = args.output_file
        if not output_file:
            # Ensure the default output is in the current working directory or a specific 'output' folder
            default_output_dir = Path.cwd() / "translated_pdfs"
            default_output_dir.mkdir(exist_ok=True)
            output_file = default_output_dir / f"translated_{args.target_lang}_{args.pdf_file.name}"
        
        translate_pdf(args.api_key, args.pdf_file.resolve(), args.target_lang, args.tier, output_file.resolve())
    
    elif args.action == "analyze":
        analyze_pdf_main(args.api_key, args.pdf_file.resolve())

if __name__ == "__main__":
    main_cli()
