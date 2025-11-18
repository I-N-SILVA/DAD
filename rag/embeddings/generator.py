"""
Embedding Generator

Generates embeddings for text content using sentence-transformers.
Supports multiple embedding models and batch processing.
"""

import asyncio
from typing import List, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger


class EmbeddingGenerator:
    """
    Generates embeddings for text content using pre-trained models.

    Supports:
    - Multiple embedding models
    - Batch processing for efficiency
    - Caching for repeated queries
    - Async operations
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        cache_enabled: bool = True
    ):
        """
        Initialize the embedding generator.

        Args:
            model_name: HuggingFace model identifier
            device: Device to run model on ('cpu', 'cuda', 'mps')
            cache_enabled: Whether to cache embeddings
        """
        self.model_name = model_name
        self.device = device
        self.cache_enabled = cache_enabled
        self._cache = {} if cache_enabled else None

        logger.info(f"Loading embedding model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name, device=device)
            logger.info(f"Successfully loaded model on {device}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def generate(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text(s).

        Args:
            text: Single text string or list of texts

        Returns:
            Numpy array of embeddings (single vector or batch)
        """
        # Convert single text to list
        is_single = isinstance(text, str)
        texts = [text] if is_single else text

        # Check cache
        if self.cache_enabled:
            uncached_texts = []
            uncached_indices = []
            cached_embeddings = []

            for i, t in enumerate(texts):
                if t in self._cache:
                    cached_embeddings.append((i, self._cache[t]))
                else:
                    uncached_texts.append(t)
                    uncached_indices.append(i)

            # Generate embeddings for uncached texts
            if uncached_texts:
                new_embeddings = self._generate_batch(uncached_texts)

                # Cache new embeddings
                for t, emb in zip(uncached_texts, new_embeddings):
                    self._cache[t] = emb

                # Combine cached and new embeddings
                all_embeddings = [None] * len(texts)
                for i, emb in cached_embeddings:
                    all_embeddings[i] = emb
                for i, emb in zip(uncached_indices, new_embeddings):
                    all_embeddings[i] = emb

                embeddings = np.array(all_embeddings)
            else:
                # All from cache
                embeddings = np.array([emb for _, emb in sorted(cached_embeddings)])
        else:
            embeddings = self._generate_batch(texts)

        # Return single vector if input was single text
        return embeddings[0] if is_single else embeddings

    def _generate_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a batch of texts."""
        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=32
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    async def generate_async(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Async version of generate().

        Runs embedding generation in thread pool to avoid blocking.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, text)

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        return self.model.get_sentence_embedding_dimension()

    def clear_cache(self):
        """Clear the embedding cache."""
        if self.cache_enabled:
            self._cache.clear()
            logger.info("Embedding cache cleared")

    def get_cache_size(self) -> int:
        """Get the number of cached embeddings."""
        return len(self._cache) if self.cache_enabled else 0

    def similarity(
        self,
        text1: Union[str, np.ndarray],
        text2: Union[str, np.ndarray]
    ) -> float:
        """
        Calculate cosine similarity between two texts or embeddings.

        Args:
            text1: Text string or embedding vector
            text2: Text string or embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        # Generate embeddings if inputs are strings
        emb1 = self.generate(text1) if isinstance(text1, str) else text1
        emb2 = self.generate(text2) if isinstance(text2, str) else text2

        # Calculate cosine similarity
        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))

    def batch_similarity(
        self,
        query: Union[str, np.ndarray],
        candidates: Union[List[str], np.ndarray]
    ) -> List[float]:
        """
        Calculate similarity between query and multiple candidates.

        Args:
            query: Query text or embedding
            candidates: List of candidate texts or embeddings matrix

        Returns:
            List of similarity scores
        """
        query_emb = self.generate(query) if isinstance(query, str) else query

        if isinstance(candidates, list) and isinstance(candidates[0], str):
            candidate_embs = self.generate(candidates)
        else:
            candidate_embs = candidates

        # Vectorized cosine similarity
        similarities = np.dot(candidate_embs, query_emb) / (
            np.linalg.norm(candidate_embs, axis=1) * np.linalg.norm(query_emb)
        )

        return similarities.tolist()

    def __repr__(self) -> str:
        return f"EmbeddingGenerator(model={self.model_name}, device={self.device})"


if __name__ == "__main__":
    # Test the embedding generator
    generator = EmbeddingGenerator()

    # Test single text
    text = "This is a test tweet about AI and machine learning."
    embedding = generator.generate(text)
    print(f"Embedding dimension: {len(embedding)}")

    # Test batch
    texts = [
        "AI is transforming the world",
        "Machine learning powers modern applications",
        "The weather is nice today"
    ]
    embeddings = generator.generate(texts)
    print(f"Batch embeddings shape: {embeddings.shape}")

    # Test similarity
    sim = generator.similarity(texts[0], texts[1])
    print(f"Similarity between first two texts: {sim:.3f}")

    sim2 = generator.similarity(texts[0], texts[2])
    print(f"Similarity between first and third: {sim2:.3f}")
