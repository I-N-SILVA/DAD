"""
Document Indexer

Handles ingestion, processing, and indexing of documents into the RAG system.
"""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from rag.embeddings.generator import EmbeddingGenerator
from rag.vectorstore.chroma_store import ChromaStore


@dataclass
class Document:
    """Document container with content and metadata."""
    content: str
    metadata: Dict[str, Any]
    id: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())


class DocumentIndexer:
    """
    Indexes documents into the RAG system.

    Features:
    - Text chunking for long documents
    - Metadata extraction and enrichment
    - Batch processing
    - Progress tracking
    - Deduplication
    """

    def __init__(
        self,
        vector_store: ChromaStore,
        embedding_generator: EmbeddingGenerator,
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ):
        """
        Initialize the document indexer.

        Args:
            vector_store: ChromaDB vector store
            embedding_generator: Embedding generator
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        logger.info("DocumentIndexer initialized")

    def index_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        Index a single document.

        Args:
            content: Document content
            metadata: Document metadata
            doc_id: Optional document ID

        Returns:
            Document ID
        """
        if metadata is None:
            metadata = {}

        # Add timestamp if not present
        if 'timestamp' not in metadata:
            metadata['timestamp'] = datetime.now().isoformat()

        # Generate ID if not provided
        if doc_id is None:
            doc_id = str(uuid.uuid4())

        # Add content length to metadata
        metadata['length'] = len(content)

        try:
            # Add to vector store
            self.vector_store.add_documents(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )

            logger.info(f"Indexed document: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            raise

    def index_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> List[str]:
        """
        Index multiple documents in batches.

        Args:
            documents: List of Document objects
            batch_size: Number of documents per batch

        Returns:
            List of document IDs
        """
        logger.info(f"Indexing {len(documents)} documents...")

        all_ids = []

        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            contents = [doc.content for doc in batch]
            metadatas = [doc.metadata for doc in batch]
            ids = [doc.id for doc in batch]

            # Add timestamp to metadata if not present
            for metadata in metadatas:
                if 'timestamp' not in metadata:
                    metadata['timestamp'] = datetime.now().isoformat()

            try:
                batch_ids = self.vector_store.add_documents(
                    documents=contents,
                    metadatas=metadatas,
                    ids=ids
                )

                all_ids.extend(batch_ids)
                logger.info(f"Indexed batch {i // batch_size + 1}: {len(batch)} documents")

            except Exception as e:
                logger.error(f"Error indexing batch {i // batch_size + 1}: {e}")
                raise

        logger.info(f"Successfully indexed {len(all_ids)} documents")
        return all_ids

    def index_long_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> List[str]:
        """
        Index a long document by splitting it into chunks.

        Args:
            content: Document content
            metadata: Document metadata
            doc_id: Optional parent document ID

        Returns:
            List of chunk IDs
        """
        if metadata is None:
            metadata = {}

        # Generate parent ID if not provided
        if doc_id is None:
            doc_id = str(uuid.uuid4())

        # Split into chunks
        chunks = self._chunk_text(content)

        logger.info(f"Split document {doc_id} into {len(chunks)} chunks")

        # Create chunk documents
        chunk_docs = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'parent_id': doc_id,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'is_chunk': True
            })

            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_docs.append(Document(
                content=chunk,
                metadata=chunk_metadata,
                id=chunk_id
            ))

        # Index chunks
        return self.index_documents(chunk_docs)

    def index_from_file(
        self,
        file_path: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Index content from a file.

        Supports: .txt, .md, .json, .jsonl

        Args:
            file_path: Path to file
            metadata: Additional metadata

        Returns:
            List of indexed document IDs
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Indexing file: {file_path}")

        if metadata is None:
            metadata = {}

        # Add file metadata
        metadata.update({
            'source': str(file_path),
            'filename': file_path.name,
            'file_type': file_path.suffix
        })

        # Read and index based on file type
        if file_path.suffix in ['.txt', '.md']:
            content = file_path.read_text(encoding='utf-8')
            if len(content) > self.chunk_size:
                return self.index_long_document(content, metadata)
            else:
                doc_id = self.index_document(content, metadata)
                return [doc_id]

        elif file_path.suffix == '.json':
            data = json.loads(file_path.read_text(encoding='utf-8'))
            if isinstance(data, list):
                # List of documents
                documents = [
                    Document(
                        content=item.get('content', item.get('text', str(item))),
                        metadata={**metadata, **item.get('metadata', {})}
                    )
                    for item in data
                ]
                return self.index_documents(documents)
            else:
                # Single document
                content = data.get('content', data.get('text', json.dumps(data)))
                return [self.index_document(content, metadata)]

        elif file_path.suffix == '.jsonl':
            documents = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    item = json.loads(line)
                    documents.append(Document(
                        content=item.get('content', item.get('text', str(item))),
                        metadata={**metadata, **item.get('metadata', {})}
                    ))
            return self.index_documents(documents)

        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

    def index_from_directory(
        self,
        directory: Union[str, Path],
        recursive: bool = True,
        file_patterns: List[str] = None
    ) -> Dict[str, Any]:
        """
        Index all supported files in a directory.

        Args:
            directory: Directory path
            recursive: Whether to search recursively
            file_patterns: File patterns to match (e.g., ['*.txt', '*.md'])

        Returns:
            Indexing statistics
        """
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        logger.info(f"Indexing directory: {directory}")

        if file_patterns is None:
            file_patterns = ['*.txt', '*.md', '*.json', '*.jsonl']

        # Find files
        files = []
        for pattern in file_patterns:
            if recursive:
                files.extend(directory.rglob(pattern))
            else:
                files.extend(directory.glob(pattern))

        logger.info(f"Found {len(files)} files to index")

        # Index files
        stats = {
            'total_files': len(files),
            'indexed_files': 0,
            'failed_files': 0,
            'total_documents': 0,
            'errors': []
        }

        for file_path in files:
            try:
                doc_ids = self.index_from_file(file_path)
                stats['indexed_files'] += 1
                stats['total_documents'] += len(doc_ids)
            except Exception as e:
                stats['failed_files'] += 1
                stats['errors'].append({
                    'file': str(file_path),
                    'error': str(e)
                })
                logger.error(f"Failed to index {file_path}: {e}")

        logger.info(f"Indexing complete: {stats['indexed_files']}/{stats['total_files']} files")
        return stats

    def index_tweets(
        self,
        tweets: List[Dict[str, Any]],
        include_metadata: bool = True
    ) -> List[str]:
        """
        Index tweets with proper metadata.

        Args:
            tweets: List of tweet dictionaries
            include_metadata: Whether to include tweet metadata

        Returns:
            List of indexed tweet IDs
        """
        documents = []

        for tweet in tweets:
            content = tweet.get('text', tweet.get('content', ''))

            metadata = {
                'type': 'tweet',
                'timestamp': tweet.get('created_at', datetime.now().isoformat())
            }

            if include_metadata:
                metadata.update({
                    'tweet_id': tweet.get('id'),
                    'likes': tweet.get('likes', tweet.get('favorite_count', 0)),
                    'retweets': tweet.get('retweets', tweet.get('retweet_count', 0)),
                    'replies': tweet.get('replies', tweet.get('reply_count', 0)),
                    'engagement': sum([
                        tweet.get('likes', 0),
                        tweet.get('retweets', 0),
                        tweet.get('replies', 0)
                    ])
                })

            documents.append(Document(
                content=content,
                metadata=metadata,
                id=tweet.get('id', str(uuid.uuid4()))
            ))

        return self.index_documents(documents)

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                boundary_window = text[end - 50:end + 50] if end + 50 < len(text) else text[end - 50:]
                sentence_ends = ['.', '!', '?', '\n']

                best_break = None
                for char in sentence_ends:
                    pos = boundary_window.rfind(char)
                    if pos != -1:
                        best_break = (end - 50) + pos + 1
                        break

                if best_break:
                    end = best_break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap

        return chunks

    def remove_document(self, doc_id: str):
        """Remove a document from the index."""
        self.vector_store.delete_documents([doc_id])
        logger.info(f"Removed document: {doc_id}")

    def update_document(
        self,
        doc_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update an existing document."""
        self.vector_store.update_documents(
            ids=[doc_id],
            documents=[content] if content else None,
            metadatas=[metadata] if metadata else None
        )
        logger.info(f"Updated document: {doc_id}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get indexing statistics."""
        return {
            'total_documents': self.vector_store.count(),
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap
        }


if __name__ == "__main__":
    # Test the indexer
    from rag.vectorstore.chroma_store import ChromaStore
    from rag.embeddings.generator import EmbeddingGenerator

    generator = EmbeddingGenerator()
    store = ChromaStore(
        persist_directory="./test_chroma",
        collection_name="test_indexing"
    )

    indexer = DocumentIndexer(
        vector_store=store,
        embedding_generator=generator,
        chunk_size=200,
        chunk_overlap=20
    )

    # Test single document indexing
    doc_id = indexer.index_document(
        content="This is a test tweet about AI and machine learning.",
        metadata={"type": "tweet", "category": "AI"}
    )
    print(f"Indexed document: {doc_id}")

    # Test long document chunking
    long_text = " ".join([f"Sentence {i} about artificial intelligence." for i in range(50)])
    chunk_ids = indexer.index_long_document(
        content=long_text,
        metadata={"type": "article", "title": "AI Article"}
    )
    print(f"Indexed long document: {len(chunk_ids)} chunks")

    # Test tweet indexing
    tweets = [
        {"id": "1", "text": "AI is amazing!", "likes": 100, "retweets": 50},
        {"id": "2", "text": "Python for data science", "likes": 75, "retweets": 30},
    ]
    tweet_ids = indexer.index_tweets(tweets)
    print(f"Indexed {len(tweet_ids)} tweets")

    # Get statistics
    stats = indexer.get_statistics()
    print(f"\nStatistics: {stats}")

    # Cleanup
    store.delete_collection()
