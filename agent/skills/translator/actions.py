import sys
import os

# Add current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import translation_api

def translate_to_arabic(text):
    return translation_api.translate(text)

if __name__ == "__main__":
    test_text = "Hello world"
    if len(sys.argv) > 1:
        test_text = sys.argv[1]
    print(translate_to_arabic(test_text))
