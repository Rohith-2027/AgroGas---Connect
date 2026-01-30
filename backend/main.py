import json
import os
import sys
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

# backend root (this file lives in backend/)
ROOT = Path(__file__).resolve().parent

# --------------------------
# Import Database Init
# --------------------------
try:
    from database import init_db
except Exception:
    # fallback: ensure backend is on sys.path then retry
    sys.path.append(str(ROOT))
    from database import init_db

# --------------------------
# Import Routers
# --------------------------
# Expect routes to exist at backend/routes/{auth.py, farmer.py, admin.py, orders.py}
try:
    from routes import farmer, admin, auth, orders
except Exception:
    sys.path.append(str(ROOT))
    from routes import farmer, admin, auth, orders

# --------------------------
# Import ML inference
# --------------------------
try:
    from infer import predict_from_bytes
except Exception:
    sys.path.append(str(ROOT))
    from infer import predict_from_bytes

# --------------------------
# Configuration (data/config.json)
# --------------------------
DATA_DIR = ROOT / "data"
CONFIG_PATH = DATA_DIR / "config.json"

FALLBACK_CONFIG: Dict[str, float] = {
    "PRICE_PER_M3": 50.0,
    "DEFAULT_YIELD_PER_KGVS": 0.20,
    "DEFAULT_METHANE_FRACTION": 0.55,
}


def load_config() -> Dict[str, float]:
    """
    Load JSON config from data/config.json. If missing, create default file.
    Returns a dict with keys PRICE_PER_M3, DEFAULT_YIELD_PER_KGVS, DEFAULT_METHANE_FRACTION.
    """
    try:
        if not CONFIG_PATH.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(json.dumps(FALLBACK_CONFIG, indent=4), encoding="utf-8")
            return FALLBACK_CONFIG.copy()

        raw = CONFIG_PATH.read_text(encoding="utf-8")
        cfg = json.loads(raw)
        # ensure keys exist and have sensible defaults
        for k, v in FALLBACK_CONFIG.items():
            if k not in cfg:
                cfg[k] = v
        return cfg
    except Exception:
        return FALLBACK_CONFIG.copy()


# --------------------------
# FastAPI App
# --------------------------
app = FastAPI(title="AgroGas Inference + Ordering API")

# Allow frontend (served on :5500 during development) to contact backend (:8000).
# In production restrict origins appropriately.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB/tables and ensure default config row exists
try:
    init_db()
except Exception as e:
    # don't crash the process — print error and continue (errors will surface in logs)
    print("⚠️ init_db() error:", e, file=sys.stderr)


# ====================================================
# PREDICTION ENDPOINT
# ====================================================
@app.post("/api/v1/predict")
async def predict(
    image: UploadFile = File(...),
    fresh_dried: str = Form("fresh"),
    measured_weight: float = Form(None),
    scale_feat: float = Form(0.0),
):
    """
    Multipart/form-data:
      - image: file (required)
      - fresh_dried: optional (string)
      - measured_weight: optional float (if provided it is used as mass_kg)
      - scale_feat: optional numeric (for future use)

    Returns predicted moisture & VS (from the model) and derived biogas & revenue
    computed using the measured_weight supplied by farmer (measured takes precedence).
    """
    # 1) read image bytes
    try:
        contents = await image.read()
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Failed to read uploaded image: {e}"})

    # 2) run inference (predict_from_bytes should return {"moisture_percent":..., "vs_fraction":...})
    try:
        preds = predict_from_bytes(contents)
    except FileNotFoundError as fe:
        # model weights missing / model not loaded
        return JSONResponse(status_code=500, content={"error": f"Inference error: {fe}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Inference error: {e}"})

    # 3) mass: prefer measured_weight entered by farmer (if provided)
    mass_kg = float(measured_weight) if measured_weight is not None else 0.0

    # 4) values returned from model
    moisture = preds.get("moisture_percent", 0.0)
    vs = preds.get("vs_fraction", 0.0)

    # 5) load current admin-config (so admin edits take effect immediately)
    cfg = load_config()
    PRICE_PER_M3 = float(cfg.get("PRICE_PER_M3", FALLBACK_CONFIG["PRICE_PER_M3"]))
    YIELD_PER_KGVS = float(cfg.get("DEFAULT_YIELD_PER_KGVS", FALLBACK_CONFIG["DEFAULT_YIELD_PER_KGVS"]))
    METHANE_FRACTION = float(cfg.get("DEFAULT_METHANE_FRACTION", FALLBACK_CONFIG["DEFAULT_METHANE_FRACTION"]))

    # 6) derived computations (use measured weight + ML-predicted VS)
    biogas_m3 = round(mass_kg * vs * YIELD_PER_KGVS, 3) if (mass_kg and vs) else 0.0
    methane_m3 = round(biogas_m3 * METHANE_FRACTION, 3)
    revenue = round(biogas_m3 * PRICE_PER_M3, 2)

    # 7) form response
    response = {
        "crop": "banana",
        "mass_kg": round(mass_kg, 3),
        "mass_source": "measured" if measured_weight is not None else "none",
        "moisture_percent": moisture,
        "vs_fraction": vs,
        "predicted_m3_biogas": biogas_m3,
        "predicted_m3_ch4": methane_m3,
        "price_per_m3": PRICE_PER_M3,
        "revenue_estimate": revenue,
        "recommendation": ("Chop <20mm" if vs and vs > 0.6 else "Dry slightly before feed"),
    }

    return response


# --------------------------
# Include route modules (auth, farmer, admin, orders)
# --------------------------
# Each router should define paths under /api/v1/...
try:
    app.include_router(auth.router)
except Exception as e:
    print("⚠️ Failed to include auth router:", e, file=sys.stderr)

try:
    app.include_router(farmer.router)
except Exception as e:
    print("⚠️ Failed to include farmer router:", e, file=sys.stderr)

try:
    app.include_router(admin.router)
except Exception as e:
    print("⚠️ Failed to include admin router:", e, file=sys.stderr)

try:
    app.include_router(orders.router)
except Exception as e:
    print("⚠️ Failed to include orders router:", e, file=sys.stderr)


# --------------------------
# Root / health check
# --------------------------
@app.get("/")
def root():
    return {"message": "AgroGas API is running 🚀"}
