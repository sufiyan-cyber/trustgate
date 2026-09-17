"""Database seeding script for Trust Gate."""
import uuid
from datetime import datetime, timezone, timedelta
from app.database import SessionLocal, init_db
from app.models import Participant, Registration, IdentityDocument, VerificationSession, ReviewAction
from app.core.security import hash_id_number

def seed_database():
    print("[INFO] Initializing database tables...")
    init_db()
    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(Participant).filter(Participant.email == "sufiyan.a@tech.ac.in").first()
        if existing:
            print("[INFO] Database already seeded. Skipping initial seeding.")
            return

        print("[INFO] Seeding initial test participants and registrations...")

        # 1. Sufiyan Ahmed (Existing owner of ID KA123456)
        sufiyan = Participant(
            id=str(uuid.uuid4()),
            name="Sufiyan Ahmed",
            email="sufiyan.a@tech.ac.in",
            phone="+91-9888776655",
            institution="National Institute of Technology",
            is_demo=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=7)
        )
        db.add(sufiyan)
        db.flush()

        sufiyan_reg = Registration(
            id=str(uuid.uuid4()),
            participant_id=sufiyan.id,
            event_id="hackingly-hackathon-2026",
            status="VERIFIED",
            is_demo=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=7)
        )
        db.add(sufiyan_reg)
        db.flush()

        sufiyan_doc = IdentityDocument(
            id=str(uuid.uuid4()),
            registration_id=sufiyan_reg.id,
            document_type="COLLEGE_ID",
            document_number_hash=hash_id_number("KA123456"),  # Stored hash!
            name="Sufiyan Ahmed",
            dob="2002-06-14",
            institution="National Institute of Technology",
            image_path=None,
            created_at=datetime.now(timezone.utc) - timedelta(days=7)
        )
        db.add(sufiyan_doc)

        # 2. Elena Rostova (Verified participant)
        elena = Participant(
            id=str(uuid.uuid4()),
            name="Elena Rostova",
            email="elena.r@mit.edu",
            phone="+1-555-7731",
            institution="MIT",
            is_demo=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=2)
        )
        db.add(elena)
        db.flush()

        elena_reg = Registration(
            id=str(uuid.uuid4()),
            participant_id=elena.id,
            event_id="hackingly-hackathon-2026",
            status="VERIFIED",
            is_demo=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=2)
        )
        db.add(elena_reg)
        db.flush()

        elena_doc = IdentityDocument(
            id=str(uuid.uuid4()),
            registration_id=elena_reg.id,
            document_type="COLLEGE_ID",
            document_number_hash=hash_id_number("MIT-991823"),
            name="Elena Rostova",
            dob="2003-11-20",
            institution="MIT",
            image_path=None,
            created_at=datetime.now(timezone.utc) - timedelta(days=2)
        )
        db.add(elena_doc)

        db.commit()
        print("[SUCCESS] Database seeded successfully with baseline participants.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
