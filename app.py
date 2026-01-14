from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
from fastapi import UploadFile, File, Form
from PIL import Image
import pytesseract

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

class QueryRequest(BaseModel):
    db_schema: str
    question: str

# If image is provided, extract text
@app.post("/generate-sql-hybrid")
async def generate_sql_hybrid(
    question: str = Form(...),
    schema_text: str = Form(""),
    schema_image: UploadFile = File(None)
):
    image_schema_text = ""

@app.post("/generate-sql")
def generate_sql(data: QueryRequest):
    prompt = f"""
You are an expert SQL developer.

Use ONLY the following database schema:
{data.db_schema}

STRICT RULES:
- Output ONLY SQL
- Do NOT explain
- Preserve NULL values
- Do NOT use COALESCE unless asked
- Prefer direct WHERE conditions
- Do NOT overcomplicate
- If question says "either A or B", use OR
- Do NOT invent tables or columns

Question:
{data.question}
"""

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    sql = response.output[0].content[0].text.strip()
    return {"sql": sql}


@app.post("/explain-sql")
def explain_sql(data: QueryRequest):
    prompt = f"""
Explain the following SQL query in simple English.

SQL:
{data.question}

Rules:
- Simple explanation
- Step by step
- Do NOT generate SQL
"""

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    explanation = response.output[0].content[0].text.strip()
    return {"explanation": explanation}
