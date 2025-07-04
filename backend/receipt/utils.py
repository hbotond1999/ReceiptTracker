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
    # Build base query
    query = select(Receipt.id)
    if not is_admin_user(current_user):
        query = query.where(Receipt.user_id == current_user.id)
    if user_id is not None and is_admin_user(current_user):
        query = query.where(Receipt.user_id == user_id)
    if market_id is not None:
        query = query.where(Receipt.market_id == market_id)
    if market_name is not None:
        query = query.join(Market).where(Market.name.ilike(f"%{market_name}%"))
    if date_from is not None:
        query = query.where(Receipt.date >= date_from)
    if date_to is not None:
        query = query.where(Receipt.date <= date_to)
    if item_name is not None:
        query = query.join(ReceiptItem).where(ReceiptItem.name.ilike(f"%{item_name}%"))
    # DISTINCT Receipt.id
    query = query.distinct()
    # Lekérjük az összes egyedi Receipt.id-t, majd ezek számát adjuk vissza
    receipt_ids = session.exec(query).all()
    return len(receipt_ids)


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
        query = query.join(Market).where(Market.name.ilike(f"%{market_name}%"))
    if date_from is not None:
        query = query.where(Receipt.date >= date_from)
    if date_to is not None:
        query = query.where(Receipt.date <= date_to)
    # For item name filtering, we need to join with ReceiptItem and use DISTINCT to avoid duplicates
    if item_name is not None:
        query = query.join(ReceiptItem).where(ReceiptItem.name.like(f"%{item_name}%")).distinct(Receipt.id)
        # DISTINCT ON esetén az ORDER BY első oszlopának a Receipt.id-nek kell lennie
        if order_dir == "asc":
            query = query.order_by(Receipt.id.asc())
        else:
            query = query.order_by(Receipt.id.desc())
    else:
        # Ha nincs item_name szűrés, akkor a normál rendezés
        allowed_columns = {"date": Receipt.date, "receipt_number": Receipt.receipt_number, "id": Receipt.id}
        sort_col = allowed_columns.get(order_by, Receipt.date)
        if order_dir == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())
    return session.exec(query.offset(skip).limit(limit)).all()
