
import csv
import html
from pathlib import Path
from urllib.parse import quote

folder = Path("bmi-royalty-statements")

# Columns excluded from public HTML pages.

excluded_columns = {
    "TIMING",
    "PERF COUNT",
    "BONUS LEVEL",
    "ROYALTY AMOUNT",
    "WITHHOLD",
    "CURRENT ACTIVITY AMT",
    "HITS SONG OR TV NET SUPER USAGE BONUS",
    "STANDARDS OR TV NET THEME BONUS",
    "FOREIGN SOCIETY ADJUSTMENT",
    "PERF DATE",
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
<link rel="stylesheet" href="/style.css">
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



# Generate the statement directory, grouped by year.

from collections import defaultdict

years = defaultdict(list)

for csv_file in folder.glob("*.csv"):
    title = csv_file.stem
    year = title.split()[0]
    filename = quote(f"{title}.html")
    years[year].append((title, filename))

directory = []

for year in sorted(years, reverse=True):
    quarters = sorted(years[year], reverse=True)

    directory.append(
        f'<div class="folder">📁 {html.escape(year)}'
        f'<div class="folder-links">'
    )

    for i, (title, filename) in enumerate(quarters):
        branch = "└──" if i == len(quarters) - 1 else "├──"

        directory.append(
            f'<div>{branch} '
            f'<a href="{filename}">{html.escape(title)}</a></div>'
        )

    directory.append("</div></div>")

index_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BMI Royalty Statements | Michael Angelo Garcia (Indijinouz)</title>
<link rel="stylesheet" href="/style.css">
</head>
<body>
<h1>Michael Angelo Garcia (Indijinouz)</h1>
<h2>BMI Royalty Statements</h2>
<div class="directory">
{''.join(directory)}
</div>
</body>
</html>"""

(folder / "index.html").write_text(index_page, encoding="utf-8")
