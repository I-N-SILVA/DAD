# Development Guide

Guide for developers who want to customize, extend, or contribute to the X Content RAG System.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend Layer                      │
│  ┌──────────────┐              ┌──────────────────────┐ │
│  │   Streamlit  │              │   External Apps      │ │
│  │   Dashboard  │◄────────────►│   (Future: React)    │ │
│  └──────────────┘              └──────────────────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────┐
│                    FastAPI Backend                       │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────┐ │
│  │  API Routes   │  │  Auth/Security │  │  Webhooks  │ │
│  └───────────────┘  └────────────────┘  └────────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                    Business Logic                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │   RAG    │  │  Content │  │  Browser │  │ Twitter ││
│  │  System  │  │Generator │  │Automation│  │   API   ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                    Data Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │ ChromaDB │  │  SQLite  │  │  Files   │  │  Cache  ││
│  │ (Vectors)│  │  (Logs)  │  │  (Docs)  │  │ (Redis) ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└─────────────────────────────────────────────────────────┘
```

## Module Structure

### RAG System (`rag/`)

**Purpose:** Retrieval-Augmented Generation engine

**Key Components:**
- `embeddings/generator.py` - Text embedding generation
- `vectorstore/chroma_store.py` - Vector database interface
- `retrieval/retriever.py` - Semantic search
- `indexing/indexer.py` - Document ingestion

**Extension Points:**
```python
# Add custom embedding model
class CustomEmbedding(EmbeddingGenerator):
    def __init__(self):
        super().__init__(model_name="your-model")

# Add custom retrieval logic
class CustomRetriever(ContentRetriever):
    def retrieve(self, query, **kwargs):
        results = super().retrieve(query, **kwargs)
        # Add custom re-ranking
        return self._custom_rerank(results)
```

### Content Generation (`content/`)

**Purpose:** AI-powered content creation

**Key Components:**
- `generation/tweet_generator.py` - Tweet generation with Claude
- `analysis/` - Performance analysis (TODO)
- `style/` - Style matching (TODO)

**Extension Points:**
```python
# Create custom generator
class ThreadGenerator(TweetGenerator):
    async def generate_mega_thread(self, topic, num_tweets=10):
        # Your custom logic
        pass

# Add to config
config.set('generators.thread', 'content.generation.custom.ThreadGenerator')
```

### Browser Automation (`automation/browser/`)

**Purpose:** Web scraping and interaction

**Key Components:**
- `browser_client.py` - Playwright wrapper
- Custom scrapers in `integrations/scraping/`

**Extension Points:**
```python
# Add custom scraper
class RedditScraper:
    async def scrape_subreddit(self, subreddit, limit=10):
        # Implementation
        pass

# Register in workflow
workflow.add_scraper('reddit', RedditScraper())
```

### Workflows (`automation/workflows/`)

**Purpose:** Automated task orchestration

**Creating New Workflows:**

```python
# automation/workflows/my_workflow.py

from typing import Dict, Any
from loguru import logger

class MyCustomWorkflow:
    """
    Your workflow description.

    Steps:
    1. Do something
    2. Do something else
    3. Generate output
    """

    def __init__(self, components...):
        self.component = component
        logger.info("MyCustomWorkflow initialized")

    async def run(self) -> Dict[str, Any]:
        """Execute workflow."""
        logger.info("Starting my custom workflow...")

        result = {
            'timestamp': datetime.now().isoformat(),
            'data': [],
            'errors': []
        }

        try:
            # Step 1
            logger.info("Step 1: ...")
            data = await self.do_something()
            result['data'].append(data)

            # Step 2
            logger.info("Step 2: ...")
            # ...

            return result

        except Exception as e:
            logger.error(f"Workflow error: {e}")
            result['errors'].append(str(e))
            return result

# Register in scheduler
from automation.schedulers.scheduler import TaskScheduler

scheduler = TaskScheduler()
scheduler.add_cron_job(
    MyCustomWorkflow().run,
    job_id="my_workflow",
    cron_expression="0 12 * * *",  # Noon daily
    description="My custom workflow"
)
```

## Adding New API Endpoints

```python
# backend/api/my_endpoints.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/my-feature", tags=["My Feature"])

class MyRequest(BaseModel):
    param: str

class MyResponse(BaseModel):
    result: str

@router.post("/process", response_model=MyResponse)
async def process_something(request: MyRequest):
    """Process something custom."""
    try:
        # Your logic
        result = do_processing(request.param)
        return MyResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include in main.py
from backend.api.my_endpoints import router as my_router
app.include_router(my_router)
```

## Database Models

For structured data beyond vector store:

```python
# backend/models/tweet.py

from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class TweetLog(Base):
    __tablename__ = 'tweet_logs'

    id = Column(Integer, primary_key=True)
    tweet_id = Column(String, unique=True)
    content = Column(String)
    posted_at = Column(DateTime, default=datetime.now)
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)

# Initialize
engine = create_engine('sqlite:///data/databases/xcontentrag.db')
Base.metadata.create_all(engine)
```

## Configuration

### Adding New Config Options

```yaml
# config/config.yaml

my_feature:
  enabled: true
  option1: "value"
  option2: 123
```

```python
# backend/core/config.py

@dataclass
class MyFeatureConfig:
    enabled: bool
    option1: str
    option2: int

class ConfigManager:
    @property
    def my_feature(self) -> MyFeatureConfig:
        feature = self.config.get('my_feature', {})
        return MyFeatureConfig(
            enabled=feature.get('enabled', False),
            option1=feature.get('option1', 'default'),
            option2=feature.get('option2', 100)
        )
```

## Testing

### Unit Tests

```python
# tests/test_tweet_generator.py

import pytest
import asyncio
from content.generation.tweet_generator import TweetGenerator

@pytest.fixture
def tweet_generator():
    # Setup
    generator = TweetGenerator(...)
    return generator

@pytest.mark.asyncio
async def test_generate_tweets(tweet_generator):
    ideas = await tweet_generator.generate_tweet_ideas_async(
        topic="test topic",
        num_ideas=3
    )

    assert len(ideas) == 3
    assert all(len(idea.content) <= 280 for idea in ideas)

# Run tests
# pytest tests/
```

### Integration Tests

```python
# tests/integration/test_workflow.py

import pytest
from automation.workflows.morning_briefing import MorningBriefingWorkflow

@pytest.mark.asyncio
async def test_morning_briefing_workflow():
    workflow = MorningBriefingWorkflow(...)
    result = await workflow.run()

    assert 'news_articles' in result
    assert 'tweet_ideas' in result
    assert len(result['errors']) == 0
```

## Performance Optimization

### Caching

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedRetriever:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = timedelta(hours=1)

    def retrieve(self, query):
        cache_key = hash(query)

        if cache_key in self._cache:
            cached_result, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                return cached_result

        result = self._do_retrieval(query)
        self._cache[cache_key] = (result, datetime.now())
        return result
```

### Batch Processing

```python
async def process_urls_batch(urls: List[str], batch_size: int = 10):
    """Process URLs in batches to avoid overwhelming APIs."""
    results = []

    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]
        batch_results = await asyncio.gather(*[
            scrape_url(url) for url in batch
        ])
        results.extend(batch_results)

        # Rate limiting
        await asyncio.sleep(1)

    return results
```

## Debugging

### Enable Debug Logging

```python
from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    level="DEBUG",
    format="{time} | {level} | {module}:{function}:{line} | {message}"
)
```

### Inspect Vector Store

```python
from rag.vectorstore.chroma_store import ChromaStore

store = ChromaStore(persist_directory="data/vectorstore/chroma")

# Check document count
print(f"Documents: {store.count()}")

# Peek at documents
sample = store.peek(limit=5)
for doc in sample['documents']:
    print(doc[:100])

# Check collection metadata
info = store.get_collection_metadata()
print(info)
```

### API Debugging

```bash
# Enable FastAPI debug mode
uvicorn backend.main:app --reload --log-level debug

# Test endpoints
curl -v http://localhost:8000/health

# Check OpenAPI schema
curl http://localhost:8000/openapi.json | jq
```

## Deployment

### Docker (Future)

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . .

CMD ["python", "-m", "backend.main"]
```

### Environment Variables

For production, use environment variables:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export TWITTER_API_KEY="..."

# Load in code
import os
from backend.core.config import ConfigManager

config = ConfigManager()
if not config.api_keys.anthropic_api_key:
    config.api_keys.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
```

## Contributing Guidelines

1. **Code Style:** Follow PEP 8, use Black formatter
2. **Type Hints:** Add type hints to all functions
3. **Documentation:** Docstrings for all classes and functions
4. **Tests:** Add tests for new features
5. **Logging:** Use loguru for consistent logging

## Common Patterns

### Async Initialization

```python
class MyComponent:
    def __init__(self):
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        # Async setup
        await self._setup()
        self._initialized = True

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
```

### Error Handling

```python
from loguru import logger

try:
    result = await risky_operation()
except SpecificException as e:
    logger.error(f"Expected error: {e}")
    # Handle gracefully
    return default_value
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    # Re-raise or handle
    raise
```

## Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com
- **ChromaDB Docs:** https://docs.trychroma.com
- **Anthropic API:** https://docs.anthropic.com
- **Playwright:** https://playwright.dev/python/

## Questions?

- Check inline code documentation
- Review example workflows
- Open an issue on GitHub
