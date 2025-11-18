"""
ChromaDB Vector Store

Manages persistent vector storage using ChromaDB for semantic search.
"""

import uuid
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from loguru import logger
import numpy as np


class ChromaStore:
    """
    ChromaDB-based vector store for RAG system.

    Features:
    - Persistent storage of document embeddings
    - Multiple collections for different content types
    - Metadata filtering
    - Similarity search
    - CRUD operations on documents
    """

    def __init__(
        self,
        persist_directory: str = "./data/vectorstore/chroma",
        collection_name: str = "content",
        embedding_function: Optional[Any] = None
    ):
        """
        Initialize ChromaDB store.

        Args:
            persist_directory: Path to store database
            collection_name: Name of the collection
            embedding_function: Optional custom embedding function
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        logger.info(f"Initializing ChromaDB at {persist_directory}")

        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Create or get collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_function,
                metadata={"description": "X Content RAG System"}
            )

            logger.info(f"ChromaDB initialized with collection: {collection_name}")
            logger.info(f"Collection size: {self.collection.count()} documents")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Add documents to the vector store.

        Args:
            documents: List of text documents
            metadatas: Optional metadata for each document
            ids: Optional custom IDs (generated if not provided)
            embeddings: Optional pre-computed embeddings

        Returns:
            List of document IDs
        """
        if not documents:
            logger.warning("No documents to add")
            return []

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        # Create default metadata if not provided
        if metadatas is None:
            metadatas = [{} for _ in documents]

        try:
            if embeddings:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )

            logger.info(f"Added {len(documents)} documents to collection")
            return ids

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

    def query(
        self,
        query_texts: Union[str, List[str]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        include: List[str] = ["documents", "metadatas", "distances"]
    ) -> Dict[str, Any]:
        """
        Query the vector store for similar documents.

        Args:
            query_texts: Query text(s)
            n_results: Number of results to return per query
            where: Metadata filter
            where_document: Document content filter
            include: What to include in results

        Returns:
            Query results with documents, metadata, and distances
        """
        if isinstance(query_texts, str):
            query_texts = [query_texts]

        try:
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=include
            )

            logger.debug(f"Query returned {len(results['ids'][0])} results")
            return results

        except Exception as e:
            logger.error(f"Error querying documents: {e}")
            raise

    def query_with_embeddings(
        self,
        query_embeddings: Union[List[float], List[List[float]]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        include: List[str] = ["documents", "metadatas", "distances"]
    ) -> Dict[str, Any]:
        """
        Query using pre-computed embeddings.

        Args:
            query_embeddings: Query embedding(s)
            n_results: Number of results to return
            where: Metadata filter
            include: What to include in results

        Returns:
            Query results
        """
        # Ensure embeddings is list of lists
        if isinstance(query_embeddings[0], (int, float)):
            query_embeddings = [query_embeddings]

        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                include=include
            )

            return results

        except Exception as e:
            logger.error(f"Error querying with embeddings: {e}")
            raise

    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        """
        Retrieve documents by their IDs.

        Args:
            ids: List of document IDs

        Returns:
            Documents and their metadata
        """
        try:
            results = self.collection.get(ids=ids)
            return results
        except Exception as e:
            logger.error(f"Error getting documents by IDs: {e}")
            raise

    def update_documents(
        self,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None
    ):
        """
        Update existing documents.

        Args:
            ids: Document IDs to update
            documents: New document texts
            metadatas: New metadata
            embeddings: New embeddings
        """
        try:
            self.collection.update(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            logger.info(f"Updated {len(ids)} documents")
        except Exception as e:
            logger.error(f"Error updating documents: {e}")
            raise

    def delete_documents(self, ids: List[str]):
        """
        Delete documents by IDs.

        Args:
            ids: Document IDs to delete
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise

    def delete_collection(self):
        """Delete the entire collection."""
        try:
            self.client.delete_collection(self.collection_name)
            logger.warning(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise

    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()

    def reset(self):
        """Reset the collection (delete all documents)."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "X Content RAG System"}
            )
            logger.warning(f"Reset collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            raise

    def list_collections(self) -> List[str]:
        """List all collections in the database."""
        collections = self.client.list_collections()
        return [c.name for c in collections]

    def get_collection_metadata(self) -> Dict[str, Any]:
        """Get metadata about the current collection."""
        return {
            "name": self.collection_name,
            "count": self.count(),
            "metadata": self.collection.metadata
        }

    def peek(self, limit: int = 10) -> Dict[str, Any]:
        """
        Peek at the first few documents in the collection.

        Args:
            limit: Number of documents to return

        Returns:
            Sample documents
        """
        return self.collection.peek(limit=limit)

    def __repr__(self) -> str:
        return f"ChromaStore(collection={self.collection_name}, count={self.count()})"


if __name__ == "__main__":
    # Test ChromaDB store
    store = ChromaStore(
        persist_directory="./test_chroma",
        collection_name="test_collection"
    )

    # Add test documents
    documents = [
        "AI is revolutionizing content creation",
        "Machine learning enables personalized experiences",
        "Python is great for data science",
        "ChromaDB is a vector database for AI applications"
    ]

    metadatas = [
        {"category": "AI", "type": "tweet"},
        {"category": "ML", "type": "tweet"},
        {"category": "programming", "type": "tweet"},
        {"category": "databases", "type": "article"}
    ]

    ids = store.add_documents(documents, metadatas=metadatas)
    print(f"Added {len(ids)} documents")

    # Query
    results = store.query("What is AI used for?", n_results=2)
    print("\nQuery results:")
    for doc, dist in zip(results['documents'][0], results['distances'][0]):
        print(f"- {doc} (distance: {dist:.3f})")

    # Filter by metadata
    results = store.query(
        "programming",
        n_results=5,
        where={"category": "AI"}
    )
    print(f"\nFiltered results: {len(results['documents'][0])} documents")

    # Cleanup
    store.delete_collection()
    print("\nTest collection deleted")
