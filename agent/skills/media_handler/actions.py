import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import image_extractor

def get_image(url):
    return image_extractor.extract_og_image(url)

if __name__ == "__main__":
    test_url = "https://www.google.com"
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    print(get_image(test_url))
