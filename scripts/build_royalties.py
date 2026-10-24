import csv
import html
from pathlib import Path
from collections import defaultdict

source = Path("bmi-royalty-statements")
output = Path("bmi-royalty-history.html")

# Exclude these columns from the generated HTML.
# Original CSV files remain unchanged.

excluded_columns = {
    "ROYALTY AMOUNT",
    "WITHHOLD",
    "CURRENT ACTIVITY AMT",
    "HITS SONG OR TV NET SUPER USAGE BONUS",
    "STANDARDS OR TV NET THEME BONUS",
    "FOREIGN SOCIETY ADJUSTMENT",
}

data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
all_headers = []
total = 0

for file in sorted(source.glob("*.csv")):
    with file.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            continue

        # Include only permitted, non-empty column headers.

        for header in reader.fieldnames:
            if (
                header
                and header.strip()
                and header.strip().upper() not in excluded_columns
                and header not in all_headers
            ):
                all_headers.append(header)

        for row in reader:
            if not any(row.values()):
                continue

            country = row.get("COUNTRY OF PERFORMANCE") or "Unknown"
            show = row.get("SHOW NAME") or "Unspecified"
            episode = row.get("EPISODE NAME") or "Unspecified"

            # Remove excluded fields from the generated records.

            clean_row = {
                key: value
                for key, value in row.items()
                if key
                and key.strip()
                and key.strip().upper() not in excluded_columns
            }

            data[country][show][episode].append(clean_row)
            total += 1


def esc(value):
    return html.escape(str(value or ""), quote=True)


parts = []

for country, shows in sorted(
    data.items(),
    key=lambda item: -sum(
        len(rows)
        for episodes in item[1].values()
        for rows in episodes.values()
    )
):
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
<link rel="stylesheet" href="/style.css">
</head>

<body class="accordion-page">

<h1>Michael Angelo Garcia (Indijinouz)</h1>
<h2>BMI Royalty History</h2>
<p class="subtitle">RECORD_COUNT records</p>

<div class="sort-controls">

  <label for="country-sort">
    Countries:
    <select id="country-sort">
      <option value="alpha">Alphabetical</option>
      <option value="count" selected>Most Records</option>
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
    sections = document.querySelectorAll("details.country");

  } else if (section.classList.contains("show")) {
    sections = document.querySelectorAll("details.show");

  } else if (section.classList.contains("episode")) {
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
