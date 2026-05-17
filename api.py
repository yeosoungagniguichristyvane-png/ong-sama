import sqlite3
from fastapi import FastAPI # type: ignore
from fastapi import HTTPException # type: ignore
from fastapi import Depends # type: ignore
from fastapi.security.api_key import APIKeyHeader # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from pydantic import BaseModel, EmailStr # type: ignore

app = FastAPI(title="API Privée - ONG SAMA", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

API_KEY = "SAMA_SECURE_KEY_2026"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verifier_cle_api(hd: str = Depends(api_key_header)):
    if hd != API_KEY:
        raise HTTPException(status_code=401, detail="Accès non autorisé.")
    return hd

class MembreInscription(BaseModel):
    nom: str
    email: EmailStr
    telephone: str

def initialiser_bdd():
    conn = sqlite3.connect("ong_data.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS membres (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT NOT NULL, email TEXT NOT NULL, telephone TEXT NOT NULL)")
    conn.commit()
    conn.close()

initialiser_bdd()

@app.get("/")
def health_check():
    return {"status": "online"}

@app.post("/inscription")
def inscription(m: MembreInscription):
    try:
        conn = sqlite3.connect("ong_data.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO membres (nom, email, telephone) VALUES (?, ?, ?)", (m.nom, m.email, m.telephone))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/membres/{m_id}")
def modifier_membre(m_id: int, m: MembreInscription, cl: str = Depends(verifier_cle_api)):
    try:
        conn = sqlite3.connect("ong_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM membres WHERE id = ?", (m_id,))
        if cursor.fetchone() is None:
            conn.close()
            raise HTTPException(status_code=404, detail="Introuvable.")
        cursor.execute("UPDATE membres SET nom=?, email=?, telephone=? WHERE id=?", (m.nom, m.email, m.telephone, m_id))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.delete("/membres/{m_id}")
def supprimer_membre(m_id: int, cl: str = Depends(verifier_cle_api)):
    try:
        conn = sqlite3.connect("ong_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM membres WHERE id = ?", (m_id,))
        if cursor.fetchone() is None:
            conn.close()
            raise HTTPException(status_code=404, detail="Introuvable.")
        cursor.execute("DELETE FROM membres WHERE id = ?", (m_id,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/membres")
def list_membres(cl: str = Depends(verifier_cle_api)):
    try:
        conn = sqlite3.connect("ong_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, email, telephone FROM membres ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "nom": r[1], "email": r[2], "telephone": r[3]} for r in rows] # type: ignore
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
