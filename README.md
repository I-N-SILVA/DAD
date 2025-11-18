# X Content Creation RAG System

An intelligent, automated content creation system for X (Twitter) powered by RAG (Retrieval-Augmented Generation), browser automation, and AI.

## ✨ Features

### Core Capabilities
- **RAG-Powered Content Generation**: Leverages your past tweets, writing samples, and curated content to generate on-brand tweets
- **Intelligent Scraping**: Monitors trending topics, competitor accounts, and news sources
- **Browser Automation**: Automatically researches content, extracts insights, and manages web tasks
- **Smart Scheduling**: Posts content at optimal times based on your engagement history
- **X/Twitter Integration**: Direct posting, engagement tracking, and social listening
- **Privacy-First**: All data stored locally with secure API key management
- **Web Dashboard**: Review, approve, and manage all automated content

### 🚀 NEW Advanced Features
- **📊 Performance Analytics**: AI-powered insights into what content works best
- **🎯 Tweet Scoring**: Predict engagement before posting (0-100 score with recommendations)
- **🤖 Smart Queue with ML**: Auto-schedule tweets at optimal times based on your history
- **🕵️ Competitor Intelligence**: Deep analysis of competitor accounts + content gap identification
- **💬 Engagement Automation**: AI-powered replies and relationship building (with safety filters)
- **🎨 Visual Content Generation**: Auto-generate quote cards, stats visuals, and thread previews
- **🔔 Smart Notifications**: Mac notifications + email reports for trends, engagement, and performance
- **📈 Comprehensive Tracking**: SQLite database tracking all tweets, analytics, and interactions

**👉 See [NEW_FEATURES.md](NEW_FEATURES.md) for detailed documentation of all advanced features!**

## Architecture

```
x-content-rag/
├── backend/                    # FastAPI backend
│   ├── api/                   # API endpoints
│   ├── core/                  # Core business logic
│   ├── models/                # Database models
│   └── services/              # Business services
├── rag/                       # RAG system
│   ├── embeddings/            # Embedding generation
│   ├── indexing/              # Content indexing
│   ├── retrieval/             # Semantic search
│   └── vectorstore/           # ChromaDB interface
├── automation/                # Automation engine
│   ├── browser/               # Playwright automation
│   ├── schedulers/            # APScheduler jobs
│   └── workflows/             # Workflow definitions
├── content/                   # Content generation
│   ├── generation/            # AI content generation
│   ├── analysis/              # Performance analysis
│   └── style/                 # Style matching
├── integrations/              # External integrations
│   ├── twitter/               # X/Twitter API
│   ├── scraping/              # Web scraping
│   └── claude/                # Claude API
├── dashboard/                 # Streamlit UI
├── data/                      # Local data storage
│   ├── knowledge_base/        # RAG documents
│   ├── databases/             # SQLite databases
│   └── logs/                  # Application logs
└── config/                    # Configuration files
```

## Installation

### Prerequisites

- Python 3.10+
- macOS (optimized for Mac)
- API Keys:
  - Anthropic Claude API key
  - X/Twitter API credentials (optional)

### Setup

1. Clone the repository:
```bash
git clone <repo-url>
cd DAD
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. Configure the system:
```bash
cp config/config.example.yaml config/config.yaml
# Edit config/config.yaml with your API keys and preferences
```

5. Initialize the database and RAG system:
```bash
python scripts/init_system.py
```

6. (Optional) Import your X archive:
```bash
python scripts/import_twitter_archive.py --archive-path /path/to/twitter-archive.zip
```

## Usage

### Start the Backend Server

```bash
python -m backend.main
```

The API will be available at `http://localhost:8000`

### Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard will open at `http://localhost:8501`

### Run Automated Workflows

The system automatically runs scheduled tasks when the backend is running:
- Morning content briefing (8:00 AM)
- Trending topics check (every 2 hours)
- Tweet generation (twice daily)
- Performance reports (weekly)

### Manual Operations

```bash
# Generate tweet ideas manually
python scripts/generate_tweets.py --topic "AI trends"

# Run browser research workflow
python scripts/research_workflow.py --urls urls.txt

# Monitor competitors
python scripts/competitor_analysis.py
```

## Configuration

Edit `config/config.yaml` to customize:

- **API Keys**: Claude, X/Twitter credentials
- **Scheduling**: Cron expressions for automation
- **Content Preferences**: Niches, topics, hashtags
- **Browser Automation**: Target sites, scraping rules
- **RAG Settings**: Embedding model, retrieval parameters
- **Posting Rules**: Auto-post vs. approval required

## Workflows

### 1. Morning Content Briefing
Scrapes news, analyzes trends, generates tweet ideas
```bash
python -m automation.workflows.morning_briefing
```

### 2. Browser Research Agent
Researches URLs, extracts insights, updates knowledge base
```bash
python -m automation.workflows.research_agent --urls "url1,url2,url3"
```

### 3. Competitor Intelligence
Monitors accounts, identifies content gaps, suggests topics
```bash
python -m automation.workflows.competitor_intel
```

## Mac Background Service

To run as a background service on Mac:

```bash
# Install as LaunchAgent
python scripts/install_service.py

# Start service
launchctl load ~/Library/LaunchAgents/com.xcontentrag.plist

# Stop service
launchctl unload ~/Library/LaunchAgents/com.xcontentrag.plist
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Project Structure

- `backend/`: FastAPI application with REST endpoints
- `rag/`: RAG implementation with ChromaDB
- `automation/`: Browser automation and scheduling
- `content/`: Content generation and analysis
- `integrations/`: External API integrations
- `dashboard/`: Streamlit web interface
- `scripts/`: Utility scripts

### Adding New Workflows

1. Create workflow file in `automation/workflows/`
2. Define workflow class inheriting from `BaseWorkflow`
3. Register in `automation/schedulers/scheduler.py`
4. Add configuration in `config/config.yaml`

### Extending the RAG System

1. Add documents to `data/knowledge_base/`
2. Run indexing: `python scripts/index_documents.py`
3. Query via API or dashboard

## Security

- API keys stored in `config/config.yaml` (gitignored)
- Use environment variables for sensitive data
- All data stored locally (no cloud dependencies)
- Rate limiting on API endpoints
- Input validation and sanitization

## Troubleshooting

### Common Issues

1. **Playwright browser not found**
   ```bash
   playwright install chromium
   ```

2. **ChromaDB persistence error**
   ```bash
   rm -rf data/vectorstore/chroma/
   python scripts/init_system.py
   ```

3. **Import error**
   Ensure virtual environment is activated:
   ```bash
   source venv/bin/activate
   ```

## Contributing

This is a personal project, but suggestions welcome!

## License

MIT License

## Acknowledgments

- Anthropic Claude for AI generation
- ChromaDB for vector storage
- Playwright for browser automation
- FastAPI for backend framework
