import os
import base64
import sqlite3
import re
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from openai import OpenAI
from dotenv import load_dotenv

# -------------------- ENV & APP SETUP --------------------
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
app = FastAPI()

# -------------------- DATABASE SETUP --------------------
def init_db():
    conn = sqlite3.connect("project_data.db")
    cursor = conn.cursor()
    # Ensure the table is created with the email column
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, 
                       username TEXT UNIQUE, 
                       email TEXT UNIQUE, 
                       password TEXT)''')
    conn.commit()
    conn.close()



# Run initialization
init_db()

# -------------------- HELPER FUNCTIONS --------------------

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def login_user_db(identifier, password):
    """Checks both username and email columns for the given identifier."""
    conn = sqlite3.connect("project_data.db")
    cursor = conn.cursor()
    # The OR condition allows either username or email login
    query = "SELECT id FROM users WHERE (username=? OR email=?) AND password=?"
    cursor.execute(query, (identifier, identifier, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def save_history_to_db(user_id, question, sql_query):
    conn = sqlite3.connect("project_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (user_id, question, sql_query, timestamp) VALUES (?, ?, ?, ?)",
                   (user_id, question, sql_query, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_history_from_db(user_id):
    conn = sqlite3.connect("project_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT question, sql_query, timestamp FROM history WHERE user_id=? ORDER BY id DESC", (user_id,))
    data = cursor.fetchall()
    conn.close()
    return data

# -------------------- API ENDPOINTS --------------------

@app.post("/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if not is_valid_email(email):
        return {"status": "fail", "message": "Invalid email format"}
    
    conn = sqlite3.connect("project_data.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                       (username, email, password))
        conn.commit()
        return {"status": "success", "message": "User created successfully"}
    except sqlite3.IntegrityError:
        return {"status": "fail", "message": "Username or Email already exists"}
    except Exception as e:
        return {"status": "fail", "message": str(e)}
    finally:
        conn.close()

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect("project_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE (username=? OR email=?) AND password=?", 
                   (username, username, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"status": "success", "user_id": user[0]}
    return {"status": "fail", "message": "Invalid credentials"}


    
    # Check if the email exists in the users table
    cursor.execute("SELECT password FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # Returns the password for recovery
        return {"status": "success", "password": user[0]}
    else:
        # Returns failure if the email is not in the DB
        return {"status": "fail", "message": "Email not found in our database."}
    
@app.get("/history/{user_id}")
def fetch_history(user_id: int):
    data = get_history_from_db(user_id)
    return {"history": data}

@app.post("/generate-sql-hybrid")
async def generate_sql_hybrid(
    question: str = Form(...),
    schema_text: str = Form(""),
    user_id: int = Form(None), 
    schema_image: UploadFile = File(None)
):
    try:
        system_instructions = f"""Output ONLY raw SQL. No markdown. Use this schema:\n{schema_text}"""
        messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": [{"type": "text", "text": f"Question: {question}"}]}
        ]

        if schema_image:
            image_bytes = await schema_image.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            })

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0
        )

        sql = response.choices[0].message.content.strip()
        if user_id:
            save_history_to_db(user_id, question, sql)
        return {"sql": sql}
    except Exception as e:
        return {"error": str(e)}
