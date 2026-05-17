import sqlite3
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(
    title="API ONG SAMA",
    description="Serveur hautement sécurisé et optimisé pour la gestion des membres.",
    version="1.1.0"
)

# 🔐 SÉCURITÉ CORS : Remplace par l'adresse exacte de ton site GitHub Pages
# Exemple : ["https://christyvane.github.io", "http://localhost:5500"]
ORIGINES_AUTORISEES = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINES_AUTORISEES,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # On n'autorise que le strict nécessaire
    allow_headers=["Content-Type"],
)

DB_NAME = "ong_data.db"

# 📐 Modèle de données strict et sécurisé
class MembreInscription(BaseModel):
    nom: str = Field(..., min_length=2, max_length=100, description="Nom et prénoms complets")
    email: EmailStr = description="Adresse e-mail valide"
    telephone: str = Field(..., min_length=8, max_length=20, description="Numéro de téléphone avec indicatif")

    # Nettoyage automatique des données reçues
    def nettoyer_donnees(self):
        return {
            "nom": self.nom.strip().title(),
            "email": self.email.strip().lower(),
            "telephone": self.telephone.strip().replace(" ", "")
        }

# 🛠️ Initialisation robuste de la base de données
def initialiser_bdd():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS membres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                email TEXT NOT NULL,
                telephone TEXT NOT NULL,
                date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

initialiser_bdd()

@app.get("/", status_code=status.HTTP_200_OK)
def page_accueil():
    return {"status": "online", "message": "Serveur ONG SAMA sécurisé et opérationnel."}

# 📥 1. Route POST d'inscription blindée
@app.post("/inscription", status_code=status.HTTP_201_CREATED)
def inscription(membre: MembreInscription):
    donnees = membre.nettoyer_donnees()
    
    try:
        # Le 'with' sécurise la connexion et gère les fermetures proprement
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            
            # Vérification si l'e-mail existe déjà pour éviter les doublons
            cursor.execute("SELECT id FROM membres WHERE email = ?", (donnees["email"],))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cette adresse e-mail est déjà inscrite."
                )
                
            # Insertion sécurisée
            cursor.execute(
                "INSERT INTO membres (nom, email, telephone) VALUES (?, ?, ?)",
                (donnees["nom"], donnees["email"], donnees["telephone"])
            )
            conn.commit()
            
        return {"status": "success", "message": "Inscription validée avec succès !"}
        
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'enregistrement en base de données : {str(e)}"
        )

# 📤 2. Route GET de récupération optimisée pour l'espace Admin
@app.get("/membres", status_code=status.HTTP_200_OK)
def obtenir_les_membres():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            # On trie par date pour voir les plus récents en premier
            cursor.execute("SELECT nom, email, telephone FROM membres ORDER BY date_inscription DESC")
            lignes = cursor.fetchall()
        
        # Construction propre de la réponse JSON
        return [
            {"nom": ligne[0], "email": ligne[1], "telephone": ligne[2]}
            for ligne in lignes
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des données : {str(e)}"
        )
