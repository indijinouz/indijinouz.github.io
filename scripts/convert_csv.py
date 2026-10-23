
import csv
import html
from pathlib import Path

folder = Path("bmi-royalty-statements")

for csv_file in sorted(folder.glob("*.csv")):
    with csv_file.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        continue

    title = csv_file.stem
    headers = rows[0]

    table = ["<table border='1'>"]
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
<title>Michael Angelo Garcia (Indijinouz) - BMI {title}</title>
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
