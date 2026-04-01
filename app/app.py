import streamlit as st
from ui_components import job_preferences_form, career_insights_page, resume_management_page
import time
from dotenv import load_dotenv
import os

# --- Load Environment Variables ---
load_dotenv()

# Set page config
st.set_page_config(layout="wide", initial_sidebar_state="auto")

# --- Page Definitions ---
pages = {
    "resume_management": resume_management_page,
    "job_preferences": job_preferences_form,
    "career_insights": career_insights_page,
}

# --- Main App Logic ---
def main():
    # --- SESSION STATE INITIALIZATION ---
    default_session_state = {
        "current_page": "resume_management",
        # Use a fixed UUID since auth is removed
        "user_id": "00000000-0000-0000-0000-000000000001",
        "suggested_titles": [],
        "extracted_skills": [],
        "pref_text_area_value": "",
        "resume_upload_success": False,
        "just_processed_audio": False,
    }
    for key, default_value in default_session_state.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

    # --- Sidebar Navigation ---
    with st.sidebar:
        st.title("ScoutifyAI")

        resume_type = "primary" if st.session_state.current_page == "resume_management" else "secondary"
        search_type = "primary" if st.session_state.current_page == "job_preferences" else "secondary"
        insights_type = "primary" if st.session_state.current_page == "career_insights" else "secondary"

        if st.button("📄 Upload Resume", use_container_width=True, type=resume_type):
            if st.session_state.current_page != "resume_management":
                st.session_state.current_page = "resume_management"
                st.rerun()

        if st.button("🔍 Search Jobs", use_container_width=True, type=search_type):
            if st.session_state.current_page != "job_preferences":
                st.session_state.current_page = "job_preferences"
                st.rerun()

        if st.button("📈 Career Insights", use_container_width=True, type=insights_type):
            if st.session_state.current_page != "career_insights":
                st.session_state.current_page = "career_insights"
                st.rerun()

    # --- Main Page Area ---
    if st.session_state.current_page in pages:
        pages[st.session_state.current_page]()
    else:
        st.session_state.current_page = "resume_management"
        st.rerun()


if __name__ == "__main__":
    main()