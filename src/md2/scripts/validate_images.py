#!/usr/bin/env python3
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path


def extract_image_urls(markdown_content: str) -> list[str]:
    pattern = r'!\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)'
    urls = re.findall(pattern, markdown_content)
    return [url.strip() for url in urls if url.startswith(("http://", "https://"))]


def validate_remote_image(url: str, timeout: int = 10) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'md2-image-validator/1.0')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content_type = response.headers.get('content-type', '').lower()
            
            if response.status != 200:
                return False, f"HTTP {response.status}"
            
            if not content_type.startswith('image/'):
                return False, f"Not an image (content-type: {content_type})"
            
            return True, "OK"
    
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return False, f"URL error: {e.reason}"
    except Exception as e:
        return False, f"Request failed: {str(e)}"


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_images.py <markdown_file>", file=sys.stderr)
        sys.exit(1)
    
    markdown_file = Path(sys.argv[1])
    if not markdown_file.exists():
        print(f"File not found: {markdown_file}", file=sys.stderr)
        sys.exit(1)
    
    content = markdown_file.read_text(encoding='utf-8')
    urls = extract_image_urls(content)
    
    invalid_images = []
    for url in urls:
        is_valid, message = validate_remote_image(url)
        if not is_valid:
            invalid_images.append((url, message))
    
    if invalid_images:
        print(f"WARNING: Found {len(invalid_images)} inaccessible remote image(s) in {markdown_file.name}:", file=sys.stderr)
        for url, msg in invalid_images:
            print(f"  - {url}: {msg}", file=sys.stderr)
        print("  These images may not render correctly in the output.", file=sys.stderr)


if __name__ == "__main__":
    main()