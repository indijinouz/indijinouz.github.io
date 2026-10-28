import csv
import html
from pathlib import Path
from urllib.parse import quote

folder = Path("bmi-royalty-statements")

# Columns excluded from public HTML pages.

excluded_columns = {
    "ROYALTY AMOUNT",
    "WITHHOLD",
    "CURRENT ACTIVITY AMT",
    "HITS SONG OR TV NET SUPER USAGE BONUS",
    "STANDARDS OR TV NET THEME BONUS",
    "FOREIGN SOCIETY ADJUSTMENT",
}

# Generate an HTML table for every quarterly CSV.

for csv_file in sorted(folder.glob("*.csv")):
    with csv_file.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        continue

    title = csv_file.stem

    # Keep only named, non-excluded columns.
    keep_columns = [
        i for i, header in enumerate(rows[0])
        if header.strip()
        and header.strip().upper() not in excluded_columns
    ]

    headers = [rows[0][i] for i in keep_columns]

    table = ["<table>"]
    table.append("<thead><tr>")

    for header in headers:
        table.append(f"<th>{html.escape(header)}</th>")

    table.append("</tr></thead><tbody>")

    for row in rows[1:]:
        table.append("<tr>")

        for i in keep_columns:
            value = row[i] if i < len(row) else ""
            table.append(f"<td>{html.escape(value)}</td>")

        table.append("</tr>")

    table.append("</tbody></table>")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BMI {html.escape(title)} | Michael Angelo Garcia (Indijinouz)</title>
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


# Generate a plain list of quarterly statements.

statement_links = []

for csv_file in sorted(folder.glob("*.csv"), reverse=True):
    title = csv_file.stem
    filename = quote(f"{title}.html")

    statement_links.append(
        f'<li><a href="{filename}">{html.escape(title)}</a></li>'
    )

statement_list = "\n".join(statement_links)

index_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BMI Royalty Statements | Michael Angelo Garcia (Indijinouz)</title>
</head>
<body>
<h1>Michael Angelo Garcia (Indijinouz)</h1>
<h2>BMI Royalty Statements</h2>
<ul>
{statement_list}
</ul>
</body>
</html>"""

(folder / "index.html").write_text(index_page, encoding="utf-8")
