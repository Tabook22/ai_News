import requests
from bs4 import BeautifulSoup

def extract_meta_image(url):
    """
    Fetches the URL and extracts the og:image meta tag content.
    Returns the image URL or None.
    """
    if not url:
        return None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try og:image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
            
        # Try twitter:image
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content']
            
        return None
        
    except Exception as e:
        print(f"Error extracting meta image from {url}: {e}")
        return None
