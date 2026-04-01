from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

from webdominer.settings import Settings


@dataclass(slots=True)
class EmbeddingBatchResult:
    """
    Holds embedding vectors for a batch of texts.
    """

    texts_count: int
    vectors: np.ndarray


class EmbeddingService:
    """
    Local embedding service built on SentenceTransformers.

    This service loads the model once and reuses it across the pipeline.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model = SentenceTransformer(settings.embedding_model_name)

    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed one text and return a 1D normalized vector.
        """
        vector = self.model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        return vector

    def embed_texts(self, texts: Sequence[str]) -> EmbeddingBatchResult:
        """
        Embed multiple texts and return normalized vectors.
        """
        if not texts:
            return EmbeddingBatchResult(
                texts_count=0,
                vectors=np.empty((0, 0), dtype=np.float32),
            )

        vectors = self.model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return EmbeddingBatchResult(
            texts_count=len(texts),
            vectors=vectors,
        )