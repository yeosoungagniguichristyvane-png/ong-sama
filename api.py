import sqlite3
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

app = FastAPI(title="API Privée - ONG SAMA", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "SAMA_SECURE_KEY_2026"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verifier_cle_api(header_key: str = Depends(api_key_header)):
    if header_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Accès non autorisé : Clé API invalide ou manquante.",
        )
    return header_key


class MembreInscription(BaseModel):
    nom: str
    email: EmailStr
    telephone: str


def initialiser_bdd():
    conn = sqlite3.connect("ong_data.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS membres (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nom       TEXT NOT NULL,
            email     TEXT NOT NULL,
            telephone TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


initialiser_bdd()


@app.get("/")
def health_check():
    return {"status": "online", "message": "Serveur ONG SAMA actif et sécurisé."}


@app.post("/inscription")
def inscription(membre: MembreInscription):
    try:
        conn = sqlite3.connect("ong_data.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO membres (nom, email, telephone) VALUES (?, ?, ?)",
            (membre.nom, membre.email, membre.telephone),
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Inscription réussie !"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/membres/{membre_id}")
def modifier_membre(membre_id: int, membre: MembreInscription, cle: str = Depends(verifier_cle_api)):
    try:
        conn = sqlite3.connect("ong_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM membres WHERE id = ?", (membre_id,))
        if cursor.fetchone() is None:
            conn.close()
            raise HTTPException(status_code=404, detail="Membre introuvable.")
        cursor.execute(
            "UPDATE membres SET nom = ?, email = ?, telephone = ? WHERE id = ?",
            (membre.nom, membre.email, membre.telephone, membre_id),
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Membre {membre_id} mis à jour avec succès."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/membres/{membre_id}")
def supprimer_membre(membre_id: int, cle: str = Depends(verifier_cle_api)):
    try:
        conn = sqlite3.connect("ong_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM membres WHERE id = ?", (membre_id,))
        if cursor.fetchone() is None:
            conn.close()
            raise HTTPException(status_code=404, detail="Membre introuvable.")
        cursor.execute("DELETE FROM membres WHERE id = ?", (membre_id,))
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Membre {membre_id} supprimé avec succès."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/membres")
def liste_membres(cle: str = Depends(verifier_cle_api)):
    try:
        conn = sqlite3.connect("ong_data.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nom, email, telephone FROM membres ORDER BY id"
        )
        rows = cursor.fetchall()
        conn.close()
        membres = []
        for row in rows:
            membres.append(
                {
                    "id": row[0],
                    "nom": row[1],
                    "email": row[2],
                    "telephone": row[3],
                }
            )
        return membres
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))