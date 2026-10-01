import os
import re
import html
import requests
from pathlib import Path
from datetime import datetime


WP_BASE_URL = os.environ["WP_BASE_URL"]
POSTS_DIR = Path("content/posts")

POSTS_DIR.mkdir(parents=True, exist_ok=True)


def strip_wp_classes(value):
    value = re.sub(r'\sclass="[^"]*"', '', value)
    value = re.sub(r'\sstyle="[^"]*"', '', value)
    value = re.sub(r'\sdata-[a-zA-Z0-9_-]+="[^"]*"', '', value)
    return value


def html_to_markdown(content):
    content = html.unescape(content)

    # Images
    content = re.sub(
        r'<figure[^>]*>\s*<img[^>]+src="([^"]+)"[^>]*/?>\s*</figure>',
        r'![WordPress image](\1)',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )

    content = re.sub(
        r'<img[^>]+src="([^"]+)"[^>]*/?>',
        r'![WordPress image](\1)',
        content,
        flags=re.IGNORECASE
    )

    # Paragraphs
    content = re.sub(
        r'<p[^>]*>(.*?)</p>',
        r'\1\n\n',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Headings
    for level in range(6, 0, -1):
        content = re.sub(
            rf'<h{level}[^>]*>(.*?)</h{level}>',
            lambda m: '#' * level + ' ' + m.group(1).strip() + '\n\n',
            content,
            flags=re.IGNORECASE | re.DOTALL
        )

    # Links
    content = re.sub(
        r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        r'[\2](\1)',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Bold / italic
    content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**',
                     content, flags=re.IGNORECASE | re.DOTALL)

    content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*',
                     content, flags=re.IGNORECASE | re.DOTALL)

    # Lists
    content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n',
                     content, flags=re.IGNORECASE | re.DOTALL)

    content = re.sub(r'</?(ul|ol)[^>]*>', '\n',
                     content, flags=re.IGNORECASE)

    # Remove remaining WordPress HTML tags
    content = re.sub(r'<[^>]+>', '', content)

    # Clean WP classes that may remain
    content = strip_wp_classes(content)

    # Normalize whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.strip()


def yaml_quote(value):
    value = str(value).replace('\\', '\\\\').replace('"', '\\"')
    return f'"{value}"'


def convert_post(post):
    post_id = post["id"]
    title = post["title"]["rendered"]
    slug = post["slug"]

    date = post["date"]

    try:
        parsed_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
        date = parsed_date.strftime("%Y-%m-%d")
    except Exception:
        date = date[:10]

    content = html_to_markdown(post["content"]["rendered"])

    filename = POSTS_DIR / f"wp-{post_id}.md"

    frontmatter = f"""---
title: {yaml_quote(title)}
date: {date}
slug: {yaml_quote(slug)}
draft: false
wordpress_id: {post_id}
---

"""

    filename.write_text(
        frontmatter + content + "\n",
        encoding="utf-8"
    )

    print(f"Synced WordPress post {post_id}: {title}")


def main():
    page = 1
    total = 0

    while True:
        url = f"{WP_BASE_URL}/wp-json/wp/v2/posts"

        response = requests.get(
            url,
            params={
                "status": "publish",
                "per_page": 100,
                "page": page
            },
            timeout=30
        )

        response.raise_for_status()

        posts = response.json()

        if not posts:
            break

        for post in posts:
            convert_post(post)
            total += 1

        total_pages = int(response.headers.get("X-WP-TotalPages", page))

        if page >= total_pages:
            break

        page += 1

    print(f"WordPress synchronization completed: {total} posts")


if __name__ == "__main__":
    main()