Examples
========

This folder contains a minimal example setup for WebDoMiner.

Files
-----

-   `sample_rs_healthcare.txt`\
    A sample requirements specification document for a healthcare appointment and clinic coordination system.
-   `example_summary.json`\
    Example summary output produced by a successful WebDoMiner run.
-   `example_corpus.jsonl`\
    Example accepted output showing validated corpus records.
-   `example_rejected.jsonl`\
    Example rejected output showing pages that were filtered out during scraping or semantic filtering.
-   `example_failed.jsonl`\
    Example failed output. In the provided example run, this file is empty because no pages failed.

Purpose
-------

These files are intended to help readers understand:

1.  what kind of input WebDoMiner expects
2.  what kind of output WebDoMiner produces
3.  how the accepted, rejected, and failed outputs are structured

How to Run the Example
----------------------

From the project root, run:

python -m webdominer.cli --input "examples/sample_rs_healthcare.txt"

This will generate output files in `data/output/` unless you provide custom output paths.

Notes
-----

-   The example input is only a sample requirements specification and is not tied to any real clinic.
-   The example outputs are illustrative and are meant to show the expected structure and style of results.
-   Depending on search engine behavior and web content changes, your actual output may differ from the example files.
-   If Playwright fallback is enabled, make sure Chromium is installed in your environment:

playwright install chromium