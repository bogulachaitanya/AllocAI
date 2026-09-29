"""Streamlit page — Dataset Import.

Imports the full 5-sheet dynamic tech dataset.
"""

from __future__ import annotations

import logging

import streamlit as st

logger = logging.getLogger(__name__)


def render() -> None:
    st.title("📥 Dataset Import")
    st.caption(
        "Import the complete dynamic tech dataset (Employees, Projects, Assignments, Hindsight, Tech Transitions)."
    )

    uploaded = st.file_uploader(
        "Upload dataset workbook",
        type=["xlsx"],
        help="Accepted format: Excel (.xlsx). Must contain 5 specific sheets.",
    )

    if uploaded is None:
        st.markdown("### Expected Sheets")
        st.markdown("- **Employees**")
        st.markdown("- **Projects**")
        st.markdown("- **Project_Teams**")
        st.markdown("- **Tech_Transitions**")
        st.markdown("- **Hindsight_Memories**")
        return

    file_bytes = uploaded.read()
    st.info(f"📄 **{uploaded.name}** — {len(file_bytes) / 1024:.1f} KB uploaded")

    if st.button("🚀 Validate & Import Dataset", type="primary"):
        import os
        import tempfile

        from db.session import get_db
        from hindsight.adapter import get_hindsight_adapter
        from services.dataset_importer import DatasetImporter

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            with get_db() as db:
                hindsight = get_hindsight_adapter()
                importer = DatasetImporter(session=db, hindsight_adapter=hindsight)

                with st.spinner("Validating workbook..."):
                    valid, result = importer.validate_workbook(tmp_path)

                if not valid:
                    st.error("Validation Failed")
                    st.json(result)
                    return

                st.success("Validation Passed!")
                st.json(result.get("sizes", {}))

                with st.spinner("Importing into database and Hindsight..."):
                    counts = importer.import_workbook(tmp_path)

                st.success("Dataset Import Complete!")
                st.json(counts)
        except Exception as e:
            st.error(f"Import Error: {e!s}")
            logger.exception("Dataset import failed")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
