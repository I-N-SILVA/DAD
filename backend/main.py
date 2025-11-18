"""
FastAPI Backend Server

Main entry point for the X Content RAG System API.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
import asyncio

from backend.core.config import get_config
from rag.embeddings.generator import EmbeddingGenerator
from rag.vectorstore.chroma_store import ChromaStore
from rag.retrieval.retriever import ContentRetriever
from rag.indexing.indexer import DocumentIndexer
from integrations.claude.client import ClaudeClient
from content.generation.tweet_generator import TweetGenerator
from automation.schedulers.scheduler import TaskScheduler
from automation.workflows.morning_briefing import run_morning_briefing

# Initialize FastAPI app
app = FastAPI(
    title="X Content RAG System API",
    description="AI-powered content creation system for X/Twitter",
    version="1.0.0"
)

# CORS configuration
config = get_config()
allowed_origins = config.get('security.allowed_origins', [
    "http://localhost:3000",
    "http://localhost:8501"
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components (initialized on startup)
embedding_generator: Optional[EmbeddingGenerator] = None
vector_store: Optional[ChromaStore] = None
content_retriever: Optional[ContentRetriever] = None
document_indexer: Optional[DocumentIndexer] = None
claude_client: Optional[ClaudeClient] = None
tweet_generator: Optional[TweetGenerator] = None
task_scheduler: Optional[TaskScheduler] = None


# Pydantic models
class TweetGenerationRequest(BaseModel):
    topic: str
    num_ideas: int = 5
    temperature: Optional[float] = None


class TweetGenerationResponse(BaseModel):
    ideas: List[Dict[str, Any]]
    generation_time: float


class DocumentIndexRequest(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global embedding_generator, vector_store, content_retriever, document_indexer
    global claude_client, tweet_generator, task_scheduler

    logger.info("Starting X Content RAG System API...")

    try:
        # Load configuration
        config = get_config()

        # Initialize RAG components
        logger.info("Initializing RAG components...")
        embedding_generator = EmbeddingGenerator(
            model_name=config.rag.embedding_model
        )

        vector_store = ChromaStore(
            persist_directory=config.rag.vectorstore_path,
            collection_name="content"
        )

        content_retriever = ContentRetriever(
            vector_store=vector_store,
            embedding_generator=embedding_generator,
            similarity_threshold=config.rag.similarity_threshold
        )

        document_indexer = DocumentIndexer(
            vector_store=vector_store,
            embedding_generator=embedding_generator,
            chunk_size=config.rag.chunk_size,
            chunk_overlap=config.rag.chunk_overlap
        )

        # Initialize Claude client
        logger.info("Initializing Claude client...")
        claude_client = ClaudeClient(
            api_key=config.api_keys.anthropic_api_key,
            model=config.claude.model,
            max_tokens=config.claude.max_tokens,
            temperature=config.claude.temperature
        )

        # Initialize tweet generator
        logger.info("Initializing tweet generator...")
        tweet_generator = TweetGenerator(
            claude_client=claude_client,
            content_retriever=content_retriever,
            config=config.content.tweet_characteristics
        )

        # Initialize scheduler
        logger.info("Initializing task scheduler...")
        task_scheduler = TaskScheduler(
            timezone=config.get('scheduling.timezone', 'UTC')
        )

        # Register scheduled jobs if enabled
        if config.get('scheduling.enabled', False):
            register_scheduled_jobs()
            task_scheduler.start()
            logger.info("Task scheduler started")

        logger.info("✅ All components initialized successfully")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down X Content RAG System API...")

    if task_scheduler:
        task_scheduler.shutdown()

    logger.info("Shutdown complete")


def register_scheduled_jobs():
    """Register scheduled automation jobs."""
    config = get_config()
    jobs = config.get('scheduling.jobs', {})

    # Morning briefing
    if jobs.get('morning_briefing', {}).get('enabled', False):
        cron = jobs['morning_briefing']['cron']
        task_scheduler.add_cron_job(
            run_morning_briefing_wrapper,
            job_id="morning_briefing",
            cron_expression=cron,
            description="Morning content briefing"
        )
        logger.info(f"Registered morning briefing job: {cron}")

    # Add more jobs as needed
    logger.info(f"Registered {len(task_scheduler.list_jobs())} scheduled jobs")


async def run_morning_briefing_wrapper():
    """Wrapper for morning briefing workflow."""
    try:
        logger.info("Running scheduled morning briefing...")
        briefing = await run_morning_briefing()
        logger.info("Morning briefing completed successfully")
        return briefing
    except Exception as e:
        logger.error(f"Error in morning briefing: {e}")


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "X Content RAG System API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "rag": vector_store is not None,
            "claude": claude_client is not None,
            "scheduler": task_scheduler is not None
        },
        "documents": vector_store.count() if vector_store else 0,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/generate/tweets", response_model=TweetGenerationResponse)
async def generate_tweets(request: TweetGenerationRequest):
    """Generate tweet ideas."""
    start_time = datetime.now()

    try:
        logger.info(f"Generating {request.num_ideas} tweet ideas for: {request.topic}")

        ideas = await tweet_generator.generate_tweet_ideas_async(
            topic=request.topic,
            num_ideas=request.num_ideas
        )

        ideas_data = [
            {
                "content": idea.content,
                "rationale": idea.rationale,
                "confidence": idea.confidence,
                "hashtags": idea.hashtags,
                "category": idea.category
            }
            for idea in ideas
        ]

        generation_time = (datetime.now() - start_time).total_seconds()

        return TweetGenerationResponse(
            ideas=ideas_data,
            generation_time=generation_time
        )

    except Exception as e:
        logger.error(f"Error generating tweets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index/document")
async def index_document(request: DocumentIndexRequest):
    """Index a document in the knowledge base."""
    try:
        doc_id = document_indexer.index_document(
            content=request.content,
            metadata=request.metadata
        )

        return {
            "success": True,
            "document_id": doc_id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error indexing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search_knowledge_base(request: SearchRequest):
    """Search the knowledge base."""
    try:
        results = content_retriever.retrieve(
            query=request.query,
            top_k=request.top_k
        )

        results_data = [
            {
                "document": result.document,
                "score": result.score,
                "metadata": result.metadata
            }
            for result in results
        ]

        return SearchResponse(results=results_data)

    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_statistics():
    """Get system statistics."""
    return {
        "knowledge_base": {
            "total_documents": vector_store.count() if vector_store else 0,
            "embedding_model": config.rag.embedding_model
        },
        "scheduler": {
            "running": task_scheduler.scheduler.running if task_scheduler else False,
            "jobs": len(task_scheduler.list_jobs()) if task_scheduler else 0
        },
        "api": {
            "tokens_used": claude_client.get_token_usage() if claude_client else 0
        },
        "timestamp": datetime.now().isoformat()
    }


@app.post("/workflows/morning-briefing")
async def trigger_morning_briefing():
    """Manually trigger morning briefing workflow."""
    try:
        logger.info("Manually triggering morning briefing...")
        briefing = await run_morning_briefing()

        return {
            "success": True,
            "briefing": briefing,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error running morning briefing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scheduler/jobs")
async def list_scheduled_jobs():
    """List all scheduled jobs."""
    if not task_scheduler:
        return {"jobs": []}

    jobs = task_scheduler.list_jobs()

    return {
        "jobs": [
            {
                "id": job_id,
                "type": info["type"],
                "description": info["description"],
                "schedule": info.get("expression") or info.get("interval")
            }
            for job_id, info in jobs.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn

    # Get server config
    host = config.get('server.host', '0.0.0.0')
    port = config.get('server.port', 8000)
    reload = config.get('server.reload', False)

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
