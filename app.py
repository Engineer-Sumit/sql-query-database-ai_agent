import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from ui.components import load_css, header, section, sidebar
from db.db_utils import init_db, import_csv, list_tables, get_schema_description
from agents.sql_agent import create_agent, run_query

from sklearn.ensemble import RandomForestRegressor
import shap
from lime.lime_tabular import LimeTabularExplainer
import matplotlib.pyplot as plt

# Helper Functions
def split_questions(text: str):
    text = text.replace("\n", " ").strip()
    parts = [q.strip() for q in text.split("?") if q.strip()]
    return [q + "?" for q in parts]

def is_explain_query(q: str):
    keywords = ["impact", "affect", "influence", "factor", "why", "reason"]
    return any(k in q.lower() for k in keywords)

# Setup
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Database AI Agent", layout="wide")
load_css()
header()

with st.sidebar:
    sidebar()

db_path = "./db/app.db"
engine = init_db(db_path)
db_uri = f"sqlite:///{db_path}"
agent = create_agent(db_uri, API_KEY)

# 📂 Upload CSV
section("📂 Upload CSV", "Upload CSV files to create SQL tables")

uploaded = st.file_uploader("Upload CSV", type="csv", accept_multiple_files=True)

if uploaded:
    for f in uploaded:
        table = import_csv(engine, f)
        st.success(f"Imported table: {table}")

tables = list_tables(engine)
if tables:
    st.info(f"Loaded tables: {', '.join(tables)}")

# 💬 Query Section
section("💬 Ask a Question", "Use natural language to query your database")

query = st.text_input("Ask something…")

if st.button("🚀 Run Query") and query:

    # LIMIT SCHEMA (IMPORTANT FIX)
    schema_info = get_schema_description(engine)[:1500]

    questions = split_questions(query)

    for idx, q in enumerate(questions, start=1):

        st.markdown(f"### {idx}️⃣ {q}")

        # EXPLAIN QUERY → SKIP SQL
        if is_explain_query(q):

            st.markdown("**✍🏻 Answer**")
            st.write("Analyzing what factors influence the data...")

            # Load limited dataset
            df_query = pd.read_sql(f"SELECT * FROM {tables[0]} LIMIT 300", engine)

        else:

            # NORMAL SQL QUERY

            enhanced_query = f"""
You are working with a SQLite database.

Database schema:
{schema_info}

Instructions:
- Use ONLY the tables and columns from the schema.
- Do NOT guess table names.

User question:
{q}
"""

            result = run_query(agent, enhanced_query)

            if "error" in result:
                st.error(result["error"])
                continue

            if "answer" in result:
                st.markdown("**✍🏻 Answer**")
                st.write(result["answer"])

            with st.expander("View Generated SQL"):
                st.code(result["sql"], language="sql")

            rows = result.get("rows", [])
            columns = result.get("columns")

            if rows:
                df_query = pd.DataFrame(rows, columns=columns)
            else:
                st.info("No results returned.")
                continue

        # DISPLAY DATA
        st.dataframe(df_query, use_container_width=True)

        if df_query.shape[1] == 2:
            col1, col2 = df_query.columns
            if df_query[col1].dtype == "object" and pd.api.types.is_numeric_dtype(df_query[col2]):
                st.bar_chart(df_query.set_index(col1)[col2])

        elif df_query.shape == (1, 1):
            value = df_query.iloc[0, 0]
            try:
                value = f"{float(value):,}"
            except:
                pass
            st.metric(label="Result", value=value)

        # AUTO AI EXPLANATION
        if is_explain_query(q):

            st.markdown("## 🤖 AI Explanation (SHAP + LIME)")

            df = df_query.copy()

            # SAMPLE DATA (IMPORTANT)
            df = df.sample(min(200, len(df)))

            df_numeric = df.select_dtypes(include=["number"])

            if df_numeric.shape[1] < 2:
                st.warning("Not enough numeric data")
                continue

            if df_numeric.shape[0] <= 5:
                st.warning("Not enough rows")
                continue

            target_col = df_numeric.columns[-1]

            X = df_numeric.drop(columns=[target_col])
            y = df_numeric[target_col]

            with st.spinner("🔄 Running AI analysis..."):
                model = RandomForestRegressor()
                model.fit(X, y)

            # 🔍 SHAP
            st.subheader("📝 SHAP Feature Importance")
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)

            plt.clf()
            fig, ax = plt.subplots()
            shap.summary_plot(shap_values, X, show=False)
            st.pyplot(fig)

            # SHAP summary
            mean_abs = abs(shap_values).mean(axis=0)
            importance = sorted(zip(X.columns, mean_abs), key=lambda x: x[1], reverse=True)

            summary_prompt = f"""
Target: {target_col}
Top features: {importance[:3]}
Explain briefly what affects target.
"""
            summary = agent["llm"].invoke(summary_prompt).content

            st.markdown("### ➤ SHAP Summary")
            st.write(summary)

            # 🧪 LIME
            st.subheader("📝 LIME Explanation")

            explainer_lime = LimeTabularExplainer(
                X.values,
                feature_names=X.columns,
                mode="regression"
            )

            exp = explainer_lime.explain_instance(
                X.iloc[0].values,
                lambda x: model.predict(pd.DataFrame(x, columns=X.columns))
            )

            fig2 = exp.as_pyplot_figure()
            st.pyplot(fig2)

            lime_prompt = f"""
Explain this prediction:
{exp.as_list()}
"""
            lime_summary = agent["llm"].invoke(lime_prompt).content

            st.markdown("### ➤ LIME Summary")
            st.write(lime_summary)