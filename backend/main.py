from fastapi import FastAPI
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/users")
def get_users():
    response = supabase.table('users').select("*").execute()
    return response
