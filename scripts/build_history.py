
import csv
import html
from pathlib import Path
from collections import defaultdict

source = Path("bmi-royalty-statements")
output = Path("bmi-royalty-history.html")

data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
all_headers = []
total = 0

for file in sorted(source.glob("*.csv")):
    with file.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            continue

        for header in reader.fieldnames:
            if header and header not in all_headers:
                all_headers.append(header)

        for row in reader:
            if not any(row.values()):
                continue

            country = row.get("COUNTRY OF PERFORMANCE") or "Unknown"
            show = row.get("SHOW NAME") or "Unspecified"
            episode = row.get("EPISODE NAME") or "Unspecified"

            data[country][show][episode].append(row)
            total += 1

def esc(value):
    return html.escape(str(value or ""), quote=True)

parts = []

for country, shows in sorted(data.items()):
    country_count = sum(
        len(rows)
        for episodes in shows.values()
        for rows in episodes.values()
    )

    parts.append(
        f'<details class="country"><summary>{esc(country)}'
        f'<span class="count">{country_count:,} records</span></summary>'
    )

    for show, episodes in sorted(shows.items()):
        show_count = sum(len(rows) for rows in episodes.values())

        parts.append(
            f'<details class="show"><summary>{esc(show)}'
            f'<span class="count">{show_count:,}</span></summary>'
        )

        for episode, rows in sorted(episodes.items()):
            parts.append(
                f'<details class="episode"><summary>{esc(episode)}'
                f'<span class="count">{len(rows):,}</span></summary>'
            )

            parts.append('<div class="table-wrap"><table><thead><tr>')

            for header in all_headers:
                parts.append(f'<th>{esc(header)}</th>')

            parts.append('</tr></thead><tbody>')

            for row in rows:
                parts.append('<tr>')
                for header in all_headers:
                    parts.append(f'<td>{esc(row.get(header))}</td>')
                parts.append('</tr>')

            parts.append('</tbody></table></div></details>')

        parts.append('</details>')

    parts.append('</details>')

page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BMI Royalty History | Michael Angelo Garcia (Indijinouz)</title>
<style>
:root {
  color-scheme: light dark;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
body {
  max-width: 1200px;
  margin: 50px auto;
  padding: 0 24px;
  line-height: 1.5;
}
h1 { font-size: 30px; margin-bottom: 4px; }
.subtitle { color: gray; margin-bottom: 32px; }
details { margin: 8px 0; }
summary {
  cursor: pointer;
  padding: 13px 16px;
  border-radius: 10px;
  display: list-item;
  font-weight: 500;
}
.country > summary {
  background: #e9edf2;
  color: #18212d;
  font-weight: 650;
}
.show { margin-left: 22px; }
.show > summary {
  background: #f2f4f7;
  color: #303846;
}
.episode { margin-left: 22px; }
.episode > summary {
  background: #f8f9fa;
  color: #414b59;
}
.count {
  float: right;
  font-size: 12px;
  color: #77808b;
  font-weight: 400;
}
.table-wrap {
  overflow-x: auto;
  margin: 12px 0 20px;
  border: 1px solid #ddd;
  border-radius: 10px;
}
table {
  border-collapse: collapse;
  width: 100%;
  font-size: 12px;
}
th, td {
  padding: 9px 12px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}
th { background: #f3f4f6; color: #333; }
tr:nth-child(even) { background: #fafafa; }
@media (prefers-color-scheme: dark) {
  body { background: #16181c; color: #f1f2f4; }
  .country > summary { background: #292e36; color: #f1f2f4; }
  .show > summary { background: #23272e; color: #eceef1; }
  .episode > summary { background: #1d2026; color: #eceef1; }
  .table-wrap { border-color: #383b42; }
  th { background: #292d34; color: #eee; }
  td { border-color: #363940; }
  tr:nth-child(even) { background: #1e2229; }
}
</style>
</head>
<body>
<h1>BMI Royalty History</h1>
<p class="subtitle">Michael Angelo Garcia (Indijinouz) · RECORD_COUNT records</p>
CONTENT
</body>
</html>"""

page = page.replace("RECORD_COUNT", f"{total:,}")
page = page.replace("CONTENT", "\n".join(parts))

output.write_text(page, encoding="utf-8")
print(f"Created {output} with {total:,} records.")
