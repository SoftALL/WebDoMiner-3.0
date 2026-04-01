from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from webdominer.io.loader import load_rs_text
from webdominer.io.writer import write_json, write_jsonl
from webdominer.logging_utils import configure_logging, get_logger
from webdominer.models import (
    FailedPage,
    PipelineSummary,
    RejectedPage,
)
from webdominer.retrieval.discovery import UrlDiscoveryService
from webdominer.retrieval.keywording import KeywordExtractor
from webdominer.retrieval.query_builder import QueryBuilder
from webdominer.retrieval.search_clients import create_search_client
from webdominer.scraping.scraper import ScraperService
from webdominer.semantic.embeddings import EmbeddingService
from webdominer.semantic.similarity import SemanticFilterService
from webdominer.settings import Settings


class WebDoMinerPipeline:
    """
    End-to-end pipeline for generating an open-web domain corpus
    from a requirements specification (RS) document.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.settings.ensure_directories()
        configure_logging(self.settings)
        self.logger = get_logger(__name__)

        self.keyword_extractor = KeywordExtractor()
        self.query_builder = QueryBuilder()
        self.search_client = create_search_client(self.settings)
        self.discovery_service = UrlDiscoveryService(self.settings, self.search_client)
        self.scraper_service = ScraperService(self.settings)
        self.embedding_service = EmbeddingService(self.settings)
        self.semantic_filter_service = SemanticFilterService(
            self.settings,
            self.embedding_service,
        )

    def run(
        self,
        input_file: str | Path | None = None,
        accepted_output_file: str | Path | None = None,
        rejected_output_file: str | Path | None = None,
        failed_output_file: str | Path | None = None,
        summary_output_file: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Run the full pipeline and return a structured summary dictionary.
        """
        summary = PipelineSummary()

        input_path = Path(input_file) if input_file else self.settings.default_input_file
        accepted_path = (
            Path(accepted_output_file)
            if accepted_output_file
            else self.settings.accepted_output_file
        )
        rejected_path = (
            Path(rejected_output_file)
            if rejected_output_file
            else self.settings.rejected_output_file
        )
        failed_path = (
            Path(failed_output_file)
            if failed_output_file
            else self.settings.failed_output_file
        )
        summary_path = (
            Path(summary_output_file)
            if summary_output_file
            else self.settings.data_output_dir / "summary.json"
        )

        self.logger.info("Starting WebDoMiner pipeline.")
        self.logger.info("Loading RS document from: %s", input_path)

        rs_text = load_rs_text(input_path)

        self.logger.info("Extracting keywords.")
        keyword_candidates = self.keyword_extractor.extract_keywords(
            rs_text,
            top_n=self.settings.top_keywords,
        )
        keywords = [item.phrase for item in keyword_candidates]
        summary.keywords_extracted = len(keywords)

        self.logger.info("Extracted %d keywords.", len(keywords))
        self.logger.debug("Keywords: %s", keywords)

        self.logger.info("Building search queries.")
        search_queries = self.query_builder.build_queries(keywords)
        self.logger.info("Built %d search queries.", len(search_queries))

        self.logger.info("Running discovery stage.")
        raw_results, discovered_urls, discovery_failures = (
            self.discovery_service.search_and_discover(search_queries)
        )
        summary.raw_search_results = len(raw_results)
        summary.unique_urls_discovered = len(discovered_urls)

        self.logger.info("Raw search results: %d", len(raw_results))
        self.logger.info("Unique discovered URLs: %d", len(discovered_urls))
        self.logger.info("Discovery failures: %d", len(discovery_failures))

        self.logger.info("Running scraping stage.")
        scraped_pages, scraping_rejections, scraping_failures = (
            self.scraper_service.scrape_urls(discovered_urls)
        )
        summary.pages_scraped_successfully = len(scraped_pages)

        self.logger.info("Scraped acceptable pages: %d", len(scraped_pages))
        self.logger.info("Scraping rejections: %d", len(scraping_rejections))
        self.logger.info("Scraping failures: %d", len(scraping_failures))

        self.logger.info("Running semantic filtering stage.")
        semantic_result = self.semantic_filter_service.filter_pages(rs_text, scraped_pages)
        accepted_documents = semantic_result.accepted_documents
        semantic_rejections = semantic_result.rejected_pages

        summary.final_accepted_documents = len(accepted_documents)
        summary.pages_rejected = len(scraping_rejections) + len(semantic_rejections)
        summary.pages_failed = len(discovery_failures) + len(scraping_failures)
        summary.mark_finished()

        all_rejected_pages: list[RejectedPage] = [
            *scraping_rejections,
            *semantic_rejections,
        ]
        all_failed_pages: list[FailedPage] = [
            *discovery_failures,
            *scraping_failures,
        ]

        self.logger.info("Writing output files.")
        accepted_count = write_jsonl(accepted_documents, accepted_path)
        rejected_count = write_jsonl(all_rejected_pages, rejected_path)
        failed_count = write_jsonl(all_failed_pages, failed_path)

        keyword_preview = [item.to_dict() for item in keyword_candidates]
        query_preview = [item.to_dict() for item in search_queries[: min(25, len(search_queries))]]

        summary_payload = {
            "summary": summary.to_dict(),
            "input_file": str(input_path),
            "accepted_output_file": str(accepted_path),
            "rejected_output_file": str(rejected_path),
            "failed_output_file": str(failed_path),
            "keywords": keyword_preview,
            "query_preview": query_preview,
            "counts_written": {
                "accepted": accepted_count,
                "rejected": rejected_count,
                "failed": failed_count,
            },
        }
        write_json(summary_payload, summary_path)

        self.logger.info("Pipeline finished.")
        self.logger.info("Accepted: %d", accepted_count)
        self.logger.info("Rejected: %d", rejected_count)
        self.logger.info("Failed: %d", failed_count)

        return summary_payload