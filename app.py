"""
The Streamlit app: paste a posting, extract it, and browse everything
you've saved so far. A local demo backed by Ollama.
"""

import logging
import sqlite3

import pandas as pd
import streamlit as st

from extractor import ExtractionError, extract_posting
from storage import all_postings, init_db, save_posting

st.set_page_config(page_title="Job-Description Structured Extractor", layout="wide")
st.title("Job-Description Structured Extractor")
st.caption("Paste any job posting. A local model turns it into structured JSON — skills, tech stack, seniority, and whether it mentions visa sponsorship. Runs entirely on this Mac, no API key.")

try:
    conn = init_db()
except sqlite3.Error:
    st.error("Could not open postings.db. Check folder permissions and available disk space.")
    st.stop()

tab_extract, tab_history = st.tabs(["Extract a posting", "My saved postings"])

with tab_extract:
    raw_text = st.text_area("Paste the full job posting text here", height=300)
    source_note = st.text_input("Where's this from? (optional — e.g. a LinkedIn URL)")

    if st.button("Extract", type="primary"):
        if not raw_text.strip():
            st.warning("Paste a job posting first.")
        else:
            try:
                with st.spinner("Extracting..."):
                    result = extract_posting(raw_text)
            except ExtractionError as exc:
                st.error(str(exc))
            except Exception:
                logging.exception("Unexpected extraction failure")
                st.error("Extraction failed unexpectedly. Check the terminal for details and retry.")
            else:
                st.session_state["last_result"] = result
                try:
                    row_id = save_posting(conn, raw_text, result, source_note)
                    st.success(f"Saved posting #{row_id}. Identical text reuses the existing record.")
                except sqlite3.Error:
                    st.error("Extraction succeeded, but saving failed. The result is shown below. Check database permissions or retry if it is locked.")

    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        st.caption("Last successful extraction (may differ from the text currently in the editor).")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Seniority", result.get("seniority_level", "—"))
            st.metric("Sponsorship signal", result.get("sponsorship_signal", "—"))
            if result.get("sponsorship_evidence_quote"):
                st.caption(f"Evidence: “{result['sponsorship_evidence_quote']}”")
        with col2:
            st.write("**Required skills**", result.get("required_skills", []))
            st.write("**Tech stack**", result.get("tech_stack", []))

        with st.expander("Full extracted JSON"):
            st.json(result)

with tab_history:
    try:
        postings = all_postings(conn)
    except (sqlite3.Error, ValueError, TypeError):
        st.error("Could not read saved postings. Check database access and stored JSON.")
        postings = []
    if not postings:
        st.info("Nothing saved yet — extract a posting on the first tab.")
    else:
        df = pd.DataFrame(postings)
        display_cols = [c for c in ["company", "job_title", "seniority_level", "sponsorship_signal", "saved_at"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        st.divider()
        options = {f"#{row['id']}: {row['job_title']} @ {row['company']} ({row['saved_at']})": row["id"] for _, row in df.iterrows()}
        chosen_label = st.selectbox("View full extraction:", list(options.keys()))
        chosen_id = options[chosen_label]
        full_record = df[df["id"] == chosen_id].iloc[0].to_dict()
        st.json(full_record)

conn.close()
