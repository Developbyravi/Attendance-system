"""
AIoT SmartAttend — Remove All Students Script
-----------------------------------------------
Deletes all student records, face embeddings, stored enrollment face image files,
daily RFID check-ins, and lecture attendance records while preserving teacher accounts.
"""

import sys
import os
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.config import settings
from app.models.student import StudentModel
from app.models.face_embedding import FaceEmbeddingModel
from app.models.daily_checkin import DailyCheckinModel
from app.models.lecture_attendance import LectureAttendanceModel
from app.models.lecture_session import LectureSessionModel
from app.models.teacher import TeacherModel

def remove_all_students():
    print("==================================================")
    print("  AIoT SmartAttend -- REMOVE ALL STUDENTS  ")
    print("==================================================")
    db = SessionLocal()

    try:
        # Delete dependent attendance and face embedding records
        deleted_attendances = db.query(LectureAttendanceModel).delete()
        deleted_checkins = db.query(DailyCheckinModel).delete()
        deleted_lectures = db.query(LectureSessionModel).delete()
        deleted_embeddings = db.query(FaceEmbeddingModel).delete()
        deleted_students = db.query(StudentModel).delete()

        db.commit()

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
        print("Database state after student removal:")
        print(f"  Students:            {db.query(StudentModel).count()}")
        print(f"  Teachers:            {db.query(TeacherModel).count()}")
        print(f"  Face Embeddings:     {db.query(FaceEmbeddingModel).count()}")
        print(f"  Daily Check-ins:     {db.query(DailyCheckinModel).count()}")
        print(f"  Lecture Sessions:    {db.query(LectureSessionModel).count()}")
        print(f"  Lecture Attendances: {db.query(LectureAttendanceModel).count()}")
        print("--------------------------------------------------")
        print(f"Successfully deleted {deleted_students} student records!")

    except Exception as err:
        db.rollback()
        print(f"Error removing students: {err}")
        sys.exit(1)

    finally:
        db.close()

if __name__ == "__main__":
    remove_all_students()
