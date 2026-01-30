# train_regression.py
# Trains a regression model (moisture_percent, vs_fraction) from residue images.
# Project synopsis (reference): /mnt/data/AgroGas -Synopsis.docx

import argparse
from pathlib import Path
import pandas as pd
from PIL import Image
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
import torchvision.transforms as T
import torchvision.models as models
from tqdm import tqdm

# Paths (relative to project root)
DATASET = Path("dataset/train.csv")
IMG_ROOT = Path("dataset/images")
OUT_DIR = Path("backend/outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------
# Dataset
# ------------------------------
class ResidueDataset(Dataset):
    def __init__(self, df, transform):
        self.df = df.reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def _resolve_path(self, raw_path: str) -> Path:
        """
        Ensure we produce a valid Path under IMG_ROOT.
        The CSV may store:
          - "residue/5.jpg"
          - "dataset/images/residue/5.jpg"
          - "dataset/images\\residue\\5.jpg"
        This function normalizes and returns a Path under IMG_ROOT.
        """
        p = str(raw_path).replace("\\", "/").strip()

        # remove leading dataset/ or dataset/images/ if present
        if p.startswith("dataset/images/"):
            p = p.replace("dataset/images/", "")
        elif p.startswith("dataset/"):
            p = p.replace("dataset/", "")

        # remove any leading slashes
        p = p.lstrip("/")

        candidate = IMG_ROOT / p
        return candidate

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        raw_path = row["image_path"]

        img_path = self._resolve_path(raw_path)

        if not img_path.exists():
            # Try an alternate: maybe the CSV path was already relative to project root (rare)
            alt = Path(raw_path)
            if alt.exists():
                img_path = alt
            else:
                # helpful debugging message
                raise FileNotFoundError(f"Missing image file for CSV row {idx}: tried\n  {img_path}\n  {alt}\n"
                                        f"Raw image_path value: '{raw_path}'")

        img = Image.open(img_path).convert("RGB")
        img = self.transform(img)

        # targets
        moisture = float(row["moisture_percent"])
        vs = float(row["vs_fraction"])
        y = torch.tensor([moisture, vs], dtype=torch.float32)
        return img, y

# ------------------------------
# Model
# ------------------------------
class MoistureVSRegressor(nn.Module):
    def __init__(self):
        super().__init__()
        # Use torchvision's pretrained efficientnet_b0 weights for better features.
        base = models.efficientnet_b0(pretrained=True)
        # remove classifier; keep feature extractor
        self.backbone = nn.Sequential(*list(base.children())[:-2])
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.head = nn.Sequential(
            nn.Linear(1280, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Linear(128, 2)      # outputs: moisture_percent, vs_fraction
        )

    def forward(self, x):
        x = self.backbone(x)
        x = self.pool(x).view(x.size(0), -1)
        return self.head(x)

# ------------------------------
# Training Loop
# ------------------------------
def train_model(epochs, batch, lr, device, img_size, num_workers):
    if not DATASET.exists():
        raise FileNotFoundError(f"Training CSV not found: {DATASET}. Run prepare_training_csv.py first.")

    df = pd.read_csv(DATASET)
    if len(df) == 0:
        raise ValueError(f"No training rows found in {DATASET}.")

    # train/val split
    train_df, val_df = train_test_split(df, test_size=0.15, random_state=42)

    transform = T.Compose([
        T.Resize((img_size, img_size)),
        T.RandomHorizontalFlip(),
        T.RandomRotation(15),
        T.ToTensor(),
        T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
    ])

    train_ds = ResidueDataset(train_df, transform)
    val_ds = ResidueDataset(val_df, transform)

    train_dl = DataLoader(train_ds, batch_size=batch, shuffle=True, num_workers=num_workers, pin_memory=(device!="cpu"))
    val_dl = DataLoader(val_ds, batch_size=batch, shuffle=False, num_workers=num_workers, pin_memory=(device!="cpu"))

    model = MoistureVSRegressor().to(device)
    optim = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.L1Loss()     # MAE for regression

    best_loss = float("inf")
    best_path = OUT_DIR / "best_regressor.pth"

    print(f"Training samples: {len(train_ds)} | Validation samples: {len(val_ds)}")
    print(f"Device: {device} | Img size: {img_size} | Batch: {batch} | Num workers: {num_workers}")

    for epoch in range(1, epochs+1):
        model.train()
        running_loss = 0.0
        pbar = tqdm(train_dl, desc=f"Epoch {epoch}/{epochs}", unit="batch")

        for imgs, targets in pbar:
            imgs, targets = imgs.to(device), targets.to(device)
            preds = model(imgs)
            loss = loss_fn(preds, targets)

            optim.zero_grad()
            loss.backward()
            optim.step()

            running_loss += loss.item() * imgs.size(0)
            pbar.set_postfix(train_loss=(running_loss / ((pbar.n + 1) * imgs.size(0))))

        train_loss = running_loss / len(train_dl.dataset)

        # Validation
        model.eval()
        val_running = 0.0
        with torch.no_grad():
            for imgs, targets in val_dl:
                imgs, targets = imgs.to(device), targets.to(device)
                preds = model(imgs)
                val_running += loss_fn(preds, targets).item() * imgs.size(0)
        val_loss = val_running / len(val_dl.dataset)

        print(f"[{epoch}] Train MAE: {train_loss:.4f} | Val MAE: {val_loss:.4f}")

        if val_loss < best_loss:
            best_loss = val_loss
            torch.save({"model_state": model.state_dict()}, best_path)
            print("✔ Saved new best model:", best_path)

    print("\nTraining complete.")
    print(f"Best model saved to: {best_path}")

# ------------------------------
# CLI
# ------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--img-size", type=int, default=320)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--num-workers", type=int, default=0, help="DataLoader num_workers (0 recommended on Windows)")

    args = parser.parse_args()
    device = torch.device(args.device if torch.cuda.is_available() or args.device=="cpu" else "cpu")

    train_model(args.epochs, args.batch, args.lr, device, args.img_size, args.num_workers)
