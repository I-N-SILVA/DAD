# Quick Start Guide

Get your X Content RAG System up and running in minutes!

## Prerequisites

- **macOS** (or Linux/Windows with minor adjustments)
- **Python 3.10+**
- **Anthropic API Key** (required)
- **X/Twitter API Keys** (optional, for posting and trending)

## Installation

### 1. Clone and Setup

```bash
cd DAD
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure

```bash
# Copy example config
cp config/config.example.yaml config/config.yaml

# Edit with your API keys
nano config/config.yaml  # or use your preferred editor
```

**Required:** Add your Anthropic API key:
```yaml
api_keys:
  anthropic_api_key: "sk-ant-your-key-here"
```

**Optional:** Add Twitter API credentials for full functionality.

### 4. Initialize System

```bash
python scripts/init_system.py
```

This will:
- Create necessary directories
- Initialize the vector database
- Validate configuration
- Set up logging

## Quick Test

### Generate Tweet Ideas

```bash
python -c "
import asyncio
from integrations.claude.client import ClaudeClient
from content.generation.tweet_generator import TweetGenerator
from rag.vectorstore.chroma_store import ChromaStore
from rag.embeddings.generator import EmbeddingGenerator
from rag.retrieval.retriever import ContentRetriever
from backend.core.config import get_config

config = get_config()

async def test():
    # Initialize components
    claude = ClaudeClient(api_key=config.api_keys.anthropic_api_key)
    embedding_gen = EmbeddingGenerator()
    store = ChromaStore(persist_directory=config.rag.vectorstore_path)
    retriever = ContentRetriever(store, embedding_gen)
    generator = TweetGenerator(claude, retriever)

    # Generate tweets
    ideas = await generator.generate_tweet_ideas_async('AI trends', num_ideas=3)

    for i, idea in enumerate(ideas, 1):
        print(f'\n{i}. {idea.content}')
        print(f'   Category: {idea.category}')

asyncio.run(test())
"
```

## Running the System

### Start the Backend API

```bash
python -m backend.main
```

API will be available at `http://localhost:8000`

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### Launch the Dashboard

In a new terminal (with venv activated):

```bash
streamlit run dashboard/app.py
```

Dashboard will open at `http://localhost:8501`

## First Steps

### 1. Add Content to Knowledge Base

**Option A: Add text directly via dashboard**
- Open dashboard → Knowledge Base → Add Content
- Paste your previous tweets or writing samples
- Click "Add to Knowledge Base"

**Option B: Import Twitter Archive**
```bash
python scripts/import_twitter_archive.py --archive-path /path/to/twitter-archive.zip
```

**Option C: Add files programmatically**
```python
from rag.indexing.indexer import DocumentIndexer
from rag.vectorstore.chroma_store import ChromaStore
from rag.embeddings.generator import EmbeddingGenerator
from backend.core.config import get_config

config = get_config()
generator = EmbeddingGenerator()
store = ChromaStore(persist_directory=config.rag.vectorstore_path)
indexer = DocumentIndexer(store, generator)

# Index a directory of documents
stats = indexer.index_from_directory("data/knowledge_base", recursive=True)
print(f"Indexed {stats['total_documents']} documents")
```

### 2. Run Morning Briefing

```bash
python -m automation.workflows.morning_briefing
```

This will:
- Scrape tech news (HackerNews, TechCrunch)
- Get trending topics
- Generate tweet ideas
- Save to knowledge base

### 3. Generate Tweet Ideas

Via API:
```bash
curl -X POST http://localhost:8000/generate/tweets \
  -H "Content-Type: application/json" \
  -d '{"topic": "artificial intelligence", "num_ideas": 5}'
```

Via Dashboard:
- Open dashboard → Generate Tweets
- Enter topic
- Click "Generate"

## Enable Automation

Edit `config/config.yaml`:

```yaml
scheduling:
  enabled: true
  timezone: "America/Los_Angeles"

  jobs:
    morning_briefing:
      enabled: true
      cron: "0 8 * * *"  # 8 AM daily
```

Restart backend to activate scheduled jobs.

## Run as Background Service (Mac)

```bash
python scripts/install_mac_service.py

# Start service
launchctl load ~/Library/LaunchAgents/com.xcontentrag.service.plist

# Check status
launchctl list | grep xcontentrag

# View logs
tail -f data/logs/stdout.log
```

## Common Tasks

### Search Knowledge Base

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "top_k": 5}'
```

### Get System Stats

```bash
curl http://localhost:8000/stats
```

### Trigger Workflow Manually

```bash
curl -X POST http://localhost:8000/workflows/morning-briefing
```

## Troubleshooting

### Playwright Browser Not Found

```bash
playwright install chromium
```

### ChromaDB Permission Error

```bash
rm -rf data/vectorstore/chroma/
python scripts/init_system.py
```

### Import Errors

Ensure virtual environment is activated:
```bash
source venv/bin/activate
which python  # Should point to venv/bin/python
```

### API Key Issues

Check config:
```bash
python -c "from backend.core.config import get_config; print(get_config().api_keys.anthropic_api_key[:10])"
```

## Next Steps

- **Customize**: Edit `config/config.yaml` to match your preferences
- **Add Content**: Import more writing samples and articles
- **Explore Workflows**: Check `automation/workflows/` for examples
- **Build Custom Features**: See `DEVELOPMENT.md` for architecture details

## Need Help?

- Check logs: `data/logs/`
- Review documentation: `README.md`, `DEVELOPMENT.md`
- API docs: `http://localhost:8000/docs`

Happy content creating! 🚀
