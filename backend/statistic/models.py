from typing import List

from pydantic import BaseModel

from datetime import date

class TimeSeriesData(BaseModel):
    date: date
    value: float

class WordCloudItem(BaseModel):
    text: str
    value: int
    total_spent: float

class TopItem(BaseModel):
    name: str
    count: int
    total_spent: float


class TotalSpentKPI(BaseModel):
    total_spent: float

class TotalReceiptsKPI(BaseModel):
    total_receipts: int

class AverageReceiptValueKPI(BaseModel):
    average_receipt_value: float

class TopItemsKPI(BaseModel):
    items: List[TopItem]