
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

            parts.append(
                '<div class="table-wrap"><table><thead><tr>'
            )

            for header in all_headers:
                parts.append(f'<th>{esc(header)}</th>')

            parts.append('</tr></thead><tbody>')

            for row in rows:
                parts.append('<tr>')

                for header in all_headers:
                    parts.append(
                        f'<td>{esc(row.get(header))}</td>'
                    )

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

  /* Default blue palette */

  --country-bg: #3a4452;
  --show-bg: #2a3544;
  --episode-bg: #1a2433;

  --table-header: #29374a;
  --table-row: #141e2d;
  --table-alt: #202c3d;
  --table-border: #344355;
}

* {
  box-sizing: border-box;
}

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
  margin-bottom: 20px;
  align-items: center;
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

/* Appearance menu */

.appearance {
  margin-bottom: 28px;
  max-width: 360px;
}

.appearance > summary {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 0;
  background: transparent;
  color: #77808b;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  list-style: none;
}

.appearance > summary::-webkit-details-marker {
  display: none;
}

.appearance > summary::before {
  content: "▸";
  display: inline-block;
  transition: transform 0.15s;
}

.appearance[open] > summary::before {
  transform: rotate(90deg);
}

.appearance-panel {
  padding: 16px;
  margin-top: 5px;
  border: 1px solid #d5d9df;
  border-radius: 12px;
  background: #f8f9fa;
}

.appearance-heading {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 12px;
}

.hue-slider {
  display: block;
  width: 100%;
  margin: 0 0 10px;
  cursor: pointer;
  accent-color: #6697d8;
}

.hue-spectrum {
  height: 8px;
  border-radius: 20px;
  background: linear-gradient(
    to right,
    #f44,
    #ff0,
    #0e5,
    #0cf,
    #55f,
    #f0f,
    #f44
  );
}

.palette-preview {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.palette-preview span {
  flex: 1;
  height: 24px;
  border-radius: 6px;
  border: 1px solid #ffffff22;
}

.swatch-country {
  background: var(--country-bg);
}

.swatch-show {
  background: var(--show-bg);
}

.swatch-episode {
  background: var(--episode-bg);
}

.appearance-note {
  font-size: 11px;
  color: #77808b;
  margin: 12px 0 0;
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
    background: var(--country-bg);
    color: #f1f2f4;
  }

  .show > summary {
    background: var(--show-bg);
    color: #eceef1;
  }

  .episode > summary {
    background: var(--episode-bg);
    color: #eceef1;
  }

  .sort-controls select {
    background: #292e36;
    border-color: #414650;
    color: #f1f2f4;
  }

  .appearance-panel {
    background: #20242b;
    border-color: #414650;
  }

  .appearance > summary {
    color: #a9b4c4;
  }

  .table-wrap {
    background: var(--table-row);
    border-color: var(--table-border);
  }

  th {
    background: var(--table-header);
    color: #f0f3f8;
    border-color: var(--table-border);
  }

  td {
    background: var(--table-row);
    color: #f0f3f8;
    border-color: var(--table-border);
  }

  tr:nth-child(even) td {
    background: var(--table-alt);
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

<details class="appearance">
  <summary>Appearance</summary>

  <div class="appearance-panel">
    <div class="appearance-heading">Color theme</div>

    <input
      type="range"
      id="hue-slider"
      class="hue-slider"
      min="0"
      max="360"
      value="214"
      aria-label="Color theme hue"
    >

    <div class="hue-spectrum"></div>

    <div class="palette-preview">
      <span class="swatch-country"></span>
      <span class="swatch-show"></span>
      <span class="swatch-episode"></span>
    </div>

    <p class="appearance-note">
      Slide to change all three levels and table colors.
    </p>
  </div>
</details>

CONTENT

<script>
const countrySort = document.getElementById("country-sort");
const showSort = document.getElementById("show-sort");

/* Sorting */

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

/* Option-click / Alt-click:
   Collapse all sections at the clicked hierarchy level. */

document.addEventListener("click", event => {
  if (!event.altKey) return;

  const summary = event.target.closest("summary");
  if (!summary) return;

  const section = summary.parentElement;
  if (!section.matches("details")) return;

  let sections;

  if (section.classList.contains("country")) {
    sections = document.querySelectorAll("details.country");

  } else if (section.classList.contains("show")) {
    sections = document.querySelectorAll("details.show");

  } else if (section.classList.contains("episode")) {
    sections = document.querySelectorAll("details.episode");

  } else {
    return;
  }

  event.preventDefault();

  sections.forEach(item => {
    item.open = false;
  });
});

/* Live hue-based color theme */

const hueSlider = document.getElementById("hue-slider");
const root = document.documentElement;

const defaultHue = 214;
const storageKey = "bmi-history-hue";

function applyHue(hue) {
  const h = Number(hue);

  if (!Number.isFinite(h) || h < 0 || h > 360) {
    return;
  }

  hueSlider.value = h;

  const colors = {
    "--country-bg": `hsl(${h}, 17%, 28%)`,
    "--show-bg": `hsl(${h}, 24%, 22%)`,
    "--episode-bg": `hsl(${h}, 32%, 15%)`,

    "--table-header": `hsl(${h}, 29%, 23%)`,
    "--table-row": `hsl(${h}, 38%, 13%)`,
    "--table-alt": `hsl(${h}, 31%, 19%)`,
    "--table-border": `hsl(${h}, 24%, 27%)`
  };

  for (const [property, value] of Object.entries(colors)) {
    root.style.setProperty(property, value);
  }
}

/* Apply saved preference without sorting the page */

let savedHue = null;

try {
  savedHue = localStorage.getItem(storageKey);
} catch (error) {
  // The page still works if browser storage is unavailable.
}

if (
  savedHue !== null &&
  savedHue !== "" &&
  Number.isFinite(Number(savedHue))
) {
  applyHue(Number(savedHue));
}

/* Change colors instantly when moving the slider */

hueSlider.addEventListener("input", () => {
  applyHue(hueSlider.value);
});

/* Save the selected hue */

hueSlider.addEventListener("change", () => {
  try {
    localStorage.setItem(storageKey, hueSlider.value);
  } catch (error) {
    // The chosen color still works for the current visit.
  }
});
</script>

</body>
</html>"""

page = page.replace("RECORD_COUNT", f"{total:,}")
page = page.replace("CONTENT", "\n".join(parts))

output.write_text(page, encoding="utf-8")

print(f"Created {output} with {total:,} records.")
