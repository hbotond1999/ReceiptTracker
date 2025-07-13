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
from app_logging import get_logger

router = APIRouter(prefix="/statistic", tags=["statistic"])

# Initialize logger
logger = get_logger(__name__)


@router.get("/kpi/total-spent", response_model=TotalSpentKPI)
async def get_total_spent_kpi(
        current_user: User = Depends(get_current_user),
        date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
        date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
        user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)")
):
    """Get total spent KPI - calculated in database"""
    logger.info(f"Total spent KPI request from user: {current_user.username}")
    logger.debug(f"Query parameters: date_from={date_from}, date_to={date_to}, user_id={user_id}")
    
    with Session(engine) as session:
        # Build query with JOIN to get total spent directly from database
        logger.debug("Building total spent query")
        query = select(func.sum(ReceiptItem.unit_price * ReceiptItem.quantity)).select_from(
            ReceiptItem.__table__.join(Receipt.__table__, ReceiptItem.receipt_id == Receipt.id)
        )

        # Apply user filter
        is_admin = is_admin_user(current_user)
        logger.debug(f"User admin status: {is_admin}")
        
        if is_admin and user_id is not None:
            logger.debug(f"Admin filtering by user_id: {user_id}")
            query = query.where(Receipt.user_id == user_id)
        elif is_admin and not user_id:
            logger.debug("Admin requesting all users data")
            pass
        else:
            logger.debug(f"Regular user requesting own data: {current_user.id}")
            query = query.where(Receipt.user_id == current_user.id)

        # Apply date filters
        if date_from:
            logger.debug(f"Applying date_from filter: {date_from}")
            query = query.where(Receipt.date >= date_from)
        if date_to:
            logger.debug(f"Applying date_to filter: {date_to}")
            query = query.where(Receipt.date <= date_to)

        # Execute query
        logger.debug("Executing total spent query")
        total_spent = session.exec(query).first()
        logger.debug(f"Total spent calculated: {total_spent}")

        result = TotalSpentKPI(total_spent=total_spent or 0.0)
        logger.info(f"Total spent KPI request completed: {result.total_spent}")
        return result


@router.get("/kpi/total-receipts", response_model=TotalReceiptsKPI)
async def get_total_receipts_kpi(
        current_user: User = Depends(get_current_user),
        date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
        date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
        user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)")
):
    """Get total receipts count KPI - calculated in database"""
    logger.info(f"Total receipts KPI request from user: {current_user.username}")
    logger.debug(f"Query parameters: date_from={date_from}, date_to={date_to}, user_id={user_id}")
    
    with Session(engine) as session:
        # Build query to count receipts
        logger.debug("Building total receipts count query")
        query = select(func.count()).select_from(Receipt)

        # Apply user filter
        is_admin = is_admin_user(current_user)
        logger.debug(f"User admin status: {is_admin}")
        
        if is_admin and user_id is not None:
            logger.debug(f"Admin filtering by user_id: {user_id}")
            query = query.where(Receipt.user_id == user_id)
        elif is_admin and not user_id:
            logger.debug("Admin requesting all users data")
            pass
        else:
            logger.debug(f"Regular user requesting own data: {current_user.id}")
            query = query.where(Receipt.user_id == current_user.id)

        # Apply date filters
        if date_from:
            logger.debug(f"Applying date_from filter: {date_from}")
            query = query.where(Receipt.date >= date_from)
        if date_to:
            logger.debug(f"Applying date_to filter: {date_to}")
            query = query.where(Receipt.date <= date_to)

        # Execute query
        logger.debug("Executing total receipts count query")
        total_receipts = session.exec(query).first()
        logger.debug(f"Total receipts calculated: {total_receipts}")

        result = TotalReceiptsKPI(total_receipts=total_receipts or 0)
        logger.info(f"Total receipts KPI request completed: {result.total_receipts}")
        return result


@router.get("/kpi/average-receipt-value", response_model=AverageReceiptValueKPI)
async def get_average_receipt_value_kpi(
        current_user: User = Depends(get_current_user),
        date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
        date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
        user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)")
):
    """Get average receipt value KPI - calculated in database"""
    logger.info(f"Average receipt value KPI request from user: {current_user.username}")
    logger.debug(f"Query parameters: date_from={date_from}, date_to={date_to}, user_id={user_id}")
    
    with Session(engine) as session:
        # Build query to calculate average receipt value
        # First get total spent
        logger.debug("Building total spent query for average calculation")
        total_query = select(func.sum(ReceiptItem.unit_price * ReceiptItem.quantity)).select_from(
            ReceiptItem.__table__.join(Receipt.__table__, ReceiptItem.receipt_id == Receipt.id)
        )

        # Apply user filter
        is_admin = is_admin_user(current_user)
        logger.debug(f"User admin status: {is_admin}")
        
        if is_admin and user_id is not None:
            logger.debug(f"Admin filtering by user_id: {user_id}")
            total_query = total_query.where(Receipt.user_id == user_id)
        elif is_admin and not user_id:
            logger.debug("Admin requesting all users data")
            pass
        else:
            logger.debug(f"Regular user requesting own data: {current_user.id}")
            total_query = total_query.where(Receipt.user_id == current_user.id)

        # Apply date filters
        if date_from:
            logger.debug(f"Applying date_from filter: {date_from}")
            total_query = total_query.where(Receipt.date >= date_from)
        if date_to:
            logger.debug(f"Applying date_to filter: {date_to}")
            total_query = total_query.where(Receipt.date <= date_to)

        # Get total spent
        logger.debug("Executing total spent query")
        total_spent = session.exec(total_query).first() or 0.0
        logger.debug(f"Total spent: {total_spent}")

        # Get receipt count
        logger.debug("Building receipts count query for average calculation")
        count_query = select(func.count()).select_from(Receipt)
        is_admin = is_admin_user(current_user)
        if is_admin and user_id is not None:
            count_query = count_query.where(Receipt.user_id == user_id)
        elif is_admin and not user_id:
            pass
        else:
            count_query = count_query.where(Receipt.user_id == current_user.id)

        if date_from:
            count_query = count_query.where(Receipt.date >= date_from)
        if date_to:
            count_query = count_query.where(Receipt.date <= date_to)

        logger.debug("Executing receipts count query")
        total_receipts = session.exec(count_query).first() or 0
        logger.debug(f"Total receipts: {total_receipts}")

        # Calculate average
        average_value = total_spent / total_receipts if total_receipts > 0 else 0.0
        logger.debug(f"Average receipt value calculated: {average_value}")

        result = AverageReceiptValueKPI(average_receipt_value=average_value)
        logger.info(f"Average receipt value KPI request completed: {result.average_receipt_value}")
        return result


@router.get("/kpi/top-items", response_model=TopItemsKPI)
async def get_top_items_kpi(
        current_user: User = Depends(get_current_user),
        date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
        date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
        user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)"),
        limit: int = Query(10, ge=1, le=50, description="Top N items to return")
):
    """Get top items KPI - calculated in database"""
    logger.info(f"Top items KPI request from user: {current_user.username}")
    logger.debug(f"Query parameters: date_from={date_from}, date_to={date_to}, user_id={user_id}, limit={limit}")
    
    with Session(engine) as session:
        # Build query to get top items with aggregation
        logger.debug("Building top items query")
        query = select(
            ReceiptItem.name,
            func.sum(ReceiptItem.quantity).label("count"),
            func.sum(ReceiptItem.unit_price * ReceiptItem.quantity).label("total_spent")
        ).select_from(
            ReceiptItem.__table__.join(Receipt.__table__, ReceiptItem.receipt_id == Receipt.id)
        ).group_by(ReceiptItem.name)

        # Apply user filter
        is_admin = is_admin_user(current_user)
        logger.debug(f"User admin status: {is_admin}")
        
        if is_admin and user_id is not None:
            logger.debug(f"Admin filtering by user_id: {user_id}")
            query = query.where(Receipt.user_id == user_id)
        elif is_admin and not user_id:
            logger.debug("Admin requesting all users data")
            pass
        else:
            logger.debug(f"Regular user requesting own data: {current_user.id}")
            query = query.where(Receipt.user_id == current_user.id)

        # Apply date filters
        if date_from:
            logger.debug(f"Applying date_from filter: {date_from}")
            query = query.where(Receipt.date >= date_from)
        if date_to:
            logger.debug(f"Applying date_to filter: {date_to}")
            query = query.where(Receipt.date <= date_to)

        # Order by count descending and limit
        logger.debug(f"Applying order and limit: {limit}")
        query = query.order_by(text("count DESC")).limit(limit)

        # Execute query
        logger.debug("Executing top items query")
        results = session.exec(query).all()
        logger.debug(f"Retrieved {len(results)} top items")

        # Convert to TopItem objects
        items = [
            TopItem(
                name=result[0],
                count=result[1],
                total_spent=float(result[2])
            )
            for result in results
        ]

        result = TopItemsKPI(items=items)
        logger.info(f"Top items KPI request completed: {len(result.items)} items")
        return result

@router.get("/timeseries/receipts", response_model=List[TimeSeriesData])
async def get_receipts_timeseries(
    current_user: User = Depends(get_current_user),
    date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
    date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
    user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)"),
    aggregation: AggregationType = Query(AggregationType.DAY, description="Aggregálás szintje: day, month, year")
):
    """Get time series data for receipts count by date - calculated in database"""
    logger.info(f"Receipts timeseries request from user: {current_user.username}")
    logger.debug(f"Query parameters: date_from={date_from}, date_to={date_to}, user_id={user_id}, aggregation={aggregation}")
    
    with Session(engine) as session:
        # Date grouping logic
        logger.debug(f"Setting up date grouping for aggregation: {aggregation}")
        if aggregation == AggregationType.YEAR:
            date_expr = func.date_trunc("year", Receipt.date)
        elif aggregation == AggregationType.MONTH:
            date_expr = func.date_trunc("month", Receipt.date)
        else:  # AggregationType.DAY
            date_expr = func.date_trunc("day", Receipt.date)

        logger.debug("Building receipts timeseries query")
        stmt = select(
            date_expr.label("date"),
            func.count().label("value")
        ).select_from(Receipt)

        # Filtering
        conditions = []
        is_admin = is_admin_user(current_user)
        logger.debug(f"User admin status: {is_admin}")
        
        if is_admin and user_id is not None:
            logger.debug(f"Admin filtering by user_id: {user_id}")
            conditions.append(Receipt.user_id == user_id)
        elif is_admin and not user_id:
            logger.debug("Admin requesting all users data")
            pass
        else:
            logger.debug(f"Regular user requesting own data: {current_user.id}")
            conditions.append(Receipt.user_id == current_user.id)

        if date_from:
            logger.debug(f"Applying date_from filter: {date_from}")
            conditions.append(Receipt.date >= date_from)
        if date_to:
            logger.debug(f"Applying date_to filter: {date_to}")
            conditions.append(Receipt.date <= date_to)

        if conditions:
            stmt = stmt.where(*conditions)

        stmt = stmt.group_by(date_expr).order_by(date_expr)

        logger.debug("Executing receipts timeseries query")
        results = session.exec(stmt).all()
        logger.debug(f"Retrieved {len(results)} timeseries data points")

        timeseries_data = [
            TimeSeriesData(date=row.date, value=float(row.value))
            for row in results
        ]

        logger.info(f"Receipts timeseries request completed: {len(timeseries_data)} data points")
        return timeseries_data

@router.get("/timeseries/amounts", response_model=List[TimeSeriesData])
async def get_amounts_timeseries(
        current_user: User = Depends(get_current_user),
        date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
        date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
        user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)"),
        aggregation: AggregationType = Query(AggregationType.DAY, description="Aggregálás szintje: day, month, year")
):
    """Get time series data for amounts spent by date - calculated in database"""
    logger.info(f"Amounts timeseries request from user: {current_user.username}")
    logger.debug(f"Query parameters: date_from={date_from}, date_to={date_to}, user_id={user_id}, aggregation={aggregation}")
    
    with Session(engine) as session:
        # Date grouping logic - ugyanaz mint a receipts endpointnál
        logger.debug(f"Setting up date grouping for aggregation: {aggregation}")
        if aggregation == AggregationType.YEAR:
            date_expr = func.date_trunc("year", Receipt.date)
        elif aggregation == AggregationType.MONTH:
            date_expr = func.date_trunc("month", Receipt.date)
        else:  # AggregationType.DAY
            date_expr = func.date_trunc("day", Receipt.date)

        # Build query with SQL aggregation
        logger.debug("Building amounts timeseries query")
        stmt = select(
            date_expr.label("date"),
            func.sum(ReceiptItem.unit_price * ReceiptItem.quantity).label("total_amount")
        ).select_from(Receipt).join(ReceiptItem)

        # Filtering
        conditions = []
        is_admin = is_admin_user(current_user)
        logger.debug(f"User admin status: {is_admin}")
        
        if is_admin and user_id is not None:
            logger.debug(f"Admin filtering by user_id: {user_id}")
            conditions.append(Receipt.user_id == user_id)
        elif is_admin and not user_id:
            logger.debug("Admin requesting all users data")
            pass
        else:
            logger.debug(f"Regular user requesting own data: {current_user.id}")
            conditions.append(Receipt.user_id == current_user.id)

        if date_from:
            logger.debug(f"Applying date_from filter: {date_from}")
            conditions.append(Receipt.date >= date_from)
        if date_to:
            logger.debug(f"Applying date_to filter: {date_to}")
            conditions.append(Receipt.date <= date_to)

        if conditions:
            stmt = stmt.where(*conditions)

        stmt = stmt.group_by(date_expr).order_by(date_expr)

        logger.debug("Executing amounts timeseries query")
        results = session.exec(stmt).all()
        logger.debug(f"Retrieved {len(results)} timeseries data points")

        timeseries_data = [
            TimeSeriesData(date=row.date, value=float(row.total_amount))
            for row in results
        ]

        logger.info(f"Amounts timeseries request completed: {len(timeseries_data)} data points")
        return timeseries_data

@router.get("/wordcloud", response_model=List[WordCloudItem])
async def get_wordcloud_data(
        current_user: User = Depends(get_current_user),
        date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
        date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
        user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)"),
        limit: int = Query(30, ge=1, le=100, description="Number of items to return")
):
    """Get word cloud data for most frequently purchased items - calculated in database"""
    logger.info(f"Wordcloud data request from user: {current_user.username}")
    logger.debug(f"Query parameters: date_from={date_from}, date_to={date_to}, user_id={user_id}, limit={limit}")
    
    with Session(engine) as session:
        # Build query to get item statistics
        logger.debug("Building wordcloud query")
        query = select(
            ReceiptItem.name,
            func.count().label("count"),
            func.sum(ReceiptItem.unit_price * ReceiptItem.quantity).label("total_spent")
        ).select_from(
            ReceiptItem.__table__.join(Receipt.__table__, ReceiptItem.receipt_id == Receipt.id)
        ).group_by(ReceiptItem.name)

        # Apply user filter
        is_admin = is_admin_user(current_user)
        logger.debug(f"User admin status: {is_admin}")
        
        if is_admin and user_id is not None:
            logger.debug(f"Admin filtering by user_id: {user_id}")
            query = query.where(Receipt.user_id == user_id)
        elif is_admin and not user_id:
            logger.debug("Admin requesting all users data")
            pass
        else:
            logger.debug(f"Regular user requesting own data: {current_user.id}")
            query = query.where(Receipt.user_id == current_user.id)

        # Apply date filters
        if date_from:
            logger.debug(f"Applying date_from filter: {date_from}")
            query = query.where(Receipt.date >= date_from)
        if date_to:
            logger.debug(f"Applying date_to filter: {date_to}")
            query = query.where(Receipt.date <= date_to)

        # Order by count descending and limit
        logger.debug(f"Applying order and limit: {limit}")
        query = query.order_by(text("count DESC")).limit(limit)

        # Execute query
        logger.debug("Executing wordcloud query")
        results = session.exec(query).all()
        logger.debug(f"Retrieved {len(results)} wordcloud items")

        # Convert to WordCloudItem objects
        wordcloud_data = [
            WordCloudItem(
                text=result[0],
                value=result[1],
                total_spent=float(result[2])
            )
            for result in results
        ]

        logger.info(f"Wordcloud data request completed: {len(wordcloud_data)} items")
        return wordcloud_data
    
@router.get("/market/total-spent", response_model=MarketTotalSpentList)
async def get_market_total_spent(
    current_user: User = Depends(get_current_user),
    date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
    date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
    user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)")
):
    """Összköltés marketenként - minden aggregáció az adatbázisban történik"""
    logger.info(f"Market total spent request from user: {current_user.username}")
    logger.debug(f"Query parameters: date_from={date_from}, date_to={date_to}, user_id={user_id}")
    
    with Session(engine) as session:
        logger.debug("Building market total spent query")
        query = select(
            Market.name,
            func.sum(ReceiptItem.unit_price * ReceiptItem.quantity).label("total_spent")
        ).select_from(
            ReceiptItem.__table__
            .join(Receipt.__table__, ReceiptItem.receipt_id == Receipt.id)
            .join(Market.__table__, Receipt.market_id == Market.id)
        )

        # User filter
        is_admin = is_admin_user(current_user)
        logger.debug(f"User admin status: {is_admin}")
        
        if is_admin and user_id is not None:
            logger.debug(f"Admin filtering by user_id: {user_id}")
            query = query.where(Receipt.user_id == user_id)
        elif is_admin and not user_id:
            logger.debug("Admin requesting all users data")
            pass
        else:
            logger.debug(f"Regular user requesting own data: {current_user.id}")
            query = query.where(Receipt.user_id == current_user.id)

        # Date filters
        if date_from:
            logger.debug(f"Applying date_from filter: {date_from}")
            query = query.where(Receipt.date >= date_from)
        if date_to:
            logger.debug(f"Applying date_to filter: {date_to}")
            query = query.where(Receipt.date <= date_to)

        query = query.group_by(Market.name)

        logger.debug("Executing market total spent query")
        results = session.exec(query).all()
        logger.debug(f"Retrieved {len(results)} markets")

        markets = [
            MarketTotalSpent(market_name=row[0], total_spent=float(row[1] or 0.0))
            for row in results
        ]

        result = MarketTotalSpentList(markets=markets)
        logger.info(f"Market total spent request completed: {len(result.markets)} markets")
        return result

@router.get("/market/total-receipts", response_model=MarketTotalReceiptsList)
async def get_market_total_receipts(
    current_user: User = Depends(get_current_user),
    date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
    date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
    user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)")
):
    """Vásárlások száma marketenként - aggregáció az adatbázisban"""
    logger.info(f"Market total receipts request from user: {current_user.username}")
    logger.debug(f"Query parameters: date_from={date_from}, date_to={date_to}, user_id={user_id}")
    
    with Session(engine) as session:
        logger.debug("Building market total receipts query")
        query = select(
            Market.name,
            func.count(Receipt.id).label("total_receipts")
        ).select_from(
            Receipt.__table__.join(Market.__table__, Receipt.market_id == Market.id)
        )

        # User filter
        is_admin = is_admin_user(current_user)
        logger.debug(f"User admin status: {is_admin}")
        
        if is_admin and user_id is not None:
            logger.debug(f"Admin filtering by user_id: {user_id}")
            query = query.where(Receipt.user_id == user_id)
        elif is_admin and not user_id:
            logger.debug("Admin requesting all users data")
            pass
        else:
            logger.debug(f"Regular user requesting own data: {current_user.id}")
            query = query.where(Receipt.user_id == current_user.id)

        # Date filters
        if date_from:
            logger.debug(f"Applying date_from filter: {date_from}")
            query = query.where(Receipt.date >= date_from)
        if date_to:
            logger.debug(f"Applying date_to filter: {date_to}")
            query = query.where(Receipt.date <= date_to)

        query = query.group_by(Market.name)

        logger.debug("Executing market total receipts query")
        results = session.exec(query).all()
        logger.debug(f"Retrieved {len(results)} markets")

        markets = [
            MarketTotalReceipts(market_name=row[0], total_receipts=int(row[1] or 0))
            for row in results
        ]

        result = MarketTotalReceiptsList(markets=markets)
        logger.info(f"Market total receipts request completed: {len(result.markets)} markets")
        return result

@router.get("/market/average-spent", response_model=MarketAverageSpentList)
async def get_market_average_spent(
    current_user: User = Depends(get_current_user),
    date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
    date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
    user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)")
):
    """Átlagos költés marketenként - aggregáció az adatbázisban"""
    logger.info(f"Market average spent request from user: {current_user.username}")
    logger.debug(f"Query parameters: date_from={date_from}, date_to={date_to}, user_id={user_id}")
    
    with Session(engine) as session:
        logger.debug("Building market average spent query")
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
        is_admin = is_admin_user(current_user)
        logger.debug(f"User admin status: {is_admin}")
        
        if is_admin and user_id is not None:
            logger.debug(f"Admin filtering by user_id: {user_id}")
            query = query.where(Receipt.user_id == user_id)
        elif is_admin and not user_id:
            logger.debug("Admin requesting all users data")
            pass
        else:
            logger.debug(f"Regular user requesting own data: {current_user.id}")
            query = query.where(Receipt.user_id == current_user.id)

        # Date filters
        if date_from:
            logger.debug(f"Applying date_from filter: {date_from}")
            query = query.where(Receipt.date >= date_from)
        if date_to:
            logger.debug(f"Applying date_to filter: {date_to}")
            query = query.where(Receipt.date <= date_to)

        query = query.group_by(Market.name)

        logger.debug("Executing market average spent query")
        results = session.exec(query).all()
        logger.debug(f"Retrieved {len(results)} markets")

        markets = [
            MarketAverageSpent(market_name=row[0], average_spent=float(row[1] or 0.0))
            for row in results
        ]

        result = MarketAverageSpentList(markets=markets)
        logger.info(f"Market average spent request completed: {len(result.markets)} markets")
        return result
