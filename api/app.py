import csv
import os
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

CSV_PATH = Path(os.getenv("INVENTORY_CSV", Path(__file__).resolve().parent.parent / "products.csv"))
DEFAULT_THRESHOLD = int(os.getenv("INVENTORY_ALERT_THRESHOLD", "10"))
FIELDS = ["id", "name", "quantity", "unit"]

app = FastAPI(title="Inventory API")
_lock = threading.Lock()


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=0)
    unit: str = Field(min_length=1, max_length=20)

    @field_validator("name", "unit")
    @classmethod
    def strip_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("no puede estar vacío")
        return v


class Product(ProductIn):
    id: int


class StockUpdate(BaseModel):
    delta: int

    @field_validator("delta")
    @classmethod
    def non_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("delta debe ser distinto de 0")
        return v


def read_products() -> list[dict]:
    if not CSV_PATH.exists():
        return []
    try:
        with CSV_PATH.open(newline="", encoding="utf-8") as f:
            return [
                {"id": int(r["id"]), "name": r["name"], "quantity": int(r["quantity"]), "unit": r["unit"]}
                for r in csv.DictReader(f)
            ]
    except (KeyError, ValueError) as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Fichero de inventario corrupto: {e}")


def write_products(products: list[dict]) -> None:
    # Write to a temp file and replace to avoid leaving a half-written CSV
    tmp = CSV_PATH.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(products)
    os.replace(tmp, CSV_PATH)


@app.get("/inventory", response_model=list[Product])
def list_products():
    with _lock:
        return read_products()


@app.post("/inventory", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductIn):
    with _lock:
        products = read_products()
        if any(p["name"].lower() == data.name.lower() for p in products):
            raise HTTPException(status.HTTP_409_CONFLICT, f"Ya existe un producto llamado '{data.name}'")
        product = {"id": max((p["id"] for p in products), default=0) + 1, **data.model_dump()}
        products.append(product)
        write_products(products)
        return product


@app.get("/inventory/alerts", response_model=list[Product])
def low_stock_alerts(threshold: int = Query(DEFAULT_THRESHOLD, ge=0, description="Umbral de stock bajo")):
    with _lock:
        return [p for p in read_products() if p["quantity"] < threshold]


@app.patch("/inventory/{product_id}", response_model=Product)
def update_stock(product_id: int, update: StockUpdate):
    with _lock:
        products = read_products()
        product = next((p for p in products if p["id"] == product_id), None)
        if product is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"No existe ningún producto con id {product_id}")
        new_qty = product["quantity"] + update.delta
        if new_qty < 0:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Stock insuficiente para '{product['name']}': disponible {product['quantity']} "
                f"{product['unit']}, solicitado {-update.delta}",
            )
        product["quantity"] = new_qty
        write_products(products)
        return product