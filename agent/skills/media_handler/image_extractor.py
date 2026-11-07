import requests
from bs4 import BeautifulSoup

def extract_og_image(url):
    try:
        if not url:
            return ""
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return ""
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        og_image = soup.find("meta", property="og:image")
        
        if og_image and og_image.get("content"):
            return og_image["content"]
            
        return ""
    except:
        return ""
