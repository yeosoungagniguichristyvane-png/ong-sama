import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

# 1. Initialisation de l'application FastAPI
app = FastAPI(title="API-ONG-SAMA")

# 2. Configuration du CORS pour que ton site HTML puisse communiquer avec l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permet les requêtes depuis n'allant de n'importe où (GitHub Pages ou local)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Modèle de données pour valider les informations reçues du formulaire HTML
class MembreInscription(BaseModel):
    nom: str
    email: EmailStr
    telephone: str

# 4. Initialisation automatique de la base de données SQLite au démarrage
def initialiser_db():
    conn = sqlite3.connect("ong_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS membres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            telephone TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

initialiser_db()

# 5. Fonction pour envoyer le mail de bienvenue via Gmail
def envoyer_mail_bienvenue(nom_destinataire: str, email_destinataire: str):
    email_ong = "ong.sama.sanpedro@gmail.com"
    
    # Sécurité : Render récupérera le mot de passe dans ses variables d'environnement
    mot_de_passe_ong = os.getenv("GMAIL_PASSWORD")

    # Si le mot de passe n'est pas encore configuré sur Render, on évite de faire crash le serveur
    if not mot_de_passe_ong:
        print("Erreur : La variable d'environnement GMAIL_PASSWORD n'est pas définie.")
        return

    # Construction du message email
    message = MIMEMultipart()
    message["From"] = email_ong
    message["To"] = email_destinataire
    message["Subject"] = "Félicitations et Bienvenue chez ONG-SAMA ! 🎉"

    corps_texte = f"""Bonjour {nom_destinataire},

Toute l'équipe de l'ONG-SAMA est heureuse de vous compter parmi ses nouveaux membres !

Votre inscription a été validée avec succès. Ensemble, nous allons mener des actions fortes pour la solidarité et le développement.

Nous vous contacterons très bientôt sur votre numéro de téléphone pour les prochaines étapes et réunions.

Cordialement,
Le secrétariat de l'ONG-SAMA
San Pedro, Côte d'Ivoire
"""
    message.attach(MIMEText(corps_texte, "plain", "utf-8"))

    try:
        # Connexion sécurisée au serveur SMTP de Gmail
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as serveur:
            serveur.login(email_ong, mot_de_passe_ong)
            serveur.send_message(message)
        print(f"Mail de bienvenue envoyé avec succès à {email_destinataire}")
    except Exception as e:
        # Si l'envoi d'email échoue, on l'affiche dans les logs sans bloquer l'inscription
        print(f"Erreur lors de l'envoi de l'email : {e}")

# 6. Route POST pour recevoir les inscriptions du formulaire
@app.post("/inscription")
def inscription(membre: MembreInscription):
    try:
        conn = sqlite3.connect("ong_data.db")
        cursor = conn.cursor()
        
        # Insertion du nouveau membre dans la base SQLite
        cursor.execute(
            "INSERT INTO membres (nom, email, telephone) VALUES (?, ?, ?)",
            (membre.nom, membre.email, membre.telephone)
        )
        conn.commit()
        conn.close()
        
        # Déclenchement de l'envoi du mail de bienvenue
        envoyer_mail_bienvenue(membre.nom, membre.email)
        
        return {
            "statut": "success", 
            "message": f"Félicitations {membre.nom}, votre inscription a été enregistrée avec succès !"
        }
    
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Cette adresse email est déjà enregistrée.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur : {str(e)}")
