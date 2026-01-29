import os
import glob
import re
from sec_edgar_downloader import Downloader

from bs4 import BeautifulSoup

class SECService:
    def __init__(self, download_dir: str = "sec_downloads"):
        self.download_dir = download_dir
        # In a real app, load from env or config. 
        # SEC requires Company Name and Email separately for v5
        self.company = os.getenv("SEC_COMPANY", "SEC Agent RAG")
        self.email = os.getenv("SEC_EMAIL", "admin@secagentrag.com")
        self.dl = Downloader(self.company, self.email, self.download_dir)

    def download_10k(self, ticker: str, year: int) -> str | None:
        """
        Downloads 10-K filings and returns the specific one matching the requested fiscal year.
        """
        try:
            print(f"Downloading 10-K for {ticker}...")
            # Download a few to ensure we get the right one
            self.dl.get("10-K", ticker, limit=5)
            
            search_pattern = os.path.join(self.download_dir, "sec-edgar-filings", ticker, "10-K", "*", "*.txt")
            files = glob.glob(search_pattern)
            
            for file_path in files:
                metadata = self.get_filing_metadata(file_path)
                if metadata.get("fiscal_year") == year:
                    print(f"Found matching filing for {year}: {file_path}")
                    return file_path
            
            print(f"No filing found with CONFORMED PERIOD OF REPORT matching {year}.")
            return None
                
        except Exception as e:
            print(f"Error downloading 10-K: {e}")
            return None

    def get_filing_metadata(self, file_path: str) -> dict:
        """
        Parses the SEC SGML header to extract metadata.
        """
        metadata = {}
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # We only need the first few thousand characters for the header
                header_text = f.read(10000)
                
                # Extract CONFORMED PERIOD OF REPORT: 20231231
                period_match = re.search(r'CONFORMED PERIOD OF REPORT:\s+(\d{4})\d{4}', header_text)
                if period_match:
                    metadata["fiscal_year"] = int(period_match.group(1))
                
                # Extract FORM TYPE
                type_match = re.search(r'CONFORMED SUBMISSION TYPE:\s+(.*)', header_text)
                if type_match:
                    metadata["form_type"] = type_match.group(1).strip()
        except Exception as e:
            print(f"Error parsing metadata for {file_path}: {e}")
            
        return metadata


    def clean_text(self, html_path: str) -> str:
        """
        Parses the HTML and returns clean text.
        """
        if not os.path.exists(html_path):
            raise FileNotFoundError(f"File not found: {html_path}")

        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Handle SGML full-submission.txt
        if "full-submission.txt" in html_path:
            content = self._extract_10k_html(content)
            
        soup = BeautifulSoup(content, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Get text
        text = soup.get_text(separator="\n\n")

        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    def _extract_10k_html(self, sgml_content: str) -> str:
        """
        Extracts the HTML content of the 10-K document from the SGML dump.
        """
        # Simple string search - in production use a regex or iterator for memory efficiency
        # We look for <TYPE>10-K ... <TEXT> ... </TEXT>
        # Note: Sometimes it's <TYPE>10-K/A
        
        import re
        # Find the start of the 10-K document
        # <DOCUMENT> -> <TYPE>10-K -> ... <TEXT>
        
        doc_start_pattern = re.compile(r'<DOCUMENT>')
        doc_end_pattern = re.compile(r'</DOCUMENT>')
        
        type_pattern = re.compile(r'<TYPE>10-K')
        
        # Split by document seems safer but memory intensive. 
        # Let's simple split by <DOCUMENT>
        documents = sgml_content.split('<DOCUMENT>')
        
        for doc in documents:
            if "<TYPE>10-K" in doc or "<TYPE>10-K/A" in doc:
                # Extract text between <TEXT> and </TEXT>
                start = doc.find('<TEXT>')
                end = doc.find('</TEXT>')
                if start != -1 and end != -1:
                    return doc[start+6:end]
                    
        # Fallback: just return the whole thing if we can't find specific 10-K section, 
        # but warn or maybe return first large chunk
        return sgml_content

