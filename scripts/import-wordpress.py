import json
import os
import urllib.request
from pathlib import Path

wordpress_url = os.environ["WORDPRESS_URL"].rstrip("/")

api_url = (
    f"{wordpress_url}/wp-json/wp/v2/posts"
    "?per_page=100&status=publish"
)

print(f"Fetching: {api_url}")

with urllib.request.urlopen(api_url, timeout=30) as response:
    posts = json.load(response)

output_dir = Path("hugo/content/posts")
output_dir.mkdir(parents=True, exist_ok=True)

# Remove previously imported WordPress posts.
for file in output_dir.glob("wp-*.md"):
    file.unlink()

for post in posts:
    post_id = post["id"]
    title = post["title"]["rendered"]
    slug = post["slug"]
    date = post["date"][:10]
    content = post["content"]["rendered"]

    markdown = f"""---
title: {json.dumps(title)}
date: {date}
slug: {json.dumps(slug)}
draft: false
---

{content}
"""

    output_file = output_dir / f"wp-{post_id}.md"
    output_file.write_text(markdown, encoding="utf-8")

    print(f"Imported: {title} -> {output_file}")

print(f"Imported {len(posts)} published WordPress posts.")
