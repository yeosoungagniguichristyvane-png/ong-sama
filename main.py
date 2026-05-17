import sqlite3
from fastapi import FastAPI,  HTTPException, status; from fastapi.middleware.cors import CORSMiddleware; from pydantic import BaseModel, EmailStr

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MembreInscription(BaseModel):
    nom: str
    email: EmailStr
    telephone: str

def initialiser_bdd():
    conn = sqlite3.connect("ong_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS membres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT NOT NULL,
            telephone TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

initialiser_bdd()

@app.get("/")
def page_accueil():
    return {"message": "Serveur de l'ONG SAMA opérationnel et prêt !"}

@app.post("/inscription")
def inscription(membre: MembreInscription):
    try:
        conn = sqlite3.connect("ong_data.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO membres (nom, email, telephone) VALUES (?, ?, ?)",
            (membre.nom, membre.email, membre.telephone)
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Inscription enregistrée avec succès !"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
