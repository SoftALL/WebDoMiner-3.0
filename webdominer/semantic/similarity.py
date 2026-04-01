from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from webdominer.models import CorpusDocument, RejectedPage, ScrapedPage
from webdominer.semantic.embeddings import EmbeddingService
from webdominer.settings import Settings


@dataclass(slots=True)
class SemanticFilterResult:
    """
    Holds accepted and rejected semantic-filtering outputs.
    """

    accepted_documents: list[CorpusDocument]
    rejected_pages: list[RejectedPage]


def cosine_similarity(normalized_vector_a: np.ndarray, normalized_vector_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two normalized vectors.

    Since vectors are normalized already, cosine similarity is just their dot product.
    """
    return float(np.dot(normalized_vector_a, normalized_vector_b))


class SemanticFilterService:
    """
    Final semantic relevance filter for scraped pages.
    """

    def __init__(self, settings: Settings, embedding_service: EmbeddingService) -> None:
        self.settings = settings
        self.embedding_service = embedding_service

    def filter_pages(
        self,
        rs_text: str,
        scraped_pages: Iterable[ScrapedPage],
    ) -> SemanticFilterResult:
        """
        Compare each scraped page against the RS document embedding and
        split pages into accepted vs rejected outputs.
        """
        page_list = list(scraped_pages)

        if not page_list:
            return SemanticFilterResult(
                accepted_documents=[],
                rejected_pages=[],
            )

        rs_vector = self.embedding_service.embed_text(rs_text)

        page_texts = [page.text for page in page_list]
        batch_result = self.embedding_service.embed_texts(page_texts)

        accepted_documents: list[CorpusDocument] = []
        rejected_pages: list[RejectedPage] = []

        for page, page_vector in zip(page_list, batch_result.vectors):
            similarity_score = cosine_similarity(rs_vector, page_vector)
            rounded_score = round(similarity_score, 4)

            if similarity_score >= self.settings.similarity_threshold:
                accepted_documents.append(
                    CorpusDocument(
                        source_url=page.url,
                        matched_keyword=page.matched_keyword,
                        similarity_score=rounded_score,
                        text=page.text,
                        title=page.title,
                        query=page.query,
                        extraction_method=page.extraction_method,
                        timestamp=page.timestamp,
                    )
                )
            else:
                rejected_pages.append(
                    RejectedPage(
                        url=page.url,
                        reason=f"below_similarity_threshold:{rounded_score}",
                        matched_keyword=page.matched_keyword,
                        query=page.query,
                        title=page.title,
                        similarity_score=rounded_score,
                        extraction_method=page.extraction_method,
                        timestamp=page.timestamp,
                    )
                )

        accepted_documents.sort(
            key=lambda doc: (-doc.similarity_score, doc.source_url)
        )

        rejected_pages.sort(
            key=lambda page: (
                -(page.similarity_score if page.similarity_score is not None else -1.0),
                page.url,
            )
        )

        return SemanticFilterResult(
            accepted_documents=accepted_documents,
            rejected_pages=rejected_pages,
        )