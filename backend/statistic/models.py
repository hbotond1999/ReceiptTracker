from typing import List, Union
from enum import Enum

from pydantic import BaseModel

from datetime import date

class AggregationType(str, Enum):
    DAY = "day"
    MONTH = "month"
    YEAR = "year"

class TimeSeriesData(BaseModel):
    date: date
    value: float

class WordCloudItem(BaseModel):
    text: str
    value: int
    total_spent: float

class TopItem(BaseModel):
    name: str
    count: float
    total_spent: float


class TotalSpentKPI(BaseModel):
    total_spent: float

class TotalReceiptsKPI(BaseModel):
    total_receipts: int

class AverageReceiptValueKPI(BaseModel):
    average_receipt_value: float

class TopItemsKPI(BaseModel):
    items: List[TopItem]

class MarketTotalSpent(BaseModel):
    market_name: str
    total_spent: float

class MarketTotalSpentList(BaseModel):
    markets: List[MarketTotalSpent]

class MarketTotalReceipts(BaseModel):
    market_name: str
    total_receipts: int

class MarketTotalReceiptsList(BaseModel):
    markets: List[MarketTotalReceipts]

class MarketAverageSpent(BaseModel):
    market_name: str
    average_spent: float

class MarketAverageSpentList(BaseModel):
    markets: List[MarketAverageSpent]