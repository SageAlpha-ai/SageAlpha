# create_users.py - Local script for seeding DB
from models import db, User
from app import app
from werkzeug.security import generate_password_hash   # ← FIXED

def create_users():
    with app.app_context():
        db.create_all()
        users = [
            ("demouser", "DemoUser", "DemoPass123!"),
            ("devuser", "DevUser", "DevPass123!"),
            ("produser", "ProductionUser", "ProdPass123!"),
        ]
        for username, display, pwd in users:
            if not User.query.filter_by(username=username).first():
                u = User(
                    username=username,
                    display_name=display,
                    password_hash=generate_password_hash(pwd),
                )
                db.session.add(u)
        db.session.commit()
        print("Created test users: demouser / devuser / produser")

if __name__ == "__main__":
    create_users()
