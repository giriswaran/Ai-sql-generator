import streamlit as st
import requests
import pyperclip
import streamlit.components.v1 as components

if "explaining" not in st.session_state:
    st.session_state.explaining = False

# Load theme from browser localStorage (once)
components.html(
    """
    <script>
    const theme = localStorage.getItem("theme");
    if (theme) {
        window.location.search = "?theme=" + theme;
    }
    </script>
    """,
    height=0
)

# Read theme from query params
if "theme" not in st.session_state:
    st.session_state.theme = st.query_params.get("theme", "light")

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

top_left, spacer, sun, moon = st.columns([6, 2, 1, 1])

def apply_theme(theme):
    def apply_theme(theme):
        if theme == "dark":
            st.markdown(
                """
                <style>
                /* Cursor (caret) in DARK mode */
                textarea, input, .stTextInput input, .stTextArea textarea {
                    caret-color: #ffffff !important;  /* bright white */
                }
                </style>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <style>
                /* Cursor (caret) in LIGHT mode */
                textarea, input, .stTextInput input, .stTextArea textarea {
                caret-color: #000000 !important;  /* solid black */
                }
                </style>
                """,
                unsafe_allow_html=True
            )

apply_theme(st.session_state.theme)

# Title
st.title("🧠 AI NLP → SQL Generator")
st.markdown("Convert **natural language questions** into **SQL queries** using AI.")

st.divider()

# Schema input
st.subheader("📂 Database Schema")

schema_text = st.text_area(
    label="",
    height=180,
    placeholder=(
        "Type your schema here..."        
    )
)
col_plus, col_hint = st.columns([1, 9])

with col_plus:
    schema_image = st.file_uploader(
        "➕",
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed"
    )

with col_hint:
    st.caption("Upload / paste schema screenshot")

# Question input
question = st.text_area(
    "❓ Ask in plain English",
    height=120,
    placeholder="count employees in sales department"
)

st.divider()

# Generate button
# Generate button
if st.button("🚀 Generate SQL", use_container_width=True):

    if not question.strip():
        st.warning("⚠️ Please enter a question.")
    elif not schema_text.strip() and not schema_image:
        st.warning("⚠️ Provide schema text or upload schema image.")
    else:
        with st.spinner("Analyzing schema and generating SQL..."):
            files = {}
            data = {
                "question": question,
                
                "schema_text": schema_text   # ✅ FIXED
            }

            if schema_image:
                files["schema_image"] = schema_image

            response = requests.post(
                "http://127.0.0.1:8000/generate-sql-hybrid",
                data=data,
                files=files if files else None,
                timeout=90
            )

            if response.status_code == 200:
                st.session_state.sql = response.json()["sql"]
                st.success("SQL generated successfully")
            else:
                st.error("Failed to generate SQL")

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

            st.session_state.show_explanation = True

            # Generate explanation ONLY ONCE
            if not st.session_state.explanation:
                st.session_state.explaining = True

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

                st.session_state.explaining = False

st.divider()
if st.session_state.show_explanation and st.session_state.explanation:
    with st.expander("📖 SQL Explanation", expanded=True):
        st.write(st.session_state.explanation)

st.caption("Created by Giriswaran")

        
