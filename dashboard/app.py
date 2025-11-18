"""
X Content RAG System Dashboard

Streamlit-based web interface for managing and monitoring the content creation system.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import asyncio
from datetime import datetime
import json

from backend.core.config import get_config

# Page configuration
st.set_page_config(
    page_title="X Content RAG System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1DA1F2;
        margin-bottom: 1rem;
    }
    .stat-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .tweet-preview {
        background-color: #ffffff;
        border: 1px solid #e1e8ed;
        border-radius: 1rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def load_config():
    """Load system configuration."""
    try:
        return get_config()
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
        return None


def main():
    """Main dashboard application."""

    # Sidebar
    with st.sidebar:
        st.title("🤖 X Content RAG")

        # Navigation
        page = st.radio(
            "Navigation",
            ["Dashboard", "Generate Tweets", "Knowledge Base", "Analytics", "Settings"]
        )

        st.divider()

        # Status indicators
        st.subheader("System Status")

        try:
            config = load_config()
            if config:
                st.success("✅ Config Loaded")

                # Check API key
                if config.api_keys.anthropic_api_key:
                    st.success("✅ Claude API")
                else:
                    st.warning("⚠️ Claude API key missing")

                # Check vector store
                try:
                    from rag.vectorstore.chroma_store import ChromaStore
                    store = ChromaStore(
                        persist_directory=config.rag.vectorstore_path,
                        collection_name="content"
                    )
                    doc_count = store.count()
                    st.success(f"✅ Vector Store ({doc_count} docs)")
                except Exception as e:
                    st.error(f"❌ Vector Store: {e}")

        except Exception as e:
            st.error(f"❌ System Error: {e}")

    # Main content
    if page == "Dashboard":
        show_dashboard()
    elif page == "Generate Tweets":
        show_generate_tweets()
    elif page == "Knowledge Base":
        show_knowledge_base()
    elif page == "Analytics":
        show_analytics()
    elif page == "Settings":
        show_settings()


def show_dashboard():
    """Show main dashboard."""
    st.markdown('<div class="main-header">📊 Dashboard</div>', unsafe_allow_html=True)

    # Stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Documents", "Loading...", help="Total documents in knowledge base")

    with col2:
        st.metric("Tweets Generated", "Loading...", help="Total tweets generated")

    with col3:
        st.metric("Engagement Rate", "Loading...", help="Average engagement rate")

    with col4:
        st.metric("Last Run", "Loading...", help="Last workflow execution")

    st.divider()

    # Recent activity
    st.subheader("📝 Recent Activity")
    st.info("No recent activity to display. Run a workflow to get started!")

    # Quick actions
    st.divider()
    st.subheader("⚡ Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🌅 Run Morning Briefing", use_container_width=True):
            with st.spinner("Running morning briefing..."):
                st.info("Morning briefing workflow started. Check logs for progress.")

    with col2:
        if st.button("💡 Generate Tweet Ideas", use_container_width=True):
            st.session_state.page = "Generate Tweets"
            st.rerun()

    with col3:
        if st.button("📚 Index New Content", use_container_width=True):
            st.info("Content indexing feature coming soon!")


def show_generate_tweets():
    """Show tweet generation page."""
    st.markdown('<div class="main-header">💡 Generate Tweets</div>', unsafe_allow_html=True)

    config = load_config()
    if not config:
        st.error("Cannot load configuration. Please check config/config.yaml")
        return

    # Topic input
    col1, col2 = st.columns([3, 1])

    with col1:
        topic = st.text_input(
            "Tweet Topic",
            placeholder="e.g., AI trends, machine learning, productivity tips",
            help="Enter a topic to generate tweet ideas about"
        )

    with col2:
        num_ideas = st.number_input("Number of Ideas", min_value=1, max_value=10, value=5)

    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        use_rag = st.checkbox("Use RAG Context", value=True, help="Retrieve relevant content from knowledge base")
        temperature = st.slider("Creativity", min_value=0.0, max_value=1.0, value=0.7, step=0.1)

    # Generate button
    if st.button("✨ Generate Tweet Ideas", type="primary", use_container_width=True):
        if not topic:
            st.warning("Please enter a topic")
            return

        with st.spinner(f"Generating {num_ideas} tweet ideas about '{topic}'..."):
            try:
                # Initialize components
                from integrations.claude.client import ClaudeClient
                from rag.embeddings.generator import EmbeddingGenerator
                from rag.vectorstore.chroma_store import ChromaStore
                from rag.retrieval.retriever import ContentRetriever
                from content.generation.tweet_generator import TweetGenerator

                claude_client = ClaudeClient(
                    api_key=config.api_keys.anthropic_api_key,
                    model=config.claude.model,
                    temperature=temperature
                )

                embedding_generator = EmbeddingGenerator(
                    model_name=config.rag.embedding_model
                )

                vector_store = ChromaStore(
                    persist_directory=config.rag.vectorstore_path,
                    collection_name="content"
                )

                content_retriever = ContentRetriever(
                    vector_store=vector_store,
                    embedding_generator=embedding_generator
                )

                tweet_generator = TweetGenerator(
                    claude_client=claude_client,
                    content_retriever=content_retriever,
                    config=config.content.tweet_characteristics
                )

                # Generate tweets
                ideas = asyncio.run(tweet_generator.generate_tweet_ideas_async(
                    topic=topic,
                    num_ideas=num_ideas
                ))

                # Display results
                st.success(f"✅ Generated {len(ideas)} tweet ideas!")

                for i, idea in enumerate(ideas, 1):
                    with st.container():
                        st.markdown(f"""
                        <div class="tweet-preview">
                            <h4>Idea {i}</h4>
                            <p style="font-size: 1.1rem; margin: 1rem 0;">{idea.content}</p>
                            <div style="color: #657786; font-size: 0.9rem;">
                                <strong>Category:</strong> {idea.category} |
                                <strong>Confidence:</strong> {idea.confidence:.0%} |
                                <strong>Hashtags:</strong> {', '.join(idea.hashtags)}
                            </div>
                            <p style="color: #657786; font-size: 0.9rem; margin-top: 0.5rem;">
                                <strong>Rationale:</strong> {idea.rationale}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button(f"✏️ Edit", key=f"edit_{i}"):
                                st.info("Edit feature coming soon!")
                        with col2:
                            if st.button(f"📋 Copy", key=f"copy_{i}"):
                                st.success("Copied to clipboard!")
                        with col3:
                            if st.button(f"🚀 Post", key=f"post_{i}"):
                                st.info("Posting feature coming soon!")

            except Exception as e:
                st.error(f"Error generating tweets: {e}")


def show_knowledge_base():
    """Show knowledge base management."""
    st.markdown('<div class="main-header">📚 Knowledge Base</div>', unsafe_allow_html=True)

    config = load_config()
    if not config:
        st.error("Cannot load configuration")
        return

    tab1, tab2, tab3 = st.tabs(["📖 Browse", "➕ Add Content", "🔍 Search"])

    with tab1:
        st.subheader("Documents in Knowledge Base")

        try:
            from rag.vectorstore.chroma_store import ChromaStore

            vector_store = ChromaStore(
                persist_directory=config.rag.vectorstore_path,
                collection_name="content"
            )

            count = vector_store.count()
            st.info(f"Total documents: {count}")

            # Show sample documents
            if count > 0:
                sample = vector_store.peek(limit=10)
                st.write("Sample documents:")
                for i, doc in enumerate(sample['documents'], 1):
                    with st.expander(f"Document {i}"):
                        st.write(doc[:500] + "..." if len(doc) > 500 else doc)

        except Exception as e:
            st.error(f"Error loading documents: {e}")

    with tab2:
        st.subheader("Add New Content")

        content_type = st.selectbox("Content Type", ["Text", "File", "URL"])

        if content_type == "Text":
            content = st.text_area("Content", height=200)
            category = st.text_input("Category", "general")

            if st.button("Add to Knowledge Base"):
                if content:
                    st.success("Content added successfully!")
                else:
                    st.warning("Please enter some content")

        elif content_type == "File":
            uploaded_file = st.file_uploader("Upload File", type=['txt', 'md', 'json'])
            if uploaded_file:
                st.info(f"File: {uploaded_file.name}")
                if st.button("Index File"):
                    st.success("File indexed successfully!")

        elif content_type == "URL":
            url = st.text_input("URL")
            if st.button("Scrape and Index"):
                if url:
                    st.info("Scraping URL...")
                else:
                    st.warning("Please enter a URL")

    with tab3:
        st.subheader("Search Knowledge Base")

        query = st.text_input("Search Query")
        top_k = st.slider("Number of Results", 1, 20, 5)

        if st.button("🔍 Search"):
            if query:
                st.info(f"Searching for: {query}")
                st.write("Search results will appear here")
            else:
                st.warning("Please enter a search query")


def show_analytics():
    """Show analytics and metrics."""
    st.markdown('<div class="main-header">📈 Analytics</div>', unsafe_allow_html=True)

    st.info("Analytics dashboard coming soon!")

    # Placeholder metrics
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Tweet Performance")
        st.line_chart({"Engagement": [100, 150, 120, 180, 200, 250]})

    with col2:
        st.subheader("Content Distribution")
        st.bar_chart({"AI": 45, "Tech": 30, "Productivity": 25})


def show_settings():
    """Show settings page."""
    st.markdown('<div class="main-header">⚙️ Settings</div>', unsafe_allow_html=True)

    config = load_config()
    if not config:
        st.error("Cannot load configuration")
        return

    tab1, tab2, tab3 = st.tabs(["🔑 API Keys", "🤖 Models", "📅 Scheduling"])

    with tab1:
        st.subheader("API Configuration")

        st.text_input("Anthropic API Key", value="sk-ant-...", type="password")
        st.text_input("Twitter API Key", value="", type="password")

        if st.button("💾 Save API Keys"):
            st.success("API keys saved!")

    with tab2:
        st.subheader("Model Configuration")

        st.selectbox("Claude Model", [
            "claude-sonnet-4-5-20250929",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229"
        ])

        st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        st.number_input("Max Tokens", 100, 4000, 1024)

        if st.button("💾 Save Model Settings"):
            st.success("Model settings saved!")

    with tab3:
        st.subheader("Scheduled Tasks")

        tasks = [
            {"name": "Morning Briefing", "schedule": "0 8 * * *", "enabled": True},
            {"name": "Trending Check", "schedule": "0 */2 * * *", "enabled": True},
            {"name": "Tweet Generation", "schedule": "0 10,16 * * *", "enabled": False},
        ]

        for task in tasks:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{task['name']}**")
            with col2:
                st.code(task['schedule'])
            with col3:
                st.checkbox("Enabled", value=task['enabled'], key=task['name'])


if __name__ == "__main__":
    main()
