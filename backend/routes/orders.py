from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

# import DB models + session dependency
from database import get_db, Record, Order, OrderItem

router = APIRouter(prefix="/api/v1", tags=["Orders"])


# Expected payload:
# {
#   "buyer_name": "Buyer A",
#   "buyer_phone": "9876",
#   "buyer_location": "Town",
#   "items": [
#     {"record_id": 12, "qty_kg": 1.5},
#     {"record_id": 15, "qty_kg": 2.0}
#   ]
# }
@router.post("/orders")
def place_order(payload: Dict[str, Any], db: Session = Depends(get_db)):
    # Basic validation
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object")

    if "buyer_name" not in payload or not payload["buyer_name"]:
        raise HTTPException(status_code=400, detail="Missing field: buyer_name")
    if "items" not in payload or not isinstance(payload["items"], list) or len(payload["items"]) == 0:
        raise HTTPException(status_code=400, detail="Missing or invalid field: items (non-empty list expected)")

    buyer_name = payload.get("buyer_name")
    buyer_phone = payload.get("buyer_phone")
    buyer_location = payload.get("buyer_location")
    items = payload["items"]

    total_price = 0.0
    order_items_to_insert = []

    try:
        # Validate each requested item and compute totals
        for it in items:
            if not isinstance(it, dict):
                raise HTTPException(status_code=400, detail="Each item must be an object with record_id and qty_kg")

            try:
                record_id = int(it.get("record_id"))
                qty = float(it.get("qty_kg", 0.0))
            except Exception:
                raise HTTPException(status_code=400, detail="record_id must be integer and qty_kg must be numeric")

            if qty <= 0:
                raise HTTPException(status_code=400, detail=f"qty_kg must be > 0 for record {record_id}")

            # Lock the row for update to avoid race (DB must support SELECT ... FOR UPDATE)
            rec = db.query(Record).filter(Record.id == record_id).with_for_update().first()
            if not rec:
                raise HTTPException(status_code=404, detail=f"Record {record_id} not found")

            # Determine available quantity: prefer available_kg column if present, otherwise mass_kg
            avail = rec.available_kg if getattr(rec, "available_kg", None) is not None else (rec.mass_kg or 0.0)
            if qty > avail:
                raise HTTPException(status_code=400,
                                    detail=f"Not enough available quantity for record {record_id} (avail={avail}, requested={qty})")

            # Compute unit price (safe): revenue_estimate / mass_kg if available
            if not rec.mass_kg or rec.mass_kg == 0 or not rec.revenue_estimate:
                unit_price = 0.0
            else:
                unit_price = float(rec.revenue_estimate) / float(rec.mass_kg)

            line_total = round(unit_price * qty, 2)
            total_price += line_total

            order_items_to_insert.append({
                "record_obj": rec,
                "record_id": record_id,
                "qty": qty,
                "unit_price": unit_price,
                "line_total": line_total
            })

        # All checks passed — create Order
        new_order = Order(
            buyer_name=buyer_name,
            buyer_phone=buyer_phone,
            buyer_location=buyer_location,
            total_price=round(total_price, 2),
            status="placed",
            created_at=datetime.utcnow()
        )
        db.add(new_order)
        db.flush()  # ensure new_order.id is available

        # Insert OrderItem rows and decrement available_kg on the related Record
        for oi in order_items_to_insert:
            item = OrderItem(
                order_id=new_order.id,
                record_id=oi["record_id"],
                qty_kg=oi["qty"],
                unit_price=oi["unit_price"],
                line_total=oi["line_total"]
            )
            db.add(item)

            # decrement available quantity on the record
            rec = oi["record_obj"]
            current_avail = rec.available_kg if getattr(rec, "available_kg", None) is not None else (rec.mass_kg or 0.0)
            new_avail = max(0.0, current_avail - oi["qty"])
            # ensure attribute exists; set available_kg on the model
            rec.available_kg = new_avail
            db.add(rec)

        db.commit()
        db.refresh(new_order)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal error placing order: {e}")

    return {"message": "Order placed", "order_id": new_order.id, "total_price": new_order.total_price}


@router.get("/orders")
def list_orders(db: Session = Depends(get_db)):
    """
    Returns list of orders with their items.
    Response: { "orders": [ { id, buyer_name, buyer_phone, buyer_location, total_price, status, created_at, items: [...] }, ... ] }
    """
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    out: List[Dict[str, Any]] = []
    for o in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
        out.append({
            "id": o.id,
            "buyer_name": o.buyer_name,
            "buyer_phone": o.buyer_phone,
            "buyer_location": o.buyer_location,
            "total_price": o.total_price,
            "status": o.status,
            "created_at": o.created_at,
            "items": [
                {
                    "record_id": it.record_id,
                    "qty_kg": it.qty_kg,
                    "unit_price": it.unit_price,
                    "line_total": it.line_total
                } for it in items
            ]
        })
    return {"orders": out}
