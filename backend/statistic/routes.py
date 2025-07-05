from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
from sqlalchemy import text, distinct

from auth.models import User
from auth.routes import engine, get_current_user
from receipt.models import ReceiptItem, Receipt, Market
from receipt.utils import is_admin_user
from statistic.models import TotalSpentKPI, TotalReceiptsKPI, AverageReceiptValueKPI, TimeSeriesData, \
    TopItemsKPI, WordCloudItem, TopItem, AggregationType, \
    MarketTotalSpent, MarketTotalSpentList, MarketTotalReceipts, MarketTotalReceiptsList, MarketAverageSpent, MarketAverageSpentList

router = APIRouter(prefix="/statistic", tags=["statistic"])


@router.get("/kpi/total-spent", response_model=TotalSpentKPI)
async def get_total_spent_kpi(
        current_user: User = Depends(get_current_user),
        date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
        date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
        user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)")
):
    """Get total spent KPI - calculated in database"""
    with Session(engine) as session:
        # Build query with JOIN to get total spent directly from database
        query = select(func.sum(ReceiptItem.unit_price * ReceiptItem.quantity)).select_from(
            ReceiptItem.__table__.join(Receipt.__table__, ReceiptItem.receipt_id == Receipt.id)
        )

        # Apply user filter
        if is_admin_user(current_user) and user_id is not None:
            query = query.where(Receipt.user_id == user_id)
        else:
            query = query.where(Receipt.user_id == current_user.id)

        # Apply date filters
        if date_from:
            query = query.where(Receipt.date >= date_from)
        if date_to:
            query = query.where(Receipt.date <= date_to)

        # Execute query
        total_spent = session.exec(query).first()

        return TotalSpentKPI(total_spent=total_spent or 0.0)


@router.get("/kpi/total-receipts", response_model=TotalReceiptsKPI)
async def get_total_receipts_kpi(
        current_user: User = Depends(get_current_user),
        date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
        date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
        user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)")
):
    """Get total receipts count KPI - calculated in database"""
    with Session(engine) as session:
        # Build query to count receipts
        query = select(func.count()).select_from(Receipt)

        # Apply user filter
        if is_admin_user(current_user) and user_id is not None:
            query = query.where(Receipt.user_id == user_id)
        else:
            query = query.where(Receipt.user_id == current_user.id)

        # Apply date filters
        if date_from:
            query = query.where(Receipt.date >= date_from)
        if date_to:
            query = query.where(Receipt.date <= date_to)

        # Execute query
        total_receipts = session.exec(query).first()

        return TotalReceiptsKPI(total_receipts=total_receipts or 0)


@router.get("/kpi/average-receipt-value", response_model=AverageReceiptValueKPI)
async def get_average_receipt_value_kpi(
        current_user: User = Depends(get_current_user),
        date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
        date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
        user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)")
):
    """Get average receipt value KPI - calculated in database"""
    with Session(engine) as session:
        # Build query to calculate average receipt value
        # First get total spent
        total_query = select(func.sum(ReceiptItem.unit_price * ReceiptItem.quantity)).select_from(
            ReceiptItem.__table__.join(Receipt.__table__, ReceiptItem.receipt_id == Receipt.id)
        )

        # Apply user filter
        if is_admin_user(current_user) and user_id is not None:
            total_query = total_query.where(Receipt.user_id == user_id)
        else:
            total_query = total_query.where(Receipt.user_id == current_user.id)

        # Apply date filters
        if date_from:
            total_query = total_query.where(Receipt.date >= date_from)
        if date_to:
            total_query = total_query.where(Receipt.date <= date_to)

        # Get total spent
        total_spent = session.exec(total_query).first() or 0.0

        # Get receipt count
        count_query = select(func.count()).select_from(Receipt)
        if is_admin_user(current_user) and user_id is not None:
            count_query = count_query.where(Receipt.user_id == user_id)
        else:
            count_query = count_query.where(Receipt.user_id == current_user.id)

        if date_from:
            count_query = count_query.where(Receipt.date >= date_from)
        if date_to:
            count_query = count_query.where(Receipt.date <= date_to)

        total_receipts = session.exec(count_query).first() or 0

        # Calculate average
        average_value = total_spent / total_receipts if total_receipts > 0 else 0.0

        return AverageReceiptValueKPI(average_receipt_value=average_value)


@router.get("/kpi/top-items", response_model=TopItemsKPI)
async def get_top_items_kpi(
        current_user: User = Depends(get_current_user),
        date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
        date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
        user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)"),
        limit: int = Query(10, ge=1, le=50, description="Top N items to return")
):
    """Get top items KPI - calculated in database"""
    with Session(engine) as session:
        # Build query to get top items with aggregation
        query = select(
            ReceiptItem.name,
            func.sum(ReceiptItem.quantity).label("count"),
            func.sum(ReceiptItem.unit_price * ReceiptItem.quantity).label("total_spent")
        ).select_from(
            ReceiptItem.__table__.join(Receipt.__table__, ReceiptItem.receipt_id == Receipt.id)
        ).group_by(ReceiptItem.name)

        # Apply user filter
        if is_admin_user(current_user) and user_id is not None:
            query = query.where(Receipt.user_id == user_id)
        else:
            query = query.where(Receipt.user_id == current_user.id)

        # Apply date filters
        if date_from:
            query = query.where(Receipt.date >= date_from)
        if date_to:
            query = query.where(Receipt.date <= date_to)

        # Order by count descending and limit
        query = query.order_by(text("count DESC")).limit(limit)

        # Execute query
        results = session.exec(query).all()

        # Convert to TopItem objects
        items = [
            TopItem(
                name=result[0],
                count=result[1],
                total_spent=float(result[2])
            )
            for result in results
        ]

        return TopItemsKPI(items=items)

@router.get("/timeseries/receipts", response_model=List[TimeSeriesData])
async def get_receipts_timeseries(
    current_user: User = Depends(get_current_user),
    date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
    date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
    user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)"),
    aggregation: AggregationType = Query(AggregationType.DAY, description="Aggregálás szintje: day, month, year")
):
    """Get time series data for receipts count by date - calculated in database"""
    with Session(engine) as session:
        # Date grouping logic
        if aggregation == AggregationType.YEAR:
            date_expr = func.date_trunc("year", Receipt.date)
        elif aggregation == AggregationType.MONTH:
            date_expr = func.date_trunc("month", Receipt.date)
        else:  # AggregationType.DAY
            date_expr = func.date_trunc("day", Receipt.date)

        stmt = select(
            date_expr.label("date"),
            func.count().label("value")
        ).select_from(Receipt)

        # Filtering
        conditions = []

        if is_admin_user(current_user) and user_id is not None:
            conditions.append(Receipt.user_id == user_id)
        else:
            conditions.append(Receipt.user_id == current_user.id)

        if date_from:
            conditions.append(Receipt.date >= date_from)
        if date_to:
            conditions.append(Receipt.date <= date_to)

        if conditions:
            stmt = stmt.where(*conditions)

        stmt = stmt.group_by(date_expr).order_by(date_expr)

        results = session.exec(stmt).all()

        return [
            TimeSeriesData(date=row.date, value=float(row.value))
            for row in results
        ]
@router.get("/timeseries/amounts", response_model=List[TimeSeriesData])
async def get_amounts_timeseries(
        current_user: User = Depends(get_current_user),
        date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
        date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
        user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)"),
        aggregation: AggregationType = Query(AggregationType.DAY, description="Aggregálás szintje: day, month, year")
):
    """Get time series data for amounts spent by date - calculated in database"""
    with Session(engine) as session:
        # Date grouping logic - ugyanaz mint a receipts endpointnál
        if aggregation == AggregationType.YEAR:
            date_expr = func.date_trunc("year", Receipt.date)
        elif aggregation == AggregationType.MONTH:
            date_expr = func.date_trunc("month", Receipt.date)
        else:  # AggregationType.DAY
            date_expr = func.date_trunc("day", Receipt.date)

        # Build query with SQL aggregation
        stmt = select(
            date_expr.label("date"),
            func.sum(ReceiptItem.unit_price * ReceiptItem.quantity).label("total_amount")
        ).select_from(Receipt).join(ReceiptItem)

        # Filtering
        conditions = []

        if is_admin_user(current_user) and user_id is not None:
            conditions.append(Receipt.user_id == user_id)
        else:
            conditions.append(Receipt.user_id == current_user.id)

        if date_from:
            conditions.append(Receipt.date >= date_from)
        if date_to:
            conditions.append(Receipt.date <= date_to)

        if conditions:
            stmt = stmt.where(*conditions)

        stmt = stmt.group_by(date_expr).order_by(date_expr)

        results = session.exec(stmt).all()

        return [
            TimeSeriesData(date=row.date, value=float(row.total_amount))
            for row in results
        ]

@router.get("/wordcloud", response_model=List[WordCloudItem])
async def get_wordcloud_data(
        current_user: User = Depends(get_current_user),
        date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
        date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
        user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)"),
        limit: int = Query(30, ge=1, le=100, description="Number of items to return")
):
    """Get word cloud data for most frequently purchased items - calculated in database"""
    with Session(engine) as session:
        # Build query to get item statistics
        query = select(
            ReceiptItem.name,
            func.count().label("count"),
            func.sum(ReceiptItem.unit_price * ReceiptItem.quantity).label("total_spent")
        ).select_from(
            ReceiptItem.__table__.join(Receipt.__table__, ReceiptItem.receipt_id == Receipt.id)
        ).group_by(ReceiptItem.name)

        # Apply user filter
        if is_admin_user(current_user) and user_id is not None:
            query = query.where(Receipt.user_id == user_id)
        else:
            query = query.where(Receipt.user_id == current_user.id)

        # Apply date filters
        if date_from:
            query = query.where(Receipt.date >= date_from)
        if date_to:
            query = query.where(Receipt.date <= date_to)

        # Order by count descending and limit
        query = query.order_by(text("count DESC")).limit(limit)

        # Execute query
        results = session.exec(query).all()

        # Convert to WordCloudItem objects
        wordcloud_data = [
            WordCloudItem(
                text=result[0],
                value=result[1],
                total_spent=float(result[2])
            )
            for result in results
        ]

        return wordcloud_data
    
@router.get("/market/total-spent", response_model=MarketTotalSpentList)
async def get_market_total_spent(
    current_user: User = Depends(get_current_user),
    date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
    date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
    user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)")
):
    """Összköltés marketenként - minden aggregáció az adatbázisban történik"""
    with Session(engine) as session:
        query = select(
            Market.name,
            func.sum(ReceiptItem.unit_price * ReceiptItem.quantity).label("total_spent")
        ).select_from(
            ReceiptItem.__table__
            .join(Receipt.__table__, ReceiptItem.receipt_id == Receipt.id)
            .join(Market.__table__, Receipt.market_id == Market.id)
        )

        # User filter
        if is_admin_user(current_user) and user_id is not None:
            query = query.where(Receipt.user_id == user_id)
        else:
            query = query.where(Receipt.user_id == current_user.id)

        # Date filters
        if date_from:
            query = query.where(Receipt.date >= date_from)
        if date_to:
            query = query.where(Receipt.date <= date_to)

        query = query.group_by(Market.name)

        results = session.exec(query).all()

        markets = [
            MarketTotalSpent(market_name=row[0], total_spent=float(row[1] or 0.0))
            for row in results
        ]

        return MarketTotalSpentList(markets=markets)

@router.get("/market/total-receipts", response_model=MarketTotalReceiptsList)
async def get_market_total_receipts(
    current_user: User = Depends(get_current_user),
    date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
    date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
    user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)")
):
    """Vásárlások száma marketenként - aggregáció az adatbázisban"""
    with Session(engine) as session:
        query = select(
            Market.name,
            func.sum(ReceiptItem.quantity).label("total_receipts")
        ).select_from(
            Receipt.__table__.join(Market.__table__, Receipt.market_id == Market.id)
        )

        # User filter
        if is_admin_user(current_user) and user_id is not None:
            query = query.where(Receipt.user_id == user_id)
        else:
            query = query.where(Receipt.user_id == current_user.id)

        # Date filters
        if date_from:
            query = query.where(Receipt.date >= date_from)
        if date_to:
            query = query.where(Receipt.date <= date_to)

        query = query.group_by(Market.name)

        results = session.exec(query).all()

        markets = [
            MarketTotalReceipts(market_name=row[0], total_receipts=int(row[1] or 0))
            for row in results
        ]

        return MarketTotalReceiptsList(markets=markets)

@router.get("/market/average-spent", response_model=MarketAverageSpentList)
async def get_market_average_spent(
    current_user: User = Depends(get_current_user),
    date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
    date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
    user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)")
):
    """Átlagos költés marketenként - aggregáció az adatbázisban"""
    with Session(engine) as session:
        avg_expr = func.sum(ReceiptItem.unit_price * ReceiptItem.quantity) / func.count(distinct(Receipt.id))

        query = select(
            Market.name,
            avg_expr.label("average_spent")
        ).select_from(
            ReceiptItem.__table__
            .join(Receipt.__table__, ReceiptItem.receipt_id == Receipt.id)
            .join(Market.__table__, Receipt.market_id == Market.id)
        )

        # User filter
        if is_admin_user(current_user) and user_id is not None:
            query = query.where(Receipt.user_id == user_id)
        else:
            query = query.where(Receipt.user_id == current_user.id)

        # Date filters
        if date_from:
            query = query.where(Receipt.date >= date_from)
        if date_to:
            query = query.where(Receipt.date <= date_to)

        query = query.group_by(Market.name)

        results = session.exec(query).all()

        markets = [
            MarketAverageSpent(market_name=row[0], average_spent=float(row[1] or 0.0))
            for row in results
        ]

        return MarketAverageSpentList(markets=markets)
