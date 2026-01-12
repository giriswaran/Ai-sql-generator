from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# ✅ define key FIRST
key = os.getenv("OPENAI_API_KEY")

# ✅ initialize client
client = OpenAI(api_key=key)

app = FastAPI()

class QueryRequest(BaseModel):
    db_schema: str
    question: str

@app.post("/generate-sql")
def generate_sql(data: QueryRequest):
    try:
        prompt = f"""
You are an expert SQL developer.

Use ONLY the following database schema:
{data.db_schema}

STRICT RULES:
- Output ONLY a valid SQL query
- DO NOT explain the query
- DO NOT add comments
- DO NOT add markdown
- DO NOT add backticks
- DO NOT add any text before or after the SQL

Question:
{data.question}
"""

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt
        )

        sql = response.output[0].content[0].text.strip()
        return {"sql": sql}

    except Exception as e:
        return {"error": str(e)}
import streamlit as st
import requests
import pyperclip

# Page config
st.set_page_config(
    page_title="AI SQL Generator",
    page_icon="🧠",
    layout="centered"
)

# Title
st.title("🧠 AI NLP → SQL Generator")
st.markdown(
    "Convert **natural language questions** into **SQL queries** using AI."
)

st.divider()

# Schema input
st.subheader("📂 Database Schema")
schema = st.text_area(
    label="Enter your database schema",
    height=150,
    placeholder="Example:\nemployees(id, name, salary, department)"
)

# Question input
st.subheader("❓ Your Question")
question = st.text_input(
    label="Ask in plain English",
    placeholder="Example: count employees in sales department"
)

st.divider()

# Generate button
if st.button("🚀 Generate SQL", use_container_width=True):

    if not schema.strip():
        st.warning("⚠️ Please enter the database schema.")
    elif not question.strip():
        st.warning("⚠️ Please enter a question.")
    else:
        with st.spinner("Generating SQL..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/generate-sql",
                    json={
                        "db_schema": schema,
                        "question": question
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()

                    if "sql" in result:
                        st.success("✅ SQL generated successfully")
                        sql = result["sql"].replace("```sql", "").replace("```", "").strip()
                        
                        st.code(sql, language="sql")
                        st.button("📋 Copy SQL to Clipboard", on_click=lambda: st.write("Copied!"))

                    else:
                        st.error("❌ Unexpected response format")
                        st.json(result)

                else:
                    st.error(f"❌ Server error: {response.status_code}")
                    st.text(response.text)

            except Exception as e:
                st.error("❌ Could not connect to backend")
                st.text(str(e))

st.divider()

# Footer
st.caption("Created by Giriswaran")
@app.post("/explain-sql")
def explain_sql(data: QueryRequest):
    try:
        prompt = f"""
Explain the following SQL query in simple English.

SQL Query:
{data.question}

Rules:
- Explain step by step
- Use simple language
- Do NOT generate SQL
"""

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt
        )

        explanation = response.output[0].content[0].text.strip()
        return {"explanation": explanation}

    except Exception as e:
        return {"error": str(e)}
