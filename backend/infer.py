# backend/infer.py
import io
from pathlib import Path
import torch
import torchvision.transforms as T
from PIL import Image
import torch.nn as nn
import torchvision.models as models
import sys
from typing import Dict

ROOT = Path(__file__).resolve().parent
# The training saved file name is best_regressor.pth, so point to it
MODEL_PATH = ROOT / "outputs" / "best_regressor.pth"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ---- Model definition used for training ----
class MoistureVSRegressor(nn.Module):
    def __init__(self):
        super().__init__()
        base = models.efficientnet_b0(pretrained=False)
        # use children up to features (match train_regression)
        self.backbone = nn.Sequential(*list(base.children())[:-2])
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.head = nn.Sequential(
            nn.Linear(1280, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Linear(128, 2)      # outputs: moisture (%) , vs (0..1)
        )

    def forward(self, x):
        x = self.backbone(x)
        x = self.pool(x).view(x.size(0), -1)
        return self.head(x)

# ---- Transforms (should match training) ----
TF = T.Compose([
    T.Resize((320, 320)),
    T.ToTensor(),
    T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
])

# ---- Load model helper ----
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"MODEL WEIGHTS NOT FOUND: {MODEL_PATH}. Train model first.")
    model = MoistureVSRegressor()
    ckpt = torch.load(MODEL_PATH, map_location=DEVICE)
    # ckpt might be state_dict or a dict with model_state
    if isinstance(ckpt, dict) and ("model_state" in ckpt or "state_dict" in ckpt):
        st = ckpt.get("model_state") or ckpt.get("state_dict")
        model.load_state_dict(st)
    else:
        model.load_state_dict(ckpt)
    model.to(DEVICE)
    model.eval()
    print(f"✅ Loaded model weights from: {MODEL_PATH} on device {DEVICE}", file=sys.stderr)
    return model

# Load once at import time (so server fails fast if file missing)
MODEL = None
LOAD_ERR = None
try:
    MODEL = load_model()
except Exception as e:
    LOAD_ERR = e
    MODEL = None
    print("⚠️ Model load error:", e, file=sys.stderr)

# ---- Inference function used by main.py ----
def predict_from_bytes(image_bytes: bytes) -> Dict[str, float]:
    """
    Accepts raw image bytes and returns:
      {"moisture_percent": float, "vs_fraction": float}
    """
    if MODEL is None:
        raise FileNotFoundError(f"Model not loaded: {LOAD_ERR}")

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    x = TF(img).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        out = MODEL(x).cpu().numpy()[0]

    # training outputs: [moisture, vs]
    moisture = float(out[0])
    vs = float(out[1])

    # clamp to realistic ranges
    moisture = max(0.0, min(100.0, moisture))
    vs = max(0.0, min(1.0, vs))

    # Round sensibly
    return {
        "moisture_percent": round(moisture, 2),
        "vs_fraction": round(vs, 3)
    }
