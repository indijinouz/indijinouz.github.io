import csv
import html
import io
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, MutableMapping, Tuple


REPOSITORY = Path(__file__).resolve().parent.parent
SOURCE = REPOSITORY / "bmi-royalty-statements"
OUTPUT = REPOSITORY / "bmi-royalty-records.html"
DATA_DIRECTORY = REPOSITORY / "bmi-royalty-records-data"

# Bundles normally contain about this many records. An individual episode is
# never split, so an unusually large episode can make one bundle larger.
TARGET_RECORDS_PER_CHUNK = 1_000

# The browser appends at most this many table rows per animation frame.
RENDER_BATCH_SIZE = 100

# These fields never appear in either the generated HTML or JSON. The source
# CSV files are only read, so they remain unchanged.
EXCLUDED_COLUMNS = {
    "ROYALTY AMOUNT",
    "WITHHOLD",
    "CURRENT ACTIVITY AMT",
    "HITS SONG OR TV NET SUPER USAGE BONUS",
    "STANDARDS OR TV NET THEME BONUS",
    "FOREIGN SOCIETY ADJUSTMENT",
}

Row = Dict[str, str]
EpisodeKey = Tuple[str, str, str]
EpisodeData = Tuple[str, str, str, List[Row]]


def escaped(value: object) -> str:
    """Escape a value before inserting it into HTML text or attributes."""

    return html.escape(str(value or ""), quote=True)


def dimension(row: Mapping[str, str], column: str, fallback: str) -> str:
    """Return a useful accordion label without changing nonblank CSV text."""

    value = row.get(column) or ""
    return value if value.strip() else fallback


def csv_rows(path: Path) -> Iterator[Row]:
    """Read a CSV, tolerating replacement characters and embedded NUL bytes.

    A historical statement contains NUL padding. Python's CSV reader rejects
    NULs, while removing them restores the ordinary CSV text around them.
    """

    text = path.read_text(encoding="utf-8-sig", errors="replace").replace("\0", "")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        return

    for raw_row in reader:
        # DictReader can use None as a key for surplus fields. Those values
        # cannot be named as columns, so ignore them just as the old builder did.
        row = {key: value or "" for key, value in raw_row.items() if key}
        if any(row.values()):
            yield row


def read_source() -> Tuple[List[str], MutableMapping[str, object], int]:
    """Read all statements and return headers, hierarchy, and record count."""

    headers: List[str] = []
    known_headers = set()
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    total = 0

    csv_files = sorted(SOURCE.glob("*.csv"))
    if not csv_files:
        raise SystemExit(f"No CSV files found in {SOURCE}")

    for path in csv_files:
        for row in csv_rows(path):
            for header in row:
                normalized = header.strip().upper()
                if (
                    header.strip()
                    and normalized not in EXCLUDED_COLUMNS
                    and header not in known_headers
                ):
                    headers.append(header)
                    known_headers.add(header)

            country = dimension(row, "COUNTRY OF PERFORMANCE", "Unknown")
            show = dimension(row, "SHOW NAME", "Unspecified")
            episode = dimension(row, "EPISODE NAME", "Unspecified")

            clean_row = {
                key: value
                for key, value in row.items()
                if key.strip() and key.strip().upper() not in EXCLUDED_COLUMNS
            }
            data[country][show][episode].append(clean_row)
            total += 1

    return headers, data, total


def count_show(episodes: Mapping[str, List[Row]]) -> int:
    return sum(len(rows) for rows in episodes.values())


def count_country(shows: Mapping[str, Mapping[str, List[Row]]]) -> int:
    return sum(count_show(episodes) for episodes in shows.values())


def sorted_hierarchy(data: Mapping[str, object]) -> Iterable[EpisodeData]:
    """Yield episodes in the same initial order used by the old page."""

    countries = sorted(
        data.items(),
        key=lambda item: (-count_country(item[1]), item[0].casefold()),
    )
    for country, shows in countries:
        for show, episodes in sorted(shows.items(), key=lambda item: item[0].casefold()):
            for episode, rows in sorted(
                episodes.items(), key=lambda item: item[0].casefold()
            ):
                yield country, show, episode, rows


def write_chunks(
    episodes: List[EpisodeData], headers: List[str]
) -> Dict[EpisodeKey, Tuple[str, str]]:
    """Bundle whole episodes into JSON files and return their lookup metadata."""

    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for stale_chunk in DATA_DIRECTORY.glob("chunk-*.json"):
        stale_chunk.unlink()

    locations: Dict[EpisodeKey, Tuple[str, str]] = {}
    pending: Dict[str, List[List[str]]] = {}
    pending_count = 0
    chunk_number = 0

    def flush() -> None:
        nonlocal pending, pending_count, chunk_number
        if not pending:
            return
        chunk_number += 1
        filename = f"chunk-{chunk_number:04d}.json"
        path = DATA_DIRECTORY / filename
        path.write_text(
            json.dumps(pending, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        pending = {}
        pending_count = 0

    for episode_number, (country, show, episode, rows) in enumerate(episodes, 1):
        if pending and pending_count + len(rows) > TARGET_RECORDS_PER_CHUNK:
            flush()

        episode_id = f"e{episode_number:05d}"
        filename = f"chunk-{chunk_number + 1:04d}.json"
        locations[(country, show, episode)] = (filename, episode_id)
        pending[episode_id] = [
            [str(row.get(header) or "") for header in headers] for row in rows
        ]
        pending_count += len(rows)

    flush()
    return locations


def write_search_index(
    episodes: List[EpisodeData],
    headers: List[str],
    locations: Mapping[EpisodeKey, Tuple[str, str]],
) -> None:
    """Write one compact searchable entry for each episode."""

    search_index: Dict[str, str] = {}

    for country, show, episode, rows in episodes:
        episode_id = locations[(country, show, episode)][1]
        values: List[str] = []
        known_values = set()

        def add_value(value: object) -> None:
            normalized = " ".join(str(value or "").lower().split())
            if normalized and normalized not in known_values:
                known_values.add(normalized)
                values.append(normalized)

        add_value(country)
        add_value(show)
        add_value(episode)

        for row in rows:
            for header in headers:
                add_value(row.get(header))

        search_index[episode_id] = "\n".join(values)

    (DATA_DIRECTORY / "search-index.json").write_text(
        json.dumps(search_index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def html_sections(
    data: Mapping[str, object],
    locations: Mapping[EpisodeKey, Tuple[str, str]],
) -> str:
    parts: List[str] = ['<main id="royalty-accordion">']
    countries = sorted(
        data.items(),
        key=lambda item: (-count_country(item[1]), item[0].casefold()),
    )

    for country, shows in countries:
        country_count = count_country(shows)
        parts.append(
            f'<details class="country" data-count="{country_count}" '
            f'data-name="{escaped(country)}"><summary>{escaped(country)}'
            f'<span class="count">{country_count:,} records</span></summary>'
        )

        for show, episodes in sorted(shows.items(), key=lambda item: item[0].casefold()):
            show_count = count_show(episodes)
            parts.append(
                f'<details class="show" data-count="{show_count}" '
                f'data-name="{escaped(show)}"><summary>{escaped(show)}'
                f'<span class="count">{show_count:,}</span></summary>'
            )

            for episode, rows in sorted(
                episodes.items(), key=lambda item: item[0].casefold()
            ):
                filename, episode_id = locations[(country, show, episode)]
                parts.append(
                    f'<details class="episode" data-count="{len(rows)}" '
                    f'data-name="{escaped(episode)}" data-episode-id="{episode_id}" '
                    f'data-chunk="bmi-royalty-records-data/{filename}">'
                    f'<summary>{escaped(episode)}'
                    f'<span class="count">{len(rows):,}</span></summary>'
                    '<div class="episode-records"></div></details>'
                )

            parts.append("</details>")
        parts.append("</details>")

    parts.append("</main>")
    return "\n".join(parts)


def script_json(value: object) -> str:
    """Serialize safe inline JavaScript data, including defensive tag escaping."""

    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def build_page(headers: List[str], sections: str, total: int) -> str:
    
    template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BMI Royalty Records | Michael Angelo Garcia (Indijinouz)</title>
<link rel="stylesheet" href="/style.css">
</head>

<body class="accordion-page">

<h1><a class="home-link" href="/">Michael Angelo Garcia (Indijinouz)</a></h1>
<h2>BMI Royalty Records</h2>
<p class="subtitle">RECORD_COUNT records</p>

<form class="accordion-search" id="royalty-search-form">
  <input
    type="search"
    id="royalty-search"
    placeholder="Search titles, shows, episodes..."
    aria-label="Search Royalty Records"
    autocomplete="off"
  >
  <span id="search-count" aria-live="polite"></span>
</form>

<div class="sort-controls">
  <label for="country-sort">
    Countries:
    <select id="country-sort">
      <option value="alpha">Alphabetical</option>
      <option value="count" selected>Count</option>
    </select>
  </label>

  <label for="show-sort">
    Shows:
    <select id="show-sort">
      <option value="alpha">Alphabetical</option>
      <option value="count">Count</option>
    </select>
  </label>
</div>

CONTENT

<footer class="accordion-footer">
  Source: <a href="/bmi-royalty-statements/">BMI Royalty Statements</a>
</footer>

<script>
"use strict";

const headers = HEADERS;
const renderBatchSize = RENDER_BATCH_SIZE;
const countrySort = document.getElementById("country-sort");
const showSort = document.getElementById("show-sort");
const accordion = document.getElementById("royalty-accordion");
const searchForm = document.getElementById("royalty-search-form");
const searchInput = document.getElementById("royalty-search");
const searchCount = document.getElementById("search-count");

const episodeCountLabel =
  accordion.querySelectorAll("details.episode").length.toLocaleString() +
  " episodes";

searchCount.textContent = episodeCountLabel;

const chunkRequests = new Map();
const renderStates = new WeakMap();
let searchIndexRequest;
let searchSequence = 0;

function sortSections(parent, selector, mode) {
  const sections = Array.from(parent.children).filter(element =>
    element.matches(selector)
  );

  sections.sort((left, right) => {
    if (mode === "count") {
      const difference = Number(right.dataset.count) - Number(left.dataset.count);
      if (difference !== 0) return difference;
    }
    return left.dataset.name.localeCompare(right.dataset.name, undefined, {
      sensitivity: "base"
    });
  });

  sections.forEach(section => parent.appendChild(section));
}

function updateSorting() {
  sortSections(accordion, "details.country", countrySort.value);
  accordion.querySelectorAll("details.country").forEach(country => {
    sortSections(country, "details.show", showSort.value);
  });
}

countrySort.addEventListener("change", updateSorting);
showSort.addEventListener("change", updateSorting);

function fetchSearchIndex() {
  if (!searchIndexRequest) {
    searchIndexRequest = fetch("bmi-royalty-records-data/search-index.json")
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status} while loading the search index`);
        }
        return response.json();
      })
      .catch(error => {
        searchIndexRequest = undefined;
        throw error;
      });
  }
  return searchIndexRequest;
}

function showAllSections() {
  accordion.querySelectorAll("details.country, details.show, details.episode")
    .forEach(section => { section.hidden = false; });
}

function filterHierarchy(matches) {
  const episodes = accordion.querySelectorAll("details.episode");
  episodes.forEach(episode => {
    episode.hidden = !matches.has(episode.dataset.episodeId);
  });

  accordion.querySelectorAll("details.show").forEach(show => {
    const hasMatch = Array.from(show.children).some(child =>
      child.matches("details.episode") && !child.hidden
    );
    show.hidden = !hasMatch;
  });

  accordion.querySelectorAll("details.country").forEach(country => {
    const hasMatch = Array.from(country.children).some(child =>
      child.matches("details.show") && !child.hidden
    );
    country.hidden = !hasMatch;
  });
}

searchForm.addEventListener("submit", async event => {
  event.preventDefault();
  const query = searchInput.value.trim().toLowerCase();
  const requestNumber = ++searchSequence;

if (!query) {
  showAllSections();
  searchCount.textContent = episodeCountLabel;
  return;
}

  const terms = query.split(/\s+/).filter(Boolean);
  searchCount.textContent = "Searching…";

  try {
    const searchIndex = await fetchSearchIndex();
    if (requestNumber !== searchSequence) return;

    const matches = new Set();
    Object.entries(searchIndex).forEach(([episodeId, text]) => {
      if (terms.every(term => text.includes(term))) matches.add(episodeId);
    });

    filterHierarchy(matches);
    searchCount.textContent =
      matches.size.toLocaleString() +
      (matches.size === 1 ? " matching episode" : " matching episodes");
  } catch (error) {
    if (requestNumber !== searchSequence) return;
    searchCount.textContent = "Search could not be loaded. Press Enter to retry.";
    console.error(error);
  }
});

searchInput.addEventListener("keydown", event => {
  if (event.key !== "Escape") return;

  searchInput.value = "";
  searchSequence += 1;
  showAllSections();
  searchCount.textContent = episodeCountLabel;
});

function fetchChunk(url) {
  if (!chunkRequests.has(url)) {
    const request = fetch(url).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status} while loading ${url}`);
      }
      return response.json();
    }).catch(error => {
      chunkRequests.delete(url);
      throw error;
    });
    chunkRequests.set(url, request);
  }
  return chunkRequests.get(url);
}

function renderNextBatch(section) {
  const state = renderStates.get(section);
  if (!state || state.scheduled || !section.open) return;

  const fragment = document.createDocumentFragment();
  const stop = Math.min(state.index + renderBatchSize, state.rows.length);
  for (; state.index < stop; state.index += 1) {
    const tableRow = document.createElement("tr");
    state.rows[state.index].forEach(value => {
      const cell = document.createElement("td");
      cell.textContent = value;
      tableRow.appendChild(cell);
    });
    fragment.appendChild(tableRow);
  }
  state.body.appendChild(fragment);

  if (state.index < state.rows.length) {
    state.scheduled = true;
    requestAnimationFrame(() => {
      state.scheduled = false;
      renderNextBatch(section);
    });
  }
}

function prepareTable(section, rows) {
  const container = section.querySelector(":scope > .episode-records");
  const wrapper = document.createElement("div");
  wrapper.className = "table-wrap";
  const table = document.createElement("table");
  const head = document.createElement("thead");
  const headingRow = document.createElement("tr");
  headers.forEach(header => {
    const cell = document.createElement("th");
    cell.textContent = header;
    headingRow.appendChild(cell);
  });
  head.appendChild(headingRow);
  const body = document.createElement("tbody");
  table.append(head, body);
  wrapper.appendChild(table);
  container.replaceChildren(wrapper);
  renderStates.set(section, { body, rows, index: 0, scheduled: false });
  renderNextBatch(section);
}

async function loadEpisode(section) {
  const container = section.querySelector(":scope > .episode-records");
  section.dataset.loadState = "loading";
  const status = document.createElement("p");
  status.setAttribute("role", "status");
  status.textContent = "Loading records…";
  container.replaceChildren(status);

  try {
    const chunk = await fetchChunk(section.dataset.chunk);
    const rows = chunk[section.dataset.episodeId];
    if (!Array.isArray(rows)) throw new Error("Episode data is missing from its chunk");
    section.dataset.loadState = "loaded";
    prepareTable(section, rows);
  } catch (error) {
    section.dataset.loadState = "error";
    status.textContent = "Could not load these records. Close and reopen to retry.";
    console.error(error);
  }
}

accordion.addEventListener("toggle", event => {
  const section = event.target;
  if (!(section instanceof HTMLDetailsElement) ||
      !section.classList.contains("episode") || !section.open) return;

  if (section.dataset.loadState === "loaded") {
    renderNextBatch(section);
  } else if (section.dataset.loadState !== "loading") {
    loadEpisode(section);
  }
}, true);

/* Option-click (Mac) / Alt-click (Windows) collapses every section at the
   clicked level globally. A normal click toggles only the clicked section. */
document.addEventListener("click", event => {
  if (!event.altKey) return;
  const summary = event.target.closest("summary");
  if (!summary) return;
  const section = summary.parentElement;
  if (!(section instanceof HTMLDetailsElement)) return;

  let selector;
  if (section.classList.contains("country")) selector = "details.country";
  else if (section.classList.contains("show")) selector = "details.show";
  else if (section.classList.contains("episode")) selector = "details.episode";
  else return;

  event.preventDefault();
  document.querySelectorAll(selector).forEach(item => { item.open = false; });
});
</script>

</body>
</html>
"""
    return (
        template.replace("RECORD_COUNT", f"{total:,}")
        .replace("CONTENT", sections)
        .replace("HEADERS", script_json(headers))
        .replace("RENDER_BATCH_SIZE", str(RENDER_BATCH_SIZE))
    )


def main() -> None:
    headers, data, total = read_source()
    episodes = list(sorted_hierarchy(data))
    locations = write_chunks(episodes, headers)
    write_search_index(episodes, headers, locations)
    sections = html_sections(data, locations)
    OUTPUT.write_text(
        build_page(headers, sections, total),
        encoding="utf-8",
    )
    
    chunks = len(list(DATA_DIRECTORY.glob("chunk-*.json")))
    print(
        f"Created {OUTPUT.name} with {total:,} records in "
        f"{len(episodes):,} episodes and {chunks:,} JSON chunks."
    )


if __name__ == "__main__":
    main()
