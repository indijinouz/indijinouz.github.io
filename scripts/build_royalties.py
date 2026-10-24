
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
                f'<details class="episode" data-name="{esc(episode)}">'
                f'<summary>{esc(episode)}'
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

<style>

/* Search bar */

.search-container {
  max-width: 700px;
  margin: 24px auto 20px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
}

#royalty-search {
  flex: 1;
  min-width: 0;
  padding: 12px 16px;
  font: inherit;
  font-size: 16px;
  color: inherit;
  background: transparent;
  border: 1px solid #999;
  border-radius: 6px;
  box-sizing: border-box;
}

#royalty-search:focus {
  outline: 2px solid #777;
  outline-offset: 2px;
}

#clear-search {
  padding: 10px 14px;
  font: inherit;
  cursor: pointer;
  border: 1px solid #999;
  border-radius: 6px;
  background: transparent;
  color: inherit;
}

#clear-search:disabled {
  opacity: 0.4;
  cursor: default;
}

#search-status {
  margin-top: 8px;
  font-size: 13px;
  opacity: 0.7;
  text-align: left;
}

</style>
</head>

<body class="accordion-page">

<h1>Michael Angelo Garcia (Indijinouz)</h1>
<h2>BMI Royalty History</h2>
<p class="subtitle">RECORD_COUNT records</p>

<!-- Search -->

<div class="search-container">

  <div class="search-box">

    <input
      type="search"
      id="royalty-search"
      placeholder="Search songs, shows, episodes, countries..."
      aria-label="Search BMI royalty history"
      autocomplete="off"
    >

    <button id="clear-search" type="button" disabled>
      Clear
    </button>

  </div>

  <div id="search-status" role="status" aria-live="polite">
    Search across all royalty records
  </div>

</div>

<!-- Sorting -->

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
      <option value="alpha" selected>Alphabetical</option>
      <option value="count">Most Records</option>
    </select>
  </label>

</div>

<!-- Royalty records -->

CONTENT

<script>

const countrySort = document.getElementById("country-sort");
const showSort = document.getElementById("show-sort");

const searchInput = document.getElementById("royalty-search");
const clearButton = document.getElementById("clear-search");
const searchStatus = document.getElementById("search-status");

let searchTimer = null;
let savedOpenStates = null;
let activeSearch = false;

/* --------------------------------------------------
   Sorting
-------------------------------------------------- */

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


/* --------------------------------------------------
   Build search index once
-------------------------------------------------- */

function directChildren(parent, selector) {
  return Array.from(parent.children)
    .filter(child => child.matches(selector));
}

const searchIndex = directChildren(
  document.body,
  "details.country"
).map(country => ({

  element: country,
  name: country.dataset.name.toLowerCase(),

  shows: directChildren(country, "details.show").map(show => ({

    element: show,
    name: show.dataset.name.toLowerCase(),

    episodes: directChildren(show, "details.episode").map(episode => ({

      element: episode,
      name: episode.dataset.name.toLowerCase(),

      rows: Array.from(
        episode.querySelectorAll("tbody tr")
      ).map(row => ({

        element: row,
        text: row.textContent.toLowerCase()

      }))

    }))

  }))

}));


/* --------------------------------------------------
   Save and restore accordion states
-------------------------------------------------- */

function saveAccordionStates() {

  savedOpenStates = new Map();

  document.querySelectorAll("details").forEach(section => {
    savedOpenStates.set(section, section.open);
  });

}

function restoreAccordionStates() {

  if (!savedOpenStates) return;

  savedOpenStates.forEach((wasOpen, section) => {
    section.open = wasOpen;
  });

  savedOpenStates = null;

}


/* --------------------------------------------------
   Search
-------------------------------------------------- */

function performSearch() {

  const query = searchInput.value.trim().toLowerCase();

  clearButton.disabled = !query;

  // Empty search: restore everything.

  if (!query) {

    searchIndex.forEach(country => {

      country.element.style.display = "";

      country.shows.forEach(show => {

        show.element.style.display = "";

        show.episodes.forEach(episode => {

          episode.element.style.display = "";

          episode.rows.forEach(row => {
            row.element.style.display = "";
          });

        });

      });

    });

    restoreAccordionStates();

    activeSearch = false;

    searchStatus.textContent =
      "Search across all royalty records";

    return;
  }

  // Save the user's original expanded/collapsed view.

  if (!activeSearch) {
    saveAccordionStates();
    activeSearch = true;
  }

  let matchingRecords = 0;

  searchIndex.forEach(country => {

    const countryMatches = country.name.includes(query);

    let countryHasMatches = false;

    country.shows.forEach(show => {

      const showMatches =
        countryMatches || show.name.includes(query);

      let showHasMatches = false;

      show.episodes.forEach(episode => {

        const episodeMatches =
          showMatches || episode.name.includes(query);

        let episodeMatchCount = 0;

        episode.rows.forEach(row => {

          const matches =
            episodeMatches || row.text.includes(query);

          row.element.style.display =
            matches ? "" : "none";

          if (matches) {
            episodeMatchCount++;
          }

        });

        const episodeHasMatches = episodeMatchCount > 0;

        episode.element.style.display =
          episodeHasMatches ? "" : "none";

        if (episodeHasMatches) {

          episode.element.open = true;

          showHasMatches = true;
          matchingRecords += episodeMatchCount;

        }

      });

      show.element.style.display =
        showHasMatches ? "" : "none";

      if (showHasMatches) {

        show.element.open = true;
        countryHasMatches = true;

      }

    });

    country.element.style.display =
      countryHasMatches ? "" : "none";

    if (countryHasMatches) {
      country.element.open = true;
    }

  });

  searchStatus.textContent =
    matchingRecords.toLocaleString() +
    (matchingRecords === 1
      ? " matching record"
      : " matching records");

}


/* --------------------------------------------------
   Debounced live search
-------------------------------------------------- */

searchInput.addEventListener("input", () => {

  clearTimeout(searchTimer);

  searchTimer = setTimeout(() => {
    performSearch();
  }, 250);

});


/* --------------------------------------------------
   Clear search
-------------------------------------------------- */

clearButton.addEventListener("click", () => {

  clearTimeout(searchTimer);

  searchInput.value = "";

  performSearch();

  searchInput.focus();

});


/* --------------------------------------------------
   Option-click / Alt-click collapsing

   Country: collapse all countries
   Show: collapse all shows
   Episode: collapse all episodes

   Normal clicks retain native accordion behavior.
-------------------------------------------------- */

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
page = page.replace("CONTENT", "\\n".join(parts))

output.write_text(page, encoding="utf-8")

print(f"Created {output} with {total:,} records.")
