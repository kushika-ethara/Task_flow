"""
Run db.create_all() to ensure all tables exist.
Used as a Railway release command (runs before the web process starts).
"""
from app import app, db

with app.app_context():
    db.create_all()
    print("DB tables created/verified.")
