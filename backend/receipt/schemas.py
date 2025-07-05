from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel
from auth.schemas import UserOut


class MarketOut(BaseModel):
    id: int
    name: str
    tax_number: str


class MarketUpdateRequest(BaseModel):
    id: int
    name: str
    tax_number: str


class ReceiptItemOut(BaseModel):
    id: int
    name: str
    price: float
    unit_price: float
    quantity: float
    unit: str


class ReceiptItemUpdateRequest(BaseModel):
    id: Optional[int] = None  # None means new item
    name: str
    unit_price: float
    quantity: float
    unit: str


class ReceiptOut(BaseModel):
    id: int
    date: datetime
    receipt_number: str
    image_path: str
    original_filename: str
    user: UserOut
    market: MarketOut
    postal_code: str
    city: str
    street_name: str
    street_number: str
    items: List[ReceiptItemOut]
    total: float


class ReceiptItemCreateRequest(BaseModel):
    name: str
    unit_price: float
    quantity: float
    unit: str


class ReceiptCreateRequest(BaseModel):
    date: datetime
    receipt_number: str
    market_id: int
    image_path: str
    original_filename: str
    postal_code: str
    city: str
    street_name: str
    street_number: str
    user_id: Optional[int] = None  # csak admin használhatja
    items: Optional[List[ReceiptItemCreateRequest]] = None  # opcionális tételek


class ReceiptUpdateRequest(BaseModel):
    date: Optional[datetime] = None
    receipt_number: Optional[str] = None
    market_id: Optional[int] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    street_name: Optional[str] = None
    street_number: Optional[str] = None
    items: Optional[List[ReceiptItemUpdateRequest]] = None


class ReceiptListOut(BaseModel):
    receipts: List[ReceiptOut]
    skip: int
    limit: int
    total: int
    has_next: bool
    has_previous: bool

