
import csv
import html
from pathlib import Path
from urllib.parse import quote

folder = Path("bmi-royalty-statements")

# Shared styling for royalty tables and index page.
# Matches the BMI Works Catalog.

style = """
<style>
body { font-family: Arial, sans-serif; margin: 30px; }
table { border-collapse: collapse; font-size: 13px; }
th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
th { background: #eee; }
tr:nth-child(even) { background: #f8f8f8; }
</style>
"""

# Generate an HTML table for every quarterly CSV.

for csv_file in sorted(folder.glob("*.csv")):
    with csv_file.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        continue

    title = csv_file.stem
    headers = rows[0]

    table = ["<table>"]
    table.append("<thead><tr>")

    for header in headers:
        table.append(f"<th>{html.escape(header)}</th>")

    table.append("</tr></thead><tbody>")

    for row in rows[1:]:
        table.append("<tr>")

        for value in row:
            table.append(f"<td>{html.escape(value)}</td>")

        table.append("</tr>")

    table.append("</tbody></table>")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Michael Angelo Garcia (Indijinouz) - BMI {html.escape(title)}</title>
{style}
</head>
<body>
<h1>Michael Angelo Garcia (Indijinouz)</h1>
<h2>BMI Royalty Statements - {html.escape(title)}</h2>
{''.join(table)}
</body>
</html>"""

    output = folder / f"{title}.html"
    output.write_text(page, encoding="utf-8")

print("HTML tables generated successfully.")

# Generate the index page listing all quarters, newest first.

links = []

for csv_file in sorted(folder.glob("*.csv"), reverse=True):
    title = csv_file.stem
    filename = quote(f"{title}.html")

    links.append(
        f'<li><a href="{filename}">{html.escape(title)}</a></li>'
    )

index_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BMI Royalty Statements | Michael Angelo Garcia (Indijinouz)</title>
{style}
</head>
<body>
<h1>BMI Royalty Statements</h1>
<ul>
{''.join(links)}
</ul>
</body>
</html>"""

(folder / "index.html").write_text(index_page, encoding="utf-8")
