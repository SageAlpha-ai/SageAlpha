# create_users.py

import os
from dotenv import load_dotenv

from werkzeug.security import generate_password_hash  # <-- ADD THIS IMPORT

from app import app
from models import db, User

load_dotenv()

DEMO_USERS = [
    ("demouser", "DemoUser", "DemoPass123!"),
    ("devuser", "DevUser", "DevPass123!"),
    ("produser", "ProductionUser", "ProdPass123!"),
]


def create_demo_users():
    with app.app_context():
        db.create_all()

        created_any = False
        for username, display_name, pwd in DEMO_USERS:
            existing = User.query.filter_by(username=username).first()
            if existing:
                print(f"[create_users] User '{username}' already exists, skipping.")
                continue

            user = User(
                username=username,
                display_name=display_name,
                password_hash=generate_password_hash(pwd),  # now defined
            )
            db.session.add(user)
            created_any = True
            print(f"[create_users] Will create user '{username}'.")

        if created_any:
            db.session.commit()
            print("[create_users] Demo users created.")
        else:
            print("[create_users] No users needed to be created.")


if __name__ == "__main__":
    create_demo_users()
