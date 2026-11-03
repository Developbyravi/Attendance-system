"""
AIoT SmartAttend — Database Reset Script
----------------------------------------
EXPLICIT MANUAL USE ONLY.
Deletes all students, teachers, face embeddings, attendance sessions,
daily checkins, lecture sessions, lecture attendances, RFID events,
AI detections, verification matrix entries, final attendance records,
and stored student face image files.

Run explicitly via:
  python backend/scripts/reset_database.py
"""

import sys
import os
import shutil

# Ensure backend root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.database import engine, Base, SessionLocal
from app.config import settings
import app.models

def reset_database():
    print("==================================================")
    print("  AIoT SmartAttend -- MANUAL DATABASE RESET  ")
    print("==================================================")

    # Drop and recreate all tables to align SQLite schema with updated models
    print("Recreating database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("Database tables recreated successfully.")

        # Reset SQLite autoincrement sequences safely
        try:
            db.execute(text("DELETE FROM sqlite_sequence;"))
            db.commit()
        except Exception:
            db.rollback()

        print("Database tables cleared successfully.")

        # Clear stored face images directory
        if os.path.exists(settings.STORAGE_DIR):
            for filename in os.listdir(settings.STORAGE_DIR):
                filepath = os.path.join(settings.STORAGE_DIR, filename)
                try:
                    if os.path.isfile(filepath) or os.path.islink(filepath):
                        os.unlink(filepath)
                    elif os.path.isdir(filepath):
                        shutil.rmtree(filepath)
                except Exception as e:
                    print(f"Failed to delete stored file {filepath}: {e}")
            print(f"Cleared storage directory: {settings.STORAGE_DIR}")

        print("--------------------------------------------------")
        print("Database state after reset:")
        print(f"  Students:            {db.execute(text('SELECT COUNT(*) FROM students;')).scalar()}")
        print(f"  Teachers:            {db.execute(text('SELECT COUNT(*) FROM teachers;')).scalar()}")
        print(f"  Face Embeddings:     {db.execute(text('SELECT COUNT(*) FROM face_embeddings;')).scalar()}")
        print(f"  Daily Check-ins:     {db.execute(text('SELECT COUNT(*) FROM daily_checkins;')).scalar()}")
        print(f"  Lecture Sessions:    {db.execute(text('SELECT COUNT(*) FROM lecture_sessions;')).scalar()}")
        print(f"  Lecture Attendances: {db.execute(text('SELECT COUNT(*) FROM lecture_attendances;')).scalar()}")
        print("--------------------------------------------------")
        print("Database reset complete!")

    except Exception as err:
        db.rollback()
        print(f"Error during database reset: {err}")
        sys.exit(1)

    finally:
        db.close()

if __name__ == "__main__":
    reset_database()
