import arxiv
import re
from io import BytesIO
import requests
import PyPDF2

def request_arxiv_pdf_chunks(arxiv_url, chunk_size=4000, overlap=250, max_size=10*1024*1024): # 10 MB limit
    """Takes in an entire URL returned from get_arxiv_articles, then outputs the text in chunks, and outputs the arxiv_url"""

    arxiv_id = re.search(r'arxiv\.org/abs/(.+)', arxiv_url).group(1)
    pdf_url = f'http://arxiv.org/pdf/{arxiv_id}.pdf'

    # Check the size of the PDF
    head = requests.head(pdf_url)
    if int(head.headers.get('Content-Length', 0)) > max_size:
        return "Error: PDF is too large to download"

    # Stream the download
    try:
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code

        # Read the PDF content
        pdf_content = BytesIO()
        for chunk in response.iter_content(chunk_size):
            pdf_content.write(chunk)

        # Initialize a PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_content)
        # Extract text from each page
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()

        # Split the text into chunks
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - overlap)]

        return chunks, arxiv_url

    except requests.HTTPError as e:
        return f"HTTP Error: {e}"
    except requests.RequestException as e:
        return f"Request Exception: {e}"


def get_arxiv_articles(keywords):
    """Use Python arxiv package to get the top 10 articles by relevance"""
    
    client = arxiv.Client()
    search = arxiv.Search(
        query=keywords,
        max_results=10
    )

    links = []
    for r in list(client.results(search)):
        links.append(r.entry_id)

    return links