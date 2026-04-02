# Examples

This folder contains a small example set that demonstrates the expected input and output format of WebDoMiner.

## Files

- `sample_rs.txt`  
  A sample Requirements Specification (RS) document used as input to the pipeline.

- `example_summary.json`  
  A summary of a completed run, including keyword counts, discovered URLs, accepted documents, rejected pages, failed pages, and previewed queries.

- `example_corpus.jsonl`  
  Example accepted output. Each line is one validated web page stored as a JSON object.

- `example_rejected.jsonl`  
  Example rejected output. These pages were processed but excluded because they did not satisfy the configured quality or similarity requirements.

- `example_failed.jsonl`  
  Example failed output. These pages could not be processed successfully because of HTTP errors, rate limits, or other retrieval issues.

## Purpose

These files are included to help readers quickly understand:

- what kind of RS input WebDoMiner expects
- how the pipeline transforms the RS into search queries
- what accepted, rejected, and failed outputs look like
- how a completed run is summarized

## Important Note

The sample RS included here is only an example. WebDoMiner is designed to be **domain-neutral** and driven by the RS document itself. That means the same pipeline can be used with requirements documents from different domains, such as healthcare, logistics, education, operations, or other system types.

## Expected Workflow

A typical workflow is:

1. provide an RS document as input
2. run the CLI
3. inspect the summary file
4. inspect the accepted corpus
5. review rejected and failed pages if you want to debug or tune the run

## Running the Example

From the project root:

```bash
python -m webdominer.cli --input "examples/sample_rs.txt"
```

You can also change parameters such as the number of keywords, number of URLs per query, similarity threshold, and minimum word count from the CLI.

## Notes

The example outputs are intended to illustrate structure and workflow. Actual outputs may differ from run to run because web search results, page availability, blocking behavior, and retrieved content can change over time.
