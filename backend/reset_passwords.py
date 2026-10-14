"""One-shot script to reset all user passwords in the SQLite database."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import bcrypt
from sqlalchemy import create_engine, text

DB_PATH = os.path.join(os.path.dirname(__file__), "security_compliance.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

NEW_PASSWORD = "Rathesh@123"

# Hash the new password using native bcrypt (matching security.py)
pwd_bytes = NEW_PASSWORD.encode("utf-8")[:72]
hashed = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")

engine = create_engine(DATABASE_URL, echo=False)

with engine.connect() as conn:
    result = conn.execute(text("SELECT id, email FROM users"))
    users = result.fetchall()

    for user in users:
        conn.execute(
            text("UPDATE users SET password_hash = :hash WHERE id = :id"),
            {"hash": hashed, "id": user[0]}
        )
        print(f"  [OK] Reset: {user[1]}")

    conn.commit()

print(f"\n[DONE] All {len(users)} users now use password: {NEW_PASSWORD}")
