"""
Content Retriever

Semantic search and retrieval system for finding relevant content from the knowledge base.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from rag.embeddings.generator import EmbeddingGenerator
from rag.vectorstore.chroma_store import ChromaStore


@dataclass
class RetrievalResult:
    """Container for a single retrieval result."""
    document: str
    metadata: Dict[str, Any]
    score: float  # Similarity score (lower distance = higher score)
    id: str


class ContentRetriever:
    """
    Retrieves relevant content from the knowledge base using semantic search.

    Features:
    - Semantic similarity search
    - Metadata filtering
    - Result re-ranking
    - Context window management
    - Hybrid search (semantic + keyword)
    """

    def __init__(
        self,
        vector_store: ChromaStore,
        embedding_generator: EmbeddingGenerator,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize the content retriever.

        Args:
            vector_store: ChromaDB vector store
            embedding_generator: Embedding generator
            similarity_threshold: Minimum similarity score for results
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.similarity_threshold = similarity_threshold

        logger.info("ContentRetriever initialized")

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = True
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant content for a query.

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Metadata filters
            rerank: Whether to re-rank results

        Returns:
            List of retrieval results sorted by relevance
        """
        logger.debug(f"Retrieving content for query: {query[:100]}...")

        try:
            # Query vector store
            results = self.vector_store.query(
                query_texts=query,
                n_results=top_k * 2 if rerank else top_k,  # Fetch more if re-ranking
                where=filters,
                include=["documents", "metadatas", "distances"]
            )

            # Convert to RetrievalResult objects
            retrieval_results = []
            for i, (doc, metadata, distance, doc_id) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0],
                results['ids'][0]
            )):
                # Convert distance to similarity score (1 - normalized distance)
                # Assuming distance is already normalized by ChromaDB
                score = 1 - distance

                # Filter by similarity threshold
                if score >= self.similarity_threshold:
                    retrieval_results.append(RetrievalResult(
                        document=doc,
                        metadata=metadata,
                        score=score,
                        id=doc_id
                    ))

            # Re-rank if requested
            if rerank and retrieval_results:
                retrieval_results = self._rerank_results(query, retrieval_results)

            # Return top_k results
            retrieval_results = retrieval_results[:top_k]

            logger.info(f"Retrieved {len(retrieval_results)} relevant documents")
            return retrieval_results

        except Exception as e:
            logger.error(f"Error retrieving content: {e}")
            raise

    def retrieve_by_category(
        self,
        query: str,
        category: str,
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        Retrieve content filtered by category.

        Args:
            query: Search query
            category: Category to filter by
            top_k: Number of results

        Returns:
            Filtered retrieval results
        """
        return self.retrieve(
            query=query,
            top_k=top_k,
            filters={"category": category}
        )

    def retrieve_recent(
        self,
        query: str,
        days: int = 7,
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        Retrieve recent content (within specified days).

        Args:
            query: Search query
            days: Number of days to look back
            top_k: Number of results

        Returns:
            Recent retrieval results
        """
        # Note: This requires timestamp metadata in documents
        # For now, we'll retrieve and filter post-query
        results = self.retrieve(query=query, top_k=top_k * 2)

        # Filter by date if timestamp exists in metadata
        recent_results = []
        for result in results:
            if 'timestamp' in result.metadata:
                try:
                    doc_date = datetime.fromisoformat(result.metadata['timestamp'])
                    age_days = (datetime.now() - doc_date).days
                    if age_days <= days:
                        recent_results.append(result)
                except Exception:
                    # If timestamp parsing fails, include the document
                    recent_results.append(result)
            else:
                # If no timestamp, include the document
                recent_results.append(result)

        return recent_results[:top_k]

    def retrieve_similar_to_document(
        self,
        document_id: str,
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        Find documents similar to a given document.

        Args:
            document_id: ID of the source document
            top_k: Number of similar documents to return

        Returns:
            Similar documents
        """
        # Get the source document
        doc_data = self.vector_store.get_by_ids([document_id])

        if not doc_data['documents']:
            logger.warning(f"Document {document_id} not found")
            return []

        source_doc = doc_data['documents'][0]

        # Find similar documents
        return self.retrieve(query=source_doc, top_k=top_k + 1)[1:]  # Exclude self

    def retrieve_for_context(
        self,
        query: str,
        max_tokens: int = 2000,
        top_k: int = 10
    ) -> str:
        """
        Retrieve and format content for use as context in generation.

        Args:
            query: Search query
            max_tokens: Maximum tokens for context (approximate)
            top_k: Number of documents to consider

        Returns:
            Formatted context string
        """
        results = self.retrieve(query=query, top_k=top_k)

        if not results:
            return ""

        # Build context string within token limit
        context_parts = []
        current_tokens = 0
        max_chars = max_tokens * 4  # Rough approximation: 1 token ≈ 4 chars

        for i, result in enumerate(results, 1):
            # Format: [Source 1] Content...
            part = f"[Source {i}] {result.document}\n"

            if current_tokens + len(part) > max_chars:
                break

            context_parts.append(part)
            current_tokens += len(part)

        context = "\n".join(context_parts)
        logger.debug(f"Built context with {len(context_parts)} sources (~{current_tokens} chars)")

        return context

    def _rerank_results(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        Re-rank results using additional signals.

        This can be extended with:
        - Cross-encoder models
        - Recency boosting
        - Engagement metrics
        - Content quality signals
        """
        # For now, implement simple recency and metadata boosting
        for result in results:
            boost = 0.0

            # Boost recent content
            if 'timestamp' in result.metadata:
                try:
                    doc_date = datetime.fromisoformat(result.metadata['timestamp'])
                    age_days = (datetime.now() - doc_date).days
                    recency_boost = max(0, 0.1 * (1 - age_days / 365))  # Up to 0.1 boost
                    boost += recency_boost
                except Exception:
                    pass

            # Boost high-engagement content
            if 'engagement' in result.metadata:
                engagement = result.metadata['engagement']
                engagement_boost = min(0.1, engagement / 1000)  # Up to 0.1 boost
                boost += engagement_boost

            # Boost content marked as high quality
            if result.metadata.get('quality') == 'high':
                boost += 0.05

            # Apply boost to score
            result.score = min(1.0, result.score + boost)

        # Re-sort by adjusted score
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        return {
            "total_documents": self.vector_store.count(),
            "similarity_threshold": self.similarity_threshold,
            "embedding_model": self.embedding_generator.model_name,
            "cache_size": self.embedding_generator.get_cache_size()
        }

    def __repr__(self) -> str:
        return f"ContentRetriever(docs={self.vector_store.count()}, threshold={self.similarity_threshold})"


if __name__ == "__main__":
    # Test the retriever
    from rag.vectorstore.chroma_store import ChromaStore
    from rag.embeddings.generator import EmbeddingGenerator

    # Initialize components
    generator = EmbeddingGenerator()
    store = ChromaStore(
        persist_directory="./test_chroma",
        collection_name="test_retrieval"
    )

    # Add test documents
    documents = [
        "AI and machine learning are transforming content creation",
        "Python is the best language for data science and AI",
        "ChromaDB is a vector database optimized for AI applications",
        "Semantic search uses embeddings to find similar content",
        "The weather today is sunny and warm"
    ]

    metadatas = [
        {"category": "AI", "timestamp": "2025-01-15T10:00:00"},
        {"category": "programming", "timestamp": "2025-01-14T09:00:00"},
        {"category": "databases", "timestamp": "2025-01-13T08:00:00"},
        {"category": "AI", "timestamp": "2025-01-16T11:00:00"},
        {"category": "weather", "timestamp": "2025-01-17T12:00:00"}
    ]

    store.add_documents(documents, metadatas=metadatas)

    # Initialize retriever
    retriever = ContentRetriever(
        vector_store=store,
        embedding_generator=generator,
        similarity_threshold=0.5
    )

    # Test retrieval
    print("Query: 'artificial intelligence'")
    results = retriever.retrieve("artificial intelligence", top_k=3)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.3f}")
        print(f"   Document: {result.document}")
        print(f"   Metadata: {result.metadata}")

    # Test category filtering
    print("\n\nQuery with category filter: 'programming'")
    results = retriever.retrieve_by_category("programming", "AI", top_k=2)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.document}")

    # Test context building
    print("\n\nContext for generation:")
    context = retriever.retrieve_for_context("AI and databases", max_tokens=500)
    print(context)

    # Cleanup
    store.delete_collection()
