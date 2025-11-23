# sql_db_agent.py
import os
import re
import io
from dotenv import load_dotenv
import pandas as pd
import sqlite3
from sqlalchemy import create_engine, text
import streamlit as st

# LangChain / OpenAI imports
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase

# Config & load env
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    st.error("OPENAI_API_KEY not found in .env — add it and restart.")
    st.stop()

# Initialize model (use gpt-3.5-turbo or change)
llm = ChatOpenAI(api_key=OPENAI_KEY, model="gpt-3.5-turbo", temperature=0)

# Streamlit UI Layout
st.set_page_config(page_title="SQL DB AI Agent", layout="wide")
st.title("Database AI Agent — SQL queries in Natural Language")

st.markdown(
    """
- Upload one or more CSV files (they will be imported to a local SQLite DB).
- Ask natural language questions and the agent will generate SQL, run it and answer.
- You can also request plots (use words: `plot`, `chart`, `graph`).
    """
)

# Sidebar: DB file location and reset
with st.sidebar:
    st.header("Database settings")
    db_path = st.text_input("SQLite DB file path", value="./db/salary.db")
    if st.button("Reset DB (delete & recreate)"):
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                st.success("Database deleted. Recreate by uploading CSV or using Load CSV.")
            except Exception as e:
                st.error(f"Could not delete DB: {e}")
        else:
            st.info("DB file does not exist.")

# Ensure db directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Session state for history / loaded tables
if "history" not in st.session_state:
    st.session_state.history = []  # list of tuples (user_query, agent_answer, sql_used)
if "tables_loaded" not in st.session_state:
    st.session_state.tables_loaded = []  # list of table names

# File upload (multiple)
st.subheader("1) Upload CSV files (optional)")
uploaded = st.file_uploader("Upload CSV(s) to import into SQLite", type=["csv"], accept_multiple_files=True)
if uploaded:
    # create engine
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    for uploaded_file in uploaded:
        try:
            file_bytes = uploaded_file.read()
            df = pd.read_csv(io.BytesIO(file_bytes)).fillna(0)
            # derive table name from filename (safe)
            name = os.path.splitext(uploaded_file.name)[0]
            table_name = re.sub(r"\W+", "_", name).lower()
            df.to_sql(table_name, con=engine, if_exists="replace", index=False)
            if table_name not in st.session_state.tables_loaded:
                st.session_state.tables_loaded.append(table_name)
            st.success(f"Imported `{uploaded_file.name}` as table `{table_name}` ({len(df)} rows).")
        except Exception as e:
            st.error(f"Failed to import {uploaded_file.name}: {e}")

# If DB already exists and tables not loaded in session, reflect them
engine = create_engine(f"sqlite:///{db_path}", echo=False)
try:
    with engine.connect() as conn:
        # list tables
        res = conn.execute(text("SELECT name FROM sqlite_schema WHERE type='table'")).fetchall()
        existing_tables = [r[0] for r in res]
        for t in existing_tables:
            if t not in st.session_state.tables_loaded:
                st.session_state.tables_loaded.append(t)
except Exception:
    existing_tables = []

if st.session_state.tables_loaded:
    st.info(f"Loaded tables: {', '.join(st.session_state.tables_loaded)}")
else:
    st.info("No tables in DB yet. Upload CSV or load an existing DB file.")

# Prepare LangChain SQL agent
# Use SQLDatabase wrapper from langchain_community
db_uri = f"sqlite:///{db_path}"
db = SQLDatabase.from_uri(db_uri)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# A safe prompt prefix that asks the model to always show the SQL in explanation
PREFIX = """
You are an assistant that translates natural language to SQL for a read-only SQL database.
- Always return the SQL query you intend to run in a separate block labelled SQL_QUERY between triple backticks.
- Do NOT run destructive statements (INSERT, UPDATE, DELETE, DROP, ALTER).
- Limit results sensibly (e.g., use LIMIT) unless the user asks for all rows.
- After the SQL, return the final human-readable answer.
"""

FORMAT_INSTRUCTIONS = """
Return format:
- Include a SQL code block like:
```sql
SQL_QUERY:
SELECT ...
"""
# Query Section
st.subheader("2) Ask a question about your database")

user_query = st.text_input(
    "Enter your natural language query:",
    placeholder="e.g., What is the highest salary? Show average salary by department. Plot salary distribution."
)

run = st.button("Run Query")

if run and user_query:
    try:
        agent = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            verbose=True,
            return_intermediate_steps=True
        )

        result = agent.invoke({"input": user_query})

        final_answer = result["output"]

        # Show answer
        st.subheader("Answer")
        st.write(final_answer)

        # Extract SQL
        st.subheader("SQL Query Used")

        steps = result.get("intermediate_steps", [])
        sql_found = False
        extracted_sql = ""

        for step in steps:
            tool_call = step[0]
            if hasattr(tool_call, "tool_input"):
                extracted_sql = tool_call.tool_input
                st.code(extracted_sql, language="sql")
                sql_found = True

        if not sql_found:
            st.info("No SQL query generated.")

        # Save to history
        st.session_state.history.append(
            (user_query, final_answer, extracted_sql if sql_found else None)
        )

    except Exception as e:
        st.error(f"Error: {e}")

# Conversation History
if st.session_state.history:
    st.subheader("3) Conversation History")
    for i, (q, a, sql) in enumerate(st.session_state.history):
        st.markdown(f"**Q{i+1}:** {q}")
        st.markdown(f"**A{i+1}:** {a}")
        if sql:
            st.code(sql, language="sql")
        st.markdown("---")
