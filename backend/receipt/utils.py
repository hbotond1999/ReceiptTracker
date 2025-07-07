from datetime import datetime
from typing import Optional, List
from sqlmodel import Session, select, func
from auth.models import User, RoleEnum
from receipt.models import Receipt, Market, ReceiptItem


def is_admin_user(user: User) -> bool:
    """Check if the user has admin role"""
    return any(role.name == RoleEnum.admin for role in user.roles)


def get_receipts_count(
    session: Session,
    current_user: User,
    user_id: Optional[int] = None,
    market_id: Optional[int] = None,
    market_name: Optional[str] = None,
    item_name: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> int:
    """Get count of receipts matching the filters."""
    
    # For item name filtering, we need a different approach to avoid GROUP BY issues
    if item_name is not None:
        # Use subquery to get distinct receipt IDs first
        subquery = select(Receipt.id).distinct()
        if not is_admin_user(current_user):
            subquery = subquery.where(Receipt.user_id == current_user.id)
        
        # Apply other filters to subquery
        if user_id is not None and is_admin_user(current_user):
            subquery = subquery.where(Receipt.user_id == user_id)
        if market_id is not None:
            subquery = subquery.where(Receipt.market_id == market_id)
        if market_name is not None:
            subquery = subquery.join(Market).where(Market.__table__.c.name.like(f"%{market_name}%"))
        if date_from is not None:
            subquery = subquery.where(Receipt.date >= date_from)
        if date_to is not None:
            subquery = subquery.where(Receipt.date <= date_to)
        
        # Join with ReceiptItem for item name filtering
        subquery = subquery.join(ReceiptItem).where(ReceiptItem.name.ilike(f"%{item_name}%"))
        
        # Count the distinct receipt IDs
        count_query = select(func.count()).select_from(subquery.subquery())
        return session.exec(count_query).one()
    
    # Build count query based on user permissions (for non-item filtering)
    query = select(func.count()).select_from(Receipt)
    if not is_admin_user(current_user):
        # Regular users can only see their own receipts
        query = query.where(Receipt.user_id == current_user.id)
    
    # Apply filters
    # User ID filter (only for admins)
    if user_id is not None and is_admin_user(current_user):
        query = query.where(Receipt.user_id == user_id)
    
    if market_id is not None:
        query = query.where(Receipt.market_id == market_id)
    
    if market_name is not None:
        # Join with Market table for name filtering
        query = query.join(Market).where(Market.name.ilike(f"%{market_name}%"))
    
    if date_from is not None:
        query = query.where(Receipt.date >= date_from)
    
    if date_to is not None:
        query = query.where(Receipt.date <= date_to)
    
    return session.exec(query).one()


def get_receipts_paginated(
    session: Session,
    current_user: User,
    user_id: Optional[int] = None,
    market_id: Optional[int] = None,
    market_name: Optional[str] = None,
    item_name: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 10,
    order_by: str = "date",
    order_dir: str = "desc"
):
    """Get paginated receipts matching the filters, with sorting."""
    # Build query based on user permissions
    query = select(Receipt)
    if not is_admin_user(current_user):
        # Regular users can only see their own receipts
        query = query.where(Receipt.user_id == current_user.id)
    # Apply filters
    # User ID filter (only for admins)
    if user_id is not None and is_admin_user(current_user):
        query = query.where(Receipt.user_id == user_id)
    if market_id is not None:
        query = query.where(Receipt.market_id == market_id)
    if market_name is not None:
        # Join with Market table for name filtering
        query = query.join(Market).where(Market.name.like(f"%{market_name}%"))
    if date_from is not None:
        query = query.where(Receipt.date >= date_from)
    if date_to is not None:
        query = query.where(Receipt.date <= date_to)
    # For item name filtering, we need to join with ReceiptItem and use DISTINCT to avoid duplicates
    if item_name is not None:
        query = query.join(ReceiptItem).where(ReceiptItem.name.ilike(f"%{item_name}%")).distinct()
    # Sorting
    allowed_columns = {"date": Receipt.date, "receipt_number": Receipt.receipt_number, "id": Receipt.id}
    sort_col = allowed_columns.get(order_by, Receipt.date)
    if order_dir == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())
    return session.exec(query.offset(skip).limit(limit)).all()
