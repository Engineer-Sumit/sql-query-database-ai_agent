import streamlit as st
import os

def load_css():
    with open("ui/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def header():
    st.title("Database AI Agent — SQL in Natural Language")
    st.markdown(
        "<p style='color:#9ca3af'>Ask questions in plain English and get SQL answers.</p>",
        unsafe_allow_html=True
    )

def section(title, desc):
    st.markdown(
        f"""
        <div class="card">
            <h4>{title}</h4>
            <p style="color:#9ca3af">{desc}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def sidebar():
    # Load CSS from the local ui/ directory
    current_dir = os.path.dirname(__file__)
    css_file = os.path.join(current_dir, "styles.css")
    
    with open(css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Render HTML
    st.sidebar.markdown(
        """
        <div class="sidebar-container">
            <div class="sidebar-title">Database AI Agent</div>            
            <div class="sidebar-text">
                “Query your data effortlessly using simple natural language. Our intelligent AI understands your questions, converts them into optimized SQL queries, and delivers accurate results with beautiful, interactive visualizations in seconds. No coding required—just ask, explore insights, and make smarter, data-driven decisions with ease.”
            </div>
        </div>

        <div class="sidebar-footer">
            Built with 💙 by <a class="author-link" href="https://github.com/Engineer-Sumit/sql-query-database-ai_agent">Engineer Sumit</a>
        </div>
        """,
        unsafe_allow_html=True
    )



