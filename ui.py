import streamlit as st
import requests
import pyperclip

if "sql" not in st.session_state:
    st.session_state.sql = ""

if "explanation" not in st.session_state:
    st.session_state.explanation = ""

if "show_explanation" not in st.session_state:
    st.session_state.show_explanation = False

# Page config
st.set_page_config(
    page_title="AI SQL Generator",
    page_icon="🧠",
    layout="centered"
)

# Title
st.title("🧠 AI NLP → SQL Generator")
st.markdown("Convert **natural language questions** into **SQL queries** using AI.")

st.divider()

# Schema input
st.subheader("📂 Database Schema")
schema = st.text_area(
    "Enter your database schema",
    height=150,
    placeholder="employees(id, name, salary, department)"
)

# Question input
st.subheader("❓ Your Question")
question = st.text_input(
    "Ask in plain English",
    placeholder="count employees in sales department"
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
                    st.session_state.sql = (
                        result["sql"]
                        .replace("```sql", "")
                        .replace("```", "")
                        .strip()
                    )

                    # Reset explanation when new SQL is generated
                    st.session_state.explanation = ""
                    st.session_state.show_explanation = False

                    st.success("✅ SQL generated successfully")
                else:
                    st.error("❌ Unexpected response format")
            else:
                st.error("❌ Backend error")
if st.session_state.sql:
    st.code(st.session_state.sql, language="sql")

    col1, col2 = st.columns(2)

    # Copy SQL (WORKS NOW)
    with col1:
        if st.button("📋 Copy SQL"):
            pyperclip.copy(st.session_state.sql)
            st.success("Copied to clipboard!")

    # Explain SQL (TOGGLE)
    with col2:
        
        if st.button("🧠 Explain SQL"):

            # Always show explanation section
            st.session_state.show_explanation = True

            # Generate explanation ONLY ONCE
            if not st.session_state.explanation:
                with st.spinner("Explaining SQL..."):
                    explain_response = requests.post(
                        "http://127.0.0.1:8000/explain-sql",
                        json={
                            "db_schema": "",
                            "question": st.session_state.sql
                        },
                        timeout=60
                    )

                    if explain_response.status_code == 200:
                        st.session_state.explanation = (
                            explain_response.json().get("explanation", "")
                        )

st.divider()
st.caption("Created by Giriswaran")
if st.session_state.show_explanation and st.session_state.explanation:
    with st.expander("📖 SQL Explanation", expanded=True):
        st.write(st.session_state.explanation)

        if st.button("❌ Hide Explanation"):
            st.session_state.show_explanation = False
