import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import logger
from app.db.database import engine as default_engine, Base
from app.db.models.user import User, UserRole
from app.db.models.facility import ScreeningCenter
from app.core.security import get_password_hash

# Import API routers
from app.api import (
    health, auth, predictions, screenings, patients, referrals,
    reviews, specialists, analytics, models, settings as settings_api,
    users, facilities, reports, sync, images
)

def seed_database(bind_engine=None):
    """Initializes tables and seeds default facilities and demo users"""
    target_engine = bind_engine or default_engine
    Base.metadata.create_all(bind=target_engine)
    SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=target_engine)
    db: Session = SessionMaker()
    try:
        # Seed default screening center
        facility = db.query(ScreeningCenter).first()
        if not facility:
            facility = ScreeningCenter(
                name="Mandya Primary Health Centre",
                facility_type="PHC",
                village="Mandya Rural",
                block="Mandya",
                district="Mandya",
                state="Karnataka",
                address="Main Road, Mandya District"
            )
            db.add(facility)
            db.commit()
            db.refresh(facility)

        # Seed default demo users for all roles
        default_users = [
            {
                "user_id": "admin",
                "name": "System Administrator",
                "role": UserRole.ADMIN,
                "email": "admin@netradrishti.org",
                "password": "admin123"
            },
            {
                "user_id": "asha",
                "name": "Lakshmi Gowda (ASHA Worker)",
                "role": UserRole.ASHA,
                "email": "asha@netradrishti.org",
                "password": "asha123",
                "facility_id": facility.id,
                "district": "Mandya"
            },
            {
                "user_id": "doctor",
                "name": "Dr. Rajesh Kumar (PHC Doctor)",
                "role": UserRole.PHC_DOCTOR,
                "email": "doctor@netradrishti.org",
                "password": "doctor123",
                "facility_id": facility.id,
                "district": "Mandya"
            },
            {
                "user_id": "specialist",
                "name": "Dr. Ananya Sharma (Ophthalmologist)",
                "role": UserRole.OPHTHALMOLOGY_DOCTOR,
                "email": "specialist@netradrishti.org",
                "password": "specialist123",
                "district": "Mandya"
            }
        ]

        for raw_data in default_users:
            u_data = dict(raw_data)
            u_id = u_data["user_id"]
            existing = db.query(User).filter(User.user_id == u_id).first()
            if not existing:
                pwd = u_data.pop("password")
                user = User(password_hash=get_password_hash(pwd), **u_data)
                db.add(user)
                
        db.commit()
        logger.info("Database seeding completed successfully.")
    except Exception as e:
        logger.error(f"Seeding error: {str(e)}")
        db.rollback()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_database()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Explainable AI for Diabetic Retinopathy Screening in Rural India — Production REST Backend API",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predictions.router) # Legacy POST /predict wrapper
app.include_router(screenings.router)
app.include_router(patients.router)
app.include_router(referrals.router)
app.include_router(reviews.router)
app.include_router(specialists.router)
app.include_router(analytics.router)
app.include_router(models.router)
app.include_router(settings_api.router)
app.include_router(users.router)
app.include_router(facilities.router)
app.include_router(reports.router)
app.include_router(sync.router)
app.include_router(images.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
