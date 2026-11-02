from langchain.tools import tool 
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os 
from dotenv import load_dotenv
from rich import print
load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def web_search(query : str) -> str:
    """Search the web for recent and reliable information on a topic . Returns Titles , URLs and snippets."""
    results = tavily.search(query=query,max_results=5)

    out = []
 
    for r in results['results']:
        out.append(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}\n"
        )
    
    return "\n----\n".join(out)


@tool
def scrape_url(url: str) -> str:
    """Scrape clean text from a webpage URL for deeper research."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(
            url,
            timeout=15,
            headers=headers,
            allow_redirects=True
        )

        # Stop if the website returns an HTTP error
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove unnecessary page elements
        for tag in soup([
            "script", "style", "nav", "footer",
            "header", "aside", "form"
        ]):
            tag.decompose()

        # Try to extract the main article first
        article = soup.find("article")

        if article:
            text = article.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)

        if not text:
            return f"No readable text found at: {url}"

        return f"Source URL: {response.url}\n\n{text[:5000]}"

    except requests.RequestException as e:
        return f"Scraping failed for {url}: {type(e).__name__}: {e}"
    except Exception as e:
        return f"Unexpected scraping error: {type(e).__name__}: {e}"
