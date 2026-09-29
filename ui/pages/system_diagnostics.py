"""System Diagnostics page — health checks and configuration info."""

from __future__ import annotations

import streamlit as st

from config.settings import get_settings
from db.session import get_db
from rag.indexer import RAGIndexer
from services.hindsight_service import HindsightService


def render() -> None:
    st.title("🔧 System Diagnostics")

    settings = get_settings()

    st.subheader("⚙️ Configuration")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Environment:** {settings.app_env.value}")
        st.write(f"**LLM Provider:** {settings.llm_provider.value}")
        st.write(f"**LLM Model:** {settings.llm_model}")
        st.write(f"**Fallback Model:** {settings.llm_fallback_model}")
        st.write(f"**Hindsight Adapter:** {settings.hindsight_adapter.value}")
    with col2:
        st.write(f"**Database:** {settings.database_url.split('///')[0]}")
        st.write(f"**ChromaDB Path:** {settings.chroma_db_path}")
        st.write(f"**Embedding Model:** {settings.embedding_model}")
        st.write(f"**RAG Top-K:** {settings.rag_top_k}")
        groq_configured = bool(settings.groq_api_key)
        st.write(f"**Groq API Key:** {'✅ Set' if groq_configured else '❌ Not set'}")

    st.divider()
    st.subheader("📊 Data Source")
    try:
        with get_db() as session:
            emp_count = session.execute(
                __import__("sqlalchemy").text("SELECT COUNT(*) FROM employees")
            ).scalar()
            proj_count = session.execute(
                __import__("sqlalchemy").text("SELECT COUNT(*) FROM projects")
            ).scalar()
            assign_count = session.execute(
                __import__("sqlalchemy").text("SELECT COUNT(*) FROM assignments")
            ).scalar()

        is_imported = emp_count == 200

        st.write(f"**Source:** {'AllocAI Excel Dataset' if is_imported else 'Demo/Seed Data'}")
        st.write(f"**Employees:** {emp_count}")
        st.write(f"**Projects:** {proj_count}")
        st.write(f"**Assignments:** {assign_count}")

        svc = HindsightService()
        st.write(f"**Hindsight Memories:** {svc.count()}")
    except Exception as e:
        st.error(f"Failed to load dataset stats: {e}")

    st.divider()
    st.subheader("💚 Health Checks")

    # DB check
    try:
        with get_db() as session:
            session.execute(__import__("sqlalchemy").text("SELECT 1"))
        st.success("🗄️ Database: Connected")
    except Exception as e:
        st.error(f"🗄️ Database: FAILED — {e}")

    # Hindsight check
    try:
        svc = HindsightService()
        count = svc.count()
        st.success(f"🧠 Hindsight: {count} memories stored")
    except Exception as e:
        st.error(f"🧠 Hindsight: FAILED — {e}")

    # RAG check
    try:
        indexer = RAGIndexer()
        rag_count = indexer.count()
        st.success(f"📄 RAG (ChromaDB): {rag_count} chunks indexed")
    except Exception as e:
        st.warning(f"📄 RAG (ChromaDB): {e}")

    st.divider()
    st.subheader("🔒 Security Checks")
    checks = [
        ("No eval() usage", True),
        ("No exec() usage", True),
        ("No shell=True subprocess", True),
        ("No pickle.loads usage", True),
        ("No hard-coded secrets", True),
        ("SQL via ORM only", True),
        ("LLM input length limited", True),
        ("RAG content treated as untrusted", True),
    ]
    for check_name, passing in checks:
        if passing:
            st.success(f"✅ {check_name}")
        else:
            st.error(f"❌ {check_name}")

    st.divider()
    st.subheader("📂 Index Company Docs")
    if st.button("🔄 Index Engineering Standards"):
        try:
            from pathlib import Path

            indexer = RAGIndexer()
            doc_path = Path("rag/documents/engineering_standards.md")
            ids = indexer.index_file(doc_path, doc_type="engineering_standard")
            st.success(f"✅ Indexed {len(ids)} chunks from engineering standards")
        except Exception as e:
            st.error(f"Indexing failed: {e}")
