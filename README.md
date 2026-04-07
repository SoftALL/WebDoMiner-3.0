# WebDoMiner

WebDoMiner generates a domain-specific corpus from the open web using a natural-language Requirements Specification (RS) document. It extracts meaningful keywords from the RS itself, discovers relevant public web pages, scrapes and cleans their main text, filters low-value content, and outputs a structured JSONL corpus with full source traceability.

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
  - [1. Keyword Extraction](#1-keyword-extraction)
  - [2. URL Discovery](#2-url-discovery)
  - [3. Content Scraping and Cleaning](#3-content-scraping-and-cleaning)
  - [4. Semantic Filtering](#4-semantic-filtering)
  - [5. Structured Output](#5-structured-output)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Basic Run](#basic-run)
  - [Common Options](#common-options)
- [Input Format](#input-format)
- [Output Files](#output-files)
  - [Accepted Corpus](#accepted-corpus)
  - [Rejected Pages](#rejected-pages)
  - [Failed Pages](#failed-pages)
  - [Summary File](#summary-file)
- [Examples](#examples)
- [Testing](#testing)
- [Technology Stack](#technology-stack)
- [License](#license)

## Overview

WebDoMiner is designed for situations where a requirements document describes a system, workflow, or operational domain, but a supporting external corpus is still needed.

Instead of relying on paid APIs or closed services, the project uses fully local or free tools to:

- extract domain-oriented keywords from an RS document
- build search queries from those RS-derived keywords
- search the open web for potentially relevant pages
- remove low-value or boilerplate-heavy content
- measure semantic similarity between the RS and scraped pages
- produce a traceable corpus ready for downstream use

A key design goal of WebDoMiner is that the **RS document defines the domain**. The system is not limited to healthcare or any other fixed field. A healthcare RS, logistics RS, education RS, or another domain-specific RS should all drive different keyword extraction and discovery behavior from the same pipeline.

The project is useful for requirements engineering, domain understanding, retrieval pipelines, corpus bootstrapping, and related NLP workflows.

## How It Works

### 1. Keyword Extraction

WebDoMiner reads a `.txt` or `.docx` requirements document and extracts candidate keywords and keyphrases using KeyBERT. The extracted phrases are then cleaned and filtered to remove weak, generic, or document-title-style phrases.

This stage is designed to prefer search-worthy, domain-oriented phrases over noisy requirement-language fragments, while staying domain-neutral and driven by the RS content itself.

### 2. URL Discovery

The cleaned keywords are transformed into search queries and sent to a free search backend such as DuckDuckGo or a self-hosted SearxNG instance.

The query-building stage is RS-driven and domain-neutral:
- it starts from extracted keyword phrases
- it adds lightweight generic query patterns
- it uses RS-derived context terms rather than fixed domain templates

Discovered URLs are then:
- normalized for stable deduplication
- filtered to remove clearly low-value or non-HTML targets
- pre-ranked using lightweight title/snippet relevance scoring

This helps reduce wasted scraping effort on weak results.

### 3. Content Scraping and Cleaning

For each discovered URL, WebDoMiner first attempts standard HTML extraction with Trafilatura.

If the initial extraction appears too weak and the page looks JavaScript-rendered, the system can fall back to Playwright with headless Chromium, render the page, and retry extraction.

The extracted content is then cleaned and checked for:
- minimum word count
- low-value or blocked-page patterns
- general text quality

### 4. Semantic Filtering

After scraping, WebDoMiner embeds:
- the original RS document
- each cleaned web page

It then computes cosine similarity using a local SentenceTransformer model. Pages below the configured similarity threshold are rejected, while stronger matches are accepted into the final corpus.

This semantic filtering stage helps keep the final corpus aligned with the input RS even when search results are broad, noisy, or partially off-topic.

### 5. Structured Output

The final accepted corpus is written as JSONL. Separate JSONL files are also generated for rejected and failed pages, along with a summary JSON file describing the run.

This makes the output easy to inspect, debug, and reuse.

## Project Structure

```text
webdominer 3.0/
├── pyproject.toml
├── README.md
├── .gitignore
├── data/
│   ├── input/
│   └── output/
├── examples/
├── tests/
├── webdominer/
│   ├── __init__.py
│   ├── cli.py
│   ├── settings.py
│   ├── logging_utils.py
│   ├── models.py
│   ├── pipeline.py
│   ├── io/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   └── writer.py
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── keywording.py
│   │   ├── query_builder.py
│   │   ├── url_filters.py
│   │   ├── search_clients.py
│   │   └── discovery.py
│   ├── scraping/
│   │   ├── __init__.py
│   │   ├── cleaning.py
│   │   ├── quality_checks.py
│   │   ├── trafilatura_client.py
│   │   ├── playwright_client.py
│   │   └── scraper.py
│   └── semantic/
│       ├── __init__.py
│       ├── embeddings.py
│       └── similarity.py
```

## Requirements

- Python 3.9 or higher
- Internet access for web search and page retrieval
- Chromium installed for Playwright fallback

## Installation

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project:

```bash
pip install -e .
```

Install Chromium for Playwright:

```bash
playwright install chromium
```

For development dependencies, including tests:

```bash
pip install -e ".[dev]"
```

## Usage

### Basic Run

Place your input file in `data/input/` or `examples/`, then run:

```bash
python -m webdominer.cli --input "examples/sample_rs.txt"
```

If no `--input` argument is provided, WebDoMiner uses the default example file at `examples/sample_rs.txt`.

### Common Options

```bash
python -m webdominer.cli \
  --input "examples/sample_rs.txt" \
  --top-keywords 10 \
  --top-urls 5 \
  --similarity-threshold 0.45 \
  --min-word-count 150 \
  --log-level INFO
```

Available CLI options include:

- `--input`  
  Path to the RS file (`.txt` or `.docx`)

- `--accepted-output`  
  Path to the accepted corpus JSONL file

- `--rejected-output`  
  Path to the rejected JSONL file

- `--failed-output`  
  Path to the failed JSONL file

- `--summary-output`  
  Path to the summary JSON file

- `--top-keywords`  
  Number of keywords to extract

- `--top-urls`  
  Number of URLs requested per query

- `--similarity-threshold`  
  Minimum semantic similarity required for acceptance

- `--min-word-count`  
  Minimum acceptable extracted page length

- `--search-backend`  
  Search backend to use (`ddg` or `searxng`)

- `--searxng-base-url`  
  Base URL for a self-hosted SearxNG instance

- `--disable-playwright-fallback`  
  Disable JavaScript-rendering fallback

- `--log-level`  
  Logging level such as `INFO` or `DEBUG`

## Input Format

WebDoMiner accepts:

- `.txt`
- `.docx`

The input should be a natural-language Requirements Specification document that describes a system, workflow, domain, or operational process.

## Output Files

By default, output files are written to `data/output/`.

### Accepted Corpus

`corpus.jsonl`

Each line represents one accepted web page. Example fields:

- `id`
- `source_url`
- `matched_keyword`
- `similarity_score`
- `text`
- `title`
- `query`
- `extraction_method`
- `timestamp`

### Rejected Pages

`rejected.jsonl`

Contains pages that were successfully fetched or processed but rejected due to:
- low text quality
- insufficient word count
- low semantic similarity

### Failed Pages

`failed.jsonl`

Contains pages or search attempts that failed due to:
- HTTP errors
- rendering issues
- search backend errors

### Summary File

`summary.json`

Provides a structured overview of the run, including:
- number of keywords extracted
- raw search results
- discovered URLs
- pages scraped successfully
- rejected pages
- failed pages
- final accepted documents

## Examples

The `examples/` folder contains a sample input RS file and example output files that illustrate the expected input style and the structure of the produced results.

Included files demonstrate:

-   a sample requirements document used as pipeline input
-   a summary of a completed run
-   accepted corpus output in JSONL format
-   rejected pages output
-   failed pages output

The current example set uses a logistics RS to show that WebDoMiner is not limited to healthcare or any other fixed domain. The pipeline is designed to be domain-neutral and driven by the RS document itself, so different RS documents should lead to different keyword extraction, search queries, and discovered content.

## Testing

Run the full test suite with:

```bash
pytest
```

Or:

```bash
pytest -q
```

The test suite covers critical logic such as:
- keyword normalization and filtering
- URL filtering and normalization
- discovery-stage scoring and deduplication
- pipeline-level rejected and failed output deduplication

## Technology Stack

WebDoMiner uses:

- **Python** for the overall pipeline
- **KeyBERT** for keyword extraction
- **DuckDuckGo Search** or **SearxNG** for free web search
- **Trafilatura** for main-content extraction
- **Playwright** for JavaScript-rendered pages
- **SentenceTransformers** for local semantic similarity
- **Pytest** for testing

## License

This project is licensed under the MIT License.
