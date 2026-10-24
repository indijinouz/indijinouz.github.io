
import csv
import html
from pathlib import Path

folder = Path("bmi-works-catalog")
source = folder / "CatalogExport_1079244.csv"
output = folder / "index.html"

def esc(value):
    return html.escape(str(value or ""), quote=True)

with source.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f)
    rows = list(reader)

if not rows:
    raise ValueError("The Works Catalog CSV is empty.")

headers = rows[0]
records = rows[1:]

parts = [
    "<!DOCTYPE html>",
    '<html lang="en">',
    "<head>",
    '<meta charset="UTF-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    "<title>BMIT Works Catalog | Michael Angelo Garcia (Indijinouz)</title>",
    "<style>",
    "body { font-family: Arial, sans-serif; margin: 30px; }",
    "table { border-collapse: collapse; font-size: 13px; }",
    "th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }",
    "th { background: #eee; }",
    "tr:nth-child(even) { background: #f8f8f8; }",
    "</style>",
    "</head>",
    "<body>",
    "<h1>Michael Angelo Garcia (Indijinouz)</h1>",
    "<h2>BMI Works Catalog</h2>",
    f"<p>{len(records):,} records</p>",
    "<table>",
    "<thead><tr>",
]

for header in headers:
    parts.append(f"<th>{esc(header)}</th>")

parts.append("</tr></thead><tbody>")

for row in records:
    parts.append("<tr>")
    for cell in row:
        parts.append(f"<td>{esc(cell)}</td>")
    parts.append("</tr>")

parts.extend([
    "</tbody></table>",
    "</body>",
    "</html>",
])

output.write_text("\n".join(parts), encoding="utf-8")

print(f"Created {output} with {len(records):,} records.")
