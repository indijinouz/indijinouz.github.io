
import csv
import html
from pathlib import Path
from collections import defaultdict

source = Path("bmi-works-catalog/CatalogExport_1079244.csv")
output = Path("bmi-works-catalog.html")


def esc(value):
    return html.escape(str(value or ""), quote=True)


# Read the Works Catalog.

with source.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    if not reader.fieldnames:
        raise ValueError("The Works Catalog has no column headers.")

    headers = [
        header
        for header in reader.fieldnames
        if header and header.strip()
    ]

    if "TitleNumber" not in headers or "Title" not in headers:
        raise ValueError("TitleNumber and Title columns are required.")

    works = defaultdict(list)
    total_records = 0

    for row in reader:
        if not any(
            value and value.strip()
            for value in row.values()
            if isinstance(value, str)
        ):
            continue

        work_id = (row.get("TitleNumber") or "").strip()

        if not work_id:
            work_id = f"missing-{total_records}"

        works[work_id].append(row)
        total_records += 1


# Alphabetically sort works before generating HTML.

sorted_works = sorted(
    works.items(),
    key=lambda item: (
        (item[1][0].get("Title") or "").casefold(),
        item[0]
    )
)


# Generate collapsible sections.

parts = []

for work_id, rows in sorted_works:
    first = rows[0]

    title = (first.get("Title") or "").strip() or "Untitled"
    title_number = (first.get("TitleNumber") or "").strip()

    # Build a searchable string from all participants
    # and all fields belonging to this composition.

    search_text = " ".join(
        str(row.get(header) or "")
        for row in rows
        for header in headers
    ).lower()

    parts.append(
        f'<details class="country work" '
        f'data-search="{esc(search_text)}">'
        f'<summary>{esc(title)}'
        f'<span class="count">BMI #{esc(title_number)}</span>'
        '</summary>'
    )

    parts.append('<div class="table-wrap"><table><thead><tr>')

    for header in headers:
        parts.append(f"<th>{esc(header)}</th>")

    parts.append("</tr></thead><tbody>")

    for row in rows:
        parts.append("<tr>")

        for header in headers:
            parts.append(f"<td>{esc(row.get(header))}</td>")

        parts.append("</tr>")

    parts.append("</tbody></table></div>")
    parts.append("</details>")


# Create the HTML page.

page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BMI Works Catalog | Michael Angelo Garcia (Indijinouz)</title>
<link rel="stylesheet" href="/style.css">
</head>

<body class="accordion-page">

<h1>Michael Angelo Garcia (Indijinouz)</h1>
<h2>BMI Works Catalog</h2>
<p class="subtitle">WORK_COUNT registered works</p>

<div class="catalog-search">
  <input
    type="search"
    id="work-search"
    placeholder="Search titles, writers, publishers..."
    aria-label="Search Works Catalog"
    autocomplete="off"
  >
  <span id="search-count" aria-live="polite"></span>
</div>

CONTENT

<script>
const searchInput = document.getElementById("work-search");
const searchCount = document.getElementById("search-count");

const workSections = Array.from(
  document.querySelectorAll("details.work")
);

// Cache searchable text once.

const searchableWorks = workSections.map(section => ({
  element: section,
  text: section.dataset.search
}));

function filterWorks() {
  const query = searchInput.value.trim().toLowerCase();

  let visible = 0;

  searchableWorks.forEach(work => {
    const matches = work.text.includes(query);

    work.element.hidden = !matches;

    if (matches) visible++;
  });

  searchCount.textContent =
    visible.toLocaleString() + " of " +
    searchableWorks.length.toLocaleString() + " works";
}

// Update search results as the user types.

searchInput.addEventListener("input", filterWorks);

// Display initial count.

searchCount.textContent =
  searchableWorks.length.toLocaleString() + " works";

/* Option-click (Mac) / Alt-click (Windows):
   Collapse all expanded compositions. */

document.addEventListener("click", event => {
  if (!event.altKey) return;

  const summary = event.target.closest("summary");
  if (!summary) return;

  const section = summary.parentElement;

  if (!section.matches("details.work")) return;

  event.preventDefault();

  workSections.forEach(item => {
    item.open = false;
  });
});
</script>

</body>
</html>"""

page = page.replace("WORK_COUNT", f"{len(works):,}")
page = page.replace("CONTENT", "\n".join(parts))

output.write_text(page, encoding="utf-8")

print(
    f"Created {output} with "
    f"{len(works):,} registered works "
    f"and {total_records:,} records."
)
