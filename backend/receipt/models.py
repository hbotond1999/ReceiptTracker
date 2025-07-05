from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class Receipt(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime = Field()
    receipt_number: str = Field()
    market_id: int = Field(foreign_key="market.id")
    user_id: int = Field(foreign_key="user.id")
    image_path: str = Field(description="A blokk képének fájlrendszerbeli elérési útja")
    original_filename: str = Field(description="A feltöltött fájl eredeti neve")
    postal_code: str = Field()
    city: str = Field()
    street_name: str = Field()
    street_number: str = Field()
    market: "Market" = Relationship(back_populates="receipts")
    items: List["ReceiptItem"] = Relationship(back_populates="receipt")

class Market(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field()
    tax_number: str = Field(unique=True)
    receipts: List["Receipt"] = Relationship(back_populates="market")


class ReceiptItem(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field()
    unit_price: float = Field()
    quantity: float = Field()
    unit: str = Field()
    receipt_id: int = Field(foreign_key="receipt.id")
    receipt: Receipt = Relationship(back_populates="items")