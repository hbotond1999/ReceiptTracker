from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from backend.auth.models import RoleEnum


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    fullname: Optional[str] = None
    profile_picture: Optional[str] = None
    disabled: bool = False
    roles: List[str] = []  # Role names as strings


class MarketResponse(BaseModel):
    id: int
    name: str
    tax_number: str


class AddressResponse(BaseModel):
    id: int
    postal_code: str
    city: str
    street_name: str
    street_number: str


class ReceiptItemResponse(BaseModel):
    id: int
    name: str
    price: float


class ReceiptResponse(BaseModel):
    id: int
    date: datetime
    receipt_number: str
    image_path: str
    original_filename: str
    user: UserResponse
    market: MarketResponse
    address: AddressResponse
    items: List[ReceiptItemResponse]


class ReceiptCreateRequest(BaseModel):
    date: datetime
    receipt_number: str
    market_id: int
    address_id: int
    image_path: str
    original_filename: str


class ReceiptItemCreateRequest(BaseModel):
    name: str
    price: float
