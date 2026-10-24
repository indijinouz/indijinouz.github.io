
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

base_url = "https://indijinouz.github.io"

# Automatically discover all HTML pages.
pages = []

for file in Path(".").rglob("*.html"):
    # Exclude Google's verification files.
    if file.name.startswith("google") and file.parent == Path("."):
        continue

    # Exclude hidden folders and development files.
    if any(part.startswith(".") for part in file.parts):
        continue

    # Convert file paths into website URLs.
    if file.name == "index.html":
        if file.parent == Path("."):
            url = "/"
        else:
            url = "/" + "/".join(
                quote(part) for part in file.parent.parts
            ) + "/"
    else:
        url = "/" + "/".join(
            quote(part) for part in file.parts
        )

    pages.append(url)

# Sort URLs for a consistent sitemap.
pages.sort()

# Generate sitemap.xml.
urlset = ET.Element(
    "urlset",
    xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
)

for page in pages:
    url = ET.SubElement(urlset, "url")
    ET.SubElement(url, "loc").text = base_url + page

tree = ET.ElementTree(urlset)
ET.indent(tree, space="  ")

tree.write(
    "sitemap.xml",
    encoding="utf-8",
    xml_declaration=True
)

print(f"Created sitemap.xml with {len(pages)} URLs.")
