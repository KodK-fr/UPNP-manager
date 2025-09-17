# Dockerfile

# Utiliser l’image de base Python 3.11
FROM python:3.11

# Définir le répertoire de travail
WORKDIR /app

# Copier tous les fichiers du projet
COPY . .

# Installer les dépendances
RUN if [ -f requirements.txt ]; then \
    pip install -r requirements.txt; \
else \
    pip install psutil pillow qrcode miniupnpc; \
fi

# Exposer le port 8080
EXPOSE 8080

# Lancer main.py
CMD ["python", "main.py"]
