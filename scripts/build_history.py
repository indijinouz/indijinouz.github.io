
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
        f'<details class="country" data-count="{country_count}" '
        f'data-name="{esc(country)}"><summary>{esc(country)}'
        f'<span class="count">{country_count:,} records</span></summary>'
    )

    for show, episodes in sorted(shows.items()):
        show_count = sum(len(rows) for rows in episodes.values())

        parts.append(
            f'<details class="show" data-count="{show_count}" '
            f'data-name="{esc(show)}"><summary>{esc(show)}'
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

h1 {
  font-size: 30px;
  margin-bottom: 4px;
}

.subtitle {
  color: gray;
  margin-bottom: 24px;
}

/* Sorting controls */

.sort-controls {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 28px;
}

.sort-controls label {
  font-size: 13px;
  color: #77808b;
}

.sort-controls select {
  margin-left: 7px;
  padding: 7px 10px;
  border: 1px solid #d5d9df;
  border-radius: 8px;
  background: #f8f9fa;
  color: #303846;
  font: inherit;
  cursor: pointer;
}

/* Collapsible sections */

details {
  margin: 8px 0;
}

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

.show {
  margin-left: 22px;
}

.show > summary {
  background: #f2f4f7;
  color: #303846;
}

.episode {
  margin-left: 22px;
}

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

/* Records table */

.table-wrap {
  overflow-x: auto;
  margin: 12px 0 20px 22px;
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

th {
  background: #f3f4f6;
  color: #333;
}

tr:nth-child(even) {
  background: #fafafa;
}

/* Dark mode */

@media (prefers-color-scheme: dark) {
  body {
    background: #16181c;
    color: #f1f2f4;
  }

  .country > summary {
    background: #3a4452;
    color: #f1f2f4;
  }

  .show > summary {
    background: #2a3544;
    color: #eceef1;
  }

  .episode > summary {
    background: #1a2433;
    color: #eceef1;
  }

  .sort-controls select {
    background: #292e36;
    border-color: #414650;
    color: #f1f2f4;
  }

  /* Table colors coordinated with the episode palette */

  .table-wrap {
    background: #141e2d;
    border-color: #344355;
  }

  th {
    background: #29374a;
    color: #f0f3f8;
    border-color: #344355;
  }

  td {
    background: #141e2d;
    color: #f0f3f8;
    border-color: #344355;
  }

  tr:nth-child(even) td {
    background: #202c3d;
  }
}
</style>
</head>

<body>

<h1>BMI Royalty History</h1>
<p class="subtitle">Michael Angelo Garcia (Indijinouz) · RECORD_COUNT records</p>

<div class="sort-controls">

  <label for="country-sort">
    Countries:
    <select id="country-sort">
      <option value="alpha">Alphabetical</option>
      <option value="count">Most Records</option>
    </select>
  </label>

  <label for="show-sort">
    Shows:
    <select id="show-sort">
      <option value="alpha">Alphabetical</option>
      <option value="count">Most Records</option>
    </select>
  </label>

</div>

CONTENT

<script>
const countrySort = document.getElementById("country-sort");
const showSort = document.getElementById("show-sort");

function sortSections(parent, selector, mode) {
  const sections = Array.from(parent.children)
    .filter(el => el.matches(selector));

  sections.sort((a, b) => {
    if (mode === "count") {
      const difference =
        Number(b.dataset.count) - Number(a.dataset.count);

      if (difference !== 0) return difference;
    }

    return a.dataset.name.localeCompare(
      b.dataset.name,
      undefined,
      { sensitivity: "base" }
    );
  });

  sections.forEach(section => parent.appendChild(section));
}

function updateSorting() {
  sortSections(
    document.body,
    "details.country",
    countrySort.value
  );

  document.querySelectorAll("details.country").forEach(country => {
    sortSections(
      country,
      "details.show",
      showSort.value
    );
  });
}

countrySort.addEventListener("change", updateSorting);
showSort.addEventListener("change", updateSorting);

/* Option-click (Mac) / Alt-click (Windows):
   Collapse every section of the clicked level, globally.
   Normal clicks toggle only the clicked section. */

document.addEventListener("click", event => {
  if (!event.altKey) return;

  const summary = event.target.closest("summary");
  if (!summary) return;

  const section = summary.parentElement;
  if (!section.matches("details")) return;

  event.preventDefault();

  let sections;

  if (section.classList.contains("country")) {
    // Collapse all countries.
    sections = document.querySelectorAll("details.country");

  } else if (section.classList.contains("show")) {
    // Collapse all shows across every country.
    sections = document.querySelectorAll("details.show");

  } else if (section.classList.contains("episode")) {
    // Collapse all episodes across every show and country.
    sections = document.querySelectorAll("details.episode");

  } else {
    return;
  }

  sections.forEach(item => {
    item.open = false;
  });
});

</script>

</body>
</html>"""

page = page.replace("RECORD_COUNT", f"{total:,}")
page = page.replace("CONTENT", "\n".join(parts))

output.write_text(page, encoding="utf-8")

print(f"Created {output} with {total:,} records.")
