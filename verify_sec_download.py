import os
from app.services.sec_service import SECService

def verify_download():
    # Use MSFT as a test case
    ticker = "MSFT"
    year = 2023
    
    print(f"--- Testing Downloader for {ticker} {year} ---")
    service = SECService()
    
    # 1. Download
    print("1. Downloading...")
    html_path = service.download_10k(ticker, year)
    
    if html_path and os.path.exists(html_path):
        print(f"SUCCESS: Downloaded to {html_path}")
    else:
        print("FAIL: Download failed.")
        return

    # 2. Parse
    print("\n2. Parsing...")
    text = service.clean_text(html_path)
    
    if len(text) > 1000:
        print(f"SUCCESS: Extracted {len(text)} chars of text.")
        print(f"Preview: {text[:500]}...")
    else:
        print(f"FAIL: Text extraction looks too short ({len(text)} chars).")

if __name__ == "__main__":
    verify_download()
