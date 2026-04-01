from __future__ import annotations

import argparse
import json
from pathlib import Path

from webdominer.pipeline import WebDoMinerPipeline
from webdominer.settings import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="webdominer",
        description=(
            "Generate a domain-specific corpus from the open web using "
            "a requirements specification document."
        ),
    )

    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to the RS file (.txt or .docx).",
    )
    parser.add_argument(
        "--accepted-output",
        type=str,
        default=None,
        help="Path to the accepted corpus JSONL output.",
    )
    parser.add_argument(
        "--rejected-output",
        type=str,
        default=None,
        help="Path to the rejected JSONL output.",
    )
    parser.add_argument(
        "--failed-output",
        type=str,
        default=None,
        help="Path to the failed JSONL output.",
    )
    parser.add_argument(
        "--summary-output",
        type=str,
        default=None,
        help="Path to the summary JSON output.",
    )

    parser.add_argument(
        "--top-keywords",
        type=int,
        default=None,
        help="Number of keywords to extract from the RS.",
    )
    parser.add_argument(
        "--top-urls",
        type=int,
        default=None,
        help="Number of URLs to request per query.",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=None,
        help="Similarity threshold for semantic filtering.",
    )
    parser.add_argument(
        "--min-word-count",
        type=int,
        default=None,
        help="Minimum acceptable word count for scraped text.",
    )
    parser.add_argument(
        "--search-backend",
        type=str,
        choices=["ddg", "searxng"],
        default=None,
        help="Search backend to use.",
    )
    parser.add_argument(
        "--searxng-base-url",
        type=str,
        default=None,
        help="Base URL for a self-hosted SearxNG instance.",
    )
    parser.add_argument(
        "--disable-playwright-fallback",
        action="store_true",
        help="Disable Playwright fallback for JS-rendered pages.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        help="Logging level, for example INFO or DEBUG.",
    )

    return parser


def build_settings_from_args(args: argparse.Namespace) -> Settings:
    settings = Settings()

    if args.top_keywords is not None:
        settings.top_keywords = args.top_keywords
    if args.top_urls is not None:
        settings.top_urls_per_keyword = args.top_urls
    if args.similarity_threshold is not None:
        settings.similarity_threshold = args.similarity_threshold
    if args.min_word_count is not None:
        settings.min_word_count = args.min_word_count
    if args.search_backend is not None:
        settings.search_backend = args.search_backend
    if args.searxng_base_url is not None:
        settings.searxng_base_url = args.searxng_base_url
    if args.disable_playwright_fallback:
        settings.enable_playwright_fallback = False
    if args.log_level is not None:
        settings.log_level = args.log_level.upper()

    return settings


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = build_settings_from_args(args)
    pipeline = WebDoMinerPipeline(settings=settings)

    result = pipeline.run(
        input_file=args.input,
        accepted_output_file=args.accepted_output,
        rejected_output_file=args.rejected_output,
        failed_output_file=args.failed_output,
        summary_output_file=args.summary_output,
    )

    print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
    print()
    print(f"Accepted output: {result['accepted_output_file']}")
    print(f"Rejected output: {result['rejected_output_file']}")
    print(f"Failed output:   {result['failed_output_file']}")


if __name__ == "__main__":
    main()