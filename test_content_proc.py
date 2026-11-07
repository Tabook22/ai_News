
import sys
import os
# Add project root to path
sys.path.append(os.getcwd())

from app.app import process_content_images

sample_html = """
<p>This is some test content.</p>
<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNiAAAABgADNjd8qAAAAABJRU5ErkJggg==" />
<p>More text after image.</p>
"""

print("Original:")
print(sample_html)
print("-" * 20)
try:
    processed = process_content_images(sample_html)
    print("Processed:")
    print(processed)
except Exception as e:
    print(f"Error: {e}")
