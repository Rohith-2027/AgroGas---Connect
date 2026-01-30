# backend/routes/farmer.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db, Record

router = APIRouter(prefix="/api/v1", tags=["Farmer"])

# ------------------------------------------------------
# SAVE RECORD (POST)
# ------------------------------------------------------
@router.post("/records")
async def save_record(payload: dict, db: Session = Depends(get_db)):

    required = [
        "farmer_name", "location", "phone",
        "mass_kg", "predicted_m3_biogas", "revenue_estimate"
    ]
    for field in required:
        if field not in payload:
            raise HTTPException(400, f"Missing: {field}")

    rec = Record(
        farmer_name=payload["farmer_name"],
        location=payload["location"],
        phone=payload["phone"],

        mass_kg=payload["mass_kg"],
        available_kg=payload["mass_kg"],        # NEW ✔

        moisture_percent=payload.get("moisture_percent"),
        vs_fraction=payload.get("vs_fraction"),

        predicted_m3_biogas=payload["predicted_m3_biogas"],
        revenue_estimate=payload["revenue_estimate"],

        timestamp=datetime.utcnow()
    )

    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {"message": "Record saved", "id": rec.id}


# ------------------------------------------------------
# LIST ALL RECORDS (GET)
# ------------------------------------------------------
@router.get("/records")
async def list_records(db: Session = Depends(get_db)):

    records = db.query(Record).order_by(Record.id.desc()).all()

    return [
        {
            "id": r.id,
            "farmer_name": r.farmer_name,
            "location": r.location,
            "phone": r.phone,
            "mass_kg": r.mass_kg,
            "available_kg": r.available_kg,      # ✔ NEW
            "moisture_percent": r.moisture_percent,
            "vs_fraction": r.vs_fraction,
            "predicted_m3_biogas": r.predicted_m3_biogas,
            "revenue_estimate": r.revenue_estimate,
            "timestamp": r.timestamp,
        }
        for r in records
    ]
