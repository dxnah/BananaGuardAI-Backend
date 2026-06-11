from fastapi import FastAPI
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

@app.get("/")
def root():
    return {"message": "BananaGuardAI Backend is running!"}

@app.get("/test-supabase")
def test_supabase():
    try:
        result = supabase.table("test").select("*").limit(1).execute()
        return {"status": "Connected to Supabase!"}
    except Exception as e:
        return {"status": "Error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)