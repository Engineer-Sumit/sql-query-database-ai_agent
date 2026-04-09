from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine, text


def create_agent(db_uri, api_key):
    llm = ChatOpenAI(
        api_key=api_key,
        model="gpt-3.5-turbo",
        temperature=0
    )

    db = SQLDatabase.from_uri(db_uri)
    engine = create_engine(db_uri)

    return {
        "llm": llm,
        "db": db,
        "engine": engine
    }


def run_query(agent, question):
    try:
        # Get actual table name (ONLY ONE TABLE ASSUMED)
        table_names = list(agent["db"].get_usable_table_names())
        if not table_names:
            raise ValueError("No tables found in database.")

        table_name = table_names[0]

        # Get schema
        schema = agent["db"].get_table_info()

        # HARD-CONSTRAINED PROMPT (NO GUESSING)
        prompt = f"""
You are an expert SQLite SQL developer.

CRITICAL RULES:
- The database has ONLY ONE table.
- The table name is EXACTLY: {table_name}
- You MUST use this table name.
- Do NOT invent table names like Employee, Employees, Salary.
- Use ONLY columns from the schema.
- Write ONLY ONE valid SQLite SELECT query.
- Return ONLY the SQL query. No explanation.

Database schema:
{schema}

Question:
{question}
"""

        # Correct method for new langchain_openai        
        sql = agent["llm"].invoke(prompt).content.strip()

        # Final safety check
        if table_name not in sql:
            raise ValueError(
                f"Generated SQL does not use required table '{table_name}'. SQL was: {sql}"
            )
                
        with agent["engine"].connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            columns = result.keys()

        answer_prompt = f"""
            You are a data analyst.

            The user asked:
            {question}

            The SQL query used was:
            {sql}

            The result returned from the database is:
            {rows}

            Explain the answer in a clean, human-friendly format.
               Formatting rules:
               - Start with a direct answer in ONE sentence.
               - If a number is involved, format it with commas.
               - Add a short explanation in the next sentence.
               - Keep it concise (2–3 sentences max).
               - Do NOT mention SQL or databases.
            """        
        natural_answer = agent["llm"].invoke(answer_prompt).content.strip()

        return {
            "sql": sql,
            "rows": rows,
            "columns": columns,
            "answer": natural_answer
        }

    except Exception as e:
        return {
            "error": str(e)
        }
