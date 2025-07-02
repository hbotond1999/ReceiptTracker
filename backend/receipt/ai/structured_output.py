from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class Market(BaseModel):
    name: str = Field(..., description="A bolt neve, ahol a vásárlás történt.")
    tax_number: str = Field(..., description="A bolt adószáma.")

class Address(BaseModel):
    postal_code: str = Field(..., description="A bolt irányítószáma.")
    city: str = Field(..., description="A bolt városa.")
    street_name: str = Field(..., description="A bolt utcaneve.")
    street_number: str = Field(..., description="A bolt házszáma.")

class ReceiptItem(BaseModel):
    name: str = Field(..., description="A termék neve a blokkon.")
    price: float = Field(..., description="A termék ára forintban.")

class Receipt(BaseModel):
    date: datetime = Field(..., description="A vásárlás dátuma és ideje a blokkon.")
    receipt_number: str = Field(..., description="A blokk sorszáma vagy azonosítója.")
    market: Market = Field(..., description="A bolt adatai, ahol a vásárlás történt.")
    address: Address = Field(..., description="A bolt címe.")
    items: List[ReceiptItem] = Field(..., description="A blokkon szereplő termékek listája.")



