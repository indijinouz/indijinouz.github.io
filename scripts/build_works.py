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

    required_headers = {
        "TitleNumber",
        "Title",
        "WtrPubIndicator",
        "Participant",
    }

    missing_headers = sorted(required_headers.difference(headers))

    if missing_headers:
        raise ValueError(
            "The Works Catalog is missing required columns: "
            + ", ".join(missing_headers)
        )

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


# Generate the default Title view.

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

<h1><a class="home-link" href="/">Michael Angelo Garcia (Indijinouz)</a></h1>
<h2>BMI Works Catalog</h2>
<p class="subtitle">WORK_COUNT registered works</p>

<form class="accordion-search" id="work-search-form">
  <input
    type="search"
    id="work-search"
    placeholder="Search titles, writers, publishers..."
    aria-label="Search Works Catalog"
    autocomplete="off"
  >
  <span id="search-count" aria-live="polite"></span>
</form>

<div class="sort-controls">
  <label for="works-view-sort">
    Sort:
    <select id="works-view-sort" aria-label="Choose Works Catalog view">
      <option value="title" selected>Title</option>
      <option value="participant">Participant</option>
    </select>
  </label>
</div>

<div id="title-view">
CONTENT
</div>

<div id="participant-view" hidden></div>

<footer class="accordion-footer">
  Source: <a href="/bmi-works-catalog/">BMI Works Catalog</a>
</footer>

<script>
"use strict";

const searchForm = document.getElementById("work-search-form");
const searchInput = document.getElementById("work-search");
const searchCount = document.getElementById("search-count");
const viewSort = document.getElementById("works-view-sort");
const titleView = document.getElementById("title-view");
const participantView = document.getElementById("participant-view");

const workSections = Array.from(
  titleView.querySelectorAll("details.work")
);

const searchableWorks = workSections.map(section => ({
  element: section,
  text: section.dataset.search
}));

let activeView = "title";
let submittedQuery = "";
let participantViewBuilt = false;
let participantSections = [];
let participantGroups = [];

function countLabel(count, view) {
  if (view === "participant") {
    return count.toLocaleString() +
      (count === 1 ? " Participant" : " Participants");
  }

  return count.toLocaleString() +
    (count === 1 ? " Work" : " Works");
}

function normalizeHeader(value) {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function createSummary(text) {
  const summary = document.createElement("summary");
  summary.textContent = text;
  return summary;
}

function buildParticipantView() {
  if (participantViewBuilt) return;

  const firstTable = titleView.querySelector("table");

  if (!firstTable) {
    participantViewBuilt = true;
    return;
  }

  const headerCells = Array.from(
    firstTable.querySelectorAll("thead th")
  );

  const headerNames = headerCells.map(cell =>
    normalizeHeader(cell.textContent.trim())
  );

  const indicatorIndex = headerNames.indexOf("wtrpubindicator");
  const participantIndex = headerNames.indexOf("participant");

  if (indicatorIndex === -1 || participantIndex === -1) {
    throw new Error(
      "WtrPubIndicator and Participant columns are required."
    );
  }

  const groupedRows = new Map();
  groupedRows.set("W", new Map());
  groupedRows.set("P", new Map());

  workSections.forEach(work => {
    work.querySelectorAll("tbody tr").forEach(row => {
      const cells = Array.from(row.cells);

      const indicator = (
        cells[indicatorIndex]?.textContent || "Other"
      ).trim().toUpperCase() || "Other";

      const participant = (
        cells[participantIndex]?.textContent || "Unknown Participant"
      ).trim() || "Unknown Participant";

      if (!groupedRows.has(indicator)) {
        groupedRows.set(indicator, new Map());
      }

      const indicatorGroup = groupedRows.get(indicator);

      if (!indicatorGroup.has(participant)) {
        indicatorGroup.set(participant, {
          rows: [],
          searchValues: []
        });
      }

      const participantGroup = indicatorGroup.get(participant);

      participantGroup.rows.push(row.cloneNode(true));

      participantGroup.searchValues.push(
        cells
          .map(cell => cell.textContent.trim())
          .join(" ")
          .toLowerCase()
      );
    });
  });

  const extraIndicators = Array.from(groupedRows.keys())
    .filter(indicator => indicator !== "W" && indicator !== "P")
    .sort((left, right) => left.localeCompare(right));

  const indicatorOrder = ["W", "P", ...extraIndicators];

  indicatorOrder.forEach(indicator => {
    const indicatorGroup = groupedRows.get(indicator);

    if (!indicatorGroup || indicatorGroup.size === 0) return;

    const indicatorSection = document.createElement("details");

    indicatorSection.className =
      "country participant-group";

    indicatorSection.appendChild(
      createSummary(indicator)
    );

    const sortedParticipants =
      Array.from(indicatorGroup.entries()).sort(
        ([left], [right]) =>
          left.localeCompare(
            right,
            undefined,
            { sensitivity: "base" }
          )
      );

    sortedParticipants.forEach(
      ([participant, participantData]) => {
        const participantSection =
          document.createElement("details");

        participantSection.className =
          "show participant";

        participantSection.appendChild(
          createSummary(participant)
        );

        const tableWrap = document.createElement("div");
        tableWrap.className = "table-wrap";

        const table = document.createElement("table");
        const tableHead = firstTable.tHead.cloneNode(true);
        const tableBody = document.createElement("tbody");

        participantData.rows.forEach(row => {
          tableBody.appendChild(row);
        });

        table.appendChild(tableHead);
        table.appendChild(tableBody);
        tableWrap.appendChild(table);
        participantSection.appendChild(tableWrap);
        indicatorSection.appendChild(participantSection);

        participantSections.push({
          element: participantSection,
          text: (
            indicator + " " +
            participant + " " +
            participantData.searchValues.join(" ")
          ).toLowerCase()
        });
      }
    );

    participantGroups.push(indicatorSection);
    participantView.appendChild(indicatorSection);
  });

  participantViewBuilt = true;
}

function filterTitleView(query) {
  let visible = 0;

  searchableWorks.forEach(work => {
    const matches =
      !query || work.text.includes(query);

    work.element.hidden = !matches;

    if (matches) {
      visible += 1;
    }
  });

  searchCount.textContent =
    countLabel(visible, "title");
}

function filterParticipantView(query) {
  let visible = 0;

  participantSections.forEach(participant => {
    const matches =
      !query || participant.text.includes(query);

    participant.element.hidden = !matches;

    if (matches) {
      visible += 1;
    }
  });

  participantGroups.forEach(group => {
    const hasVisibleParticipant =
      Array.from(group.children).some(child =>
        child.matches("details.participant") &&
        !child.hidden
      );

    group.hidden = !hasVisibleParticipant;
  });

  searchCount.textContent =
    countLabel(visible, "participant");
}

function filterActiveView() {
  if (activeView === "participant") {
    filterParticipantView(submittedQuery);
  } else {
    filterTitleView(submittedQuery);
  }
}

function changeView() {
  activeView = viewSort.value;

  if (activeView === "participant") {
    buildParticipantView();
  }

  titleView.hidden = activeView !== "title";
  participantView.hidden =
    activeView !== "participant";

  filterActiveView();
}

searchCount.textContent =
  countLabel(workSections.length, "title");


// Search only after Enter is pressed.

searchForm.addEventListener("submit", event => {
  event.preventDefault();

  submittedQuery =
    searchInput.value.trim().toLowerCase();

  filterActiveView();
});


viewSort.addEventListener("change", changeView);


/* Option-click (Mac) / Alt-click (Windows):
   Collapse all expanded sections in the active view. */

document.addEventListener("click", event => {
  if (!event.altKey) return;

  const summary = event.target.closest("summary");

  if (!summary) return;

  const activeContainer =
    activeView === "participant"
      ? participantView
      : titleView;

  if (!activeContainer.contains(summary)) return;

  event.preventDefault();

  activeContainer
    .querySelectorAll("details")
    .forEach(section => {
      section.open = false;
    });
});
</script>

</body>
</html>"""

page = page.replace(
    "WORK_COUNT",
    f"{len(works):,}"
)

page = page.replace(
    "CONTENT",
    "\n".join(parts)
)

output.write_text(
    page,
    encoding="utf-8"
)

print(
    f"Created {output} with "
    f"{len(works):,} registered works "
    f"and {total_records:,} records."
)
