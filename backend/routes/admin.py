# backend/routes/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pathlib import Path
import json

from database import get_db, Config

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

DATA_JSON = Path(__file__).resolve().parent.parent / "data" / "config.json"

class ConfigIn(BaseModel):
    PRICE_PER_M3: float
    DEFAULT_YIELD_PER_KGVS: float
    DEFAULT_METHANE_FRACTION: float

@router.get("/config")
def get_config(db: Session = Depends(get_db)):
    # Try DB Config first
    cfg = db.query(Config).first()
    if cfg:
        return {
            "PRICE_PER_M3": cfg.price_per_m3,
            "DEFAULT_YIELD_PER_KGVS": cfg.default_yield_per_kgvs,
            "DEFAULT_METHANE_FRACTION": cfg.default_methane_fraction
        }

    # Fallback to JSON file
    try:
        if DATA_JSON.exists():
            return json.loads(DATA_JSON.read_text(encoding="utf-8"))
    except Exception:
        pass

    # default fallback
    return {"PRICE_PER_M3": 50.0, "DEFAULT_YIELD_PER_KGVS": 0.20, "DEFAULT_METHANE_FRACTION": 0.55}

@router.post("/config")
def update_config(payload: ConfigIn, db: Session = Depends(get_db)):
    # update DB config if exists otherwise update JSON file
    cfg = db.query(Config).first()
    if cfg:
        cfg.price_per_m3 = payload.PRICE_PER_M3
        cfg.default_yield_per_kgvs = payload.DEFAULT_YIELD_PER_KGVS
        cfg.default_methane_fraction = payload.DEFAULT_METHANE_FRACTION
        db.commit()
        return {"message": "Config updated (DB)"}

    # ensure data dir exists
    DATA_JSON.parent.mkdir(parents=True, exist_ok=True)
    DATA_JSON.write_text(json.dumps(payload.dict(), indent=2), encoding="utf-8")
    return {"message": "Config updated (config.json)"}
