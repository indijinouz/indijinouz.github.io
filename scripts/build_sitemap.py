from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

BASE_URL = "https://indijinouz.github.io"
SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
SITEMAP_OUTPUT = Path("sitemap.xml")
ROBOTS_OUTPUT = Path("robots.txt")

ET.register_namespace("", SITEMAP_NAMESPACE)

# Automatically discover all HTML pages.

pages = set()

for file in Path(".").rglob("*.html"):
    # Exclude Google's verification file.

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

    pages.add(url)

# Sort URLs for a consistent sitemap.

pages = sorted(pages)

# Generate sitemap.xml.

urlset = ET.Element(
    ET.QName(SITEMAP_NAMESPACE, "urlset")
)

for page in pages:
    url = ET.SubElement(
        urlset,
        ET.QName(SITEMAP_NAMESPACE, "url")
    )

    ET.SubElement(
        url,
        ET.QName(SITEMAP_NAMESPACE, "loc")
    ).text = BASE_URL + page

tree = ET.ElementTree(urlset)
ET.indent(tree, space="  ")

tree.write(
    SITEMAP_OUTPUT,
    encoding="utf-8",
    xml_declaration=True
)

# Validate the sitemap before GitHub Actions commits it.

if not SITEMAP_OUTPUT.read_bytes().startswith(b"<?xml "):
    raise ValueError(
        "sitemap.xml is missing its XML declaration."
    )

parsed_root = ET.parse(SITEMAP_OUTPUT).getroot()
expected_root = f"{{{SITEMAP_NAMESPACE}}}urlset"

if parsed_root.tag != expected_root:
    raise ValueError(
        "sitemap.xml has an invalid sitemap namespace."
    )

locations = [
    element.text or ""
    for element in parsed_root.findall(
        f"{{{SITEMAP_NAMESPACE}}}url/"
        f"{{{SITEMAP_NAMESPACE}}}loc"
    )
]

expected_locations = [
    BASE_URL + page
    for page in pages
]

if locations != expected_locations:
    raise ValueError(
        "sitemap.xml contains missing, duplicate, or invalid URLs."
    )

if any(
    not location.startswith(BASE_URL + "/")
    for location in locations
):
    raise ValueError(
        "sitemap.xml contains a URL from the wrong domain."
    )

# Generate robots.txt and identify the sitemap for search engines.

ROBOTS_OUTPUT.write_text(
    "User-agent: *\n"
    "Allow: /\n\n"
    f"Sitemap: {BASE_URL}/sitemap.xml\n",
    encoding="utf-8"
)

print(
    f"Created {SITEMAP_OUTPUT} with {len(pages)} URLs "
    f"and updated {ROBOTS_OUTPUT}."
)
