import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlmodel import Session, select, func
import shutil
import os
import mimetypes
from typing import List, Optional
from datetime import datetime
from sqlalchemy import text

from auth.models import User
from auth.routes import get_current_user, engine
from auth.schemas import Role
from receipt.ai.agent import recognize_receipt
from receipt.models import Market, Receipt, ReceiptItem
from receipt.schemas import ReceiptOut, MarketOut, ReceiptItemOut, UserOut, ReceiptListOut, \
    ReceiptUpdateRequest, MarketUpdateRequest, ReceiptCreateRequest
from receipt.utils import is_admin_user, get_receipts_count, get_receipts_paginated
from app_logging import get_logger

# Központi konfiguráció
UPLOADS_DIR = "receipt_images"
os.makedirs(UPLOADS_DIR, exist_ok=True)
router = APIRouter(prefix="/receipt", tags=["receipt"])

# Initialize logger
logger = get_logger(__name__)



@router.post("/recognize", response_model=ReceiptOut)
async def create_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Receipt recognition started for user: {current_user.username}, file: {file.filename}")
    logger.debug(f"File details: content_type={file.content_type}, size={file.size}")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        logger.warning(f"Invalid file type uploaded: {file.content_type}")
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    # Validate filename
    if not file.filename:
        logger.warning("File uploaded without filename")
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # Generate UUID filename with original extension
    file_extension = os.path.splitext(file.filename)[-1]
    uuid_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOADS_DIR, uuid_filename)
    
    logger.debug(f"Saving uploaded file to: {file_path}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.debug(f"File saved successfully: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # 2. Recognize receipt
    logger.debug("Starting AI receipt recognition")
    try:
        receipt_data = recognize_receipt(file_path)
        logger.debug(f"Receipt recognition successful: {receipt_data}")
    except Exception as e:
        logger.error(f"Receipt recognition failed: {str(e)}")
        # Clean up file if recognition fails
        try:
            os.remove(file_path)
            logger.debug(f"Cleaned up file after recognition failure: {file_path}")
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Receipt recognition failed: {str(e)}")

    # 3. Upsert Market and Address
    logger.debug("Processing market and address data")
    with Session(engine) as session:
        # Market
        market_data = receipt_data.market  # type: ignore
        logger.debug(f"Market data: name={market_data.name}, tax_number={market_data.tax_number}")
        
        market = session.exec(select(Market).where(
            Market.name == market_data.name, 
            Market.tax_number == market_data.tax_number
        )).first()
        
        if not market:
            logger.debug("Market not found, creating new market")
            market = Market(name=market_data.name, tax_number=market_data.tax_number)
            session.add(market)
            session.commit()
            session.refresh(market)
            logger.debug(f"New market created with ID: {market.id}")
        else:
            logger.debug(f"Existing market found with ID: {market.id}")
        
        # 4. Save Receipt with user and file info
        if not market.id or not current_user.id:
            logger.error("Failed to create required entities - missing market or user ID")
            raise HTTPException(status_code=500, detail="Failed to create required entities")
        
        # Get address data from AI recognition
        address_data = receipt_data.address  # type: ignore
        logger.debug(f"Address data: postal_code={address_data.postal_code}, city={address_data.city}, street={address_data.street_name} {address_data.street_number}")

        logger.debug("Creating receipt record")
        receipt = Receipt(
            date=receipt_data.date,  # type: ignore
            receipt_number=receipt_data.receipt_number,  # type: ignore
            market_id=market.id,
            user_id=current_user.id,
            image_path=file_path,
            original_filename=file.filename,
            postal_code=address_data.postal_code,
            city=address_data.city,
            street_name=address_data.street_name,
            street_number=address_data.street_number
        )
        session.add(receipt)
        session.commit()
        session.refresh(receipt)
        logger.debug(f"Receipt created with ID: {receipt.id}")
        
        # 5. Save ReceiptItems
        if not receipt.id:
            logger.error("Failed to create receipt - missing receipt ID")
            raise HTTPException(status_code=500, detail="Failed to create receipt")
        
        logger.debug(f"Processing {len(receipt_data.items)} receipt items")
        for i, item in enumerate(receipt_data.items):  # type: ignore
            logger.debug(f"Processing item {i+1}: name={item.name}, unit_price={item.unit_price}, quantity={item.quantity}, unit={item.unit}")
            receipt_item = ReceiptItem(
                name=item.name,
                unit_price=item.unit_price,
                quantity=item.quantity,
                unit=item.unit,
                receipt_id=receipt.id
            )
            session.add(receipt_item)
        session.commit()
        logger.debug("All receipt items saved successfully")
        
        # 6. Return the created receipt (with items, market, and address)
        logger.debug("Fetching receipt items for response")
        items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt.id)).all()
        
        # Calculate total
        total = sum(item.unit_price * item.quantity for item in items)
        logger.debug(f"Receipt total calculated: {total}")
        
        # Create a complete response using the schema
        response = ReceiptOut(
            id=receipt.id,
            date=receipt.date,
            receipt_number=receipt.receipt_number,
            image_path=receipt.image_path,
            original_filename=receipt.original_filename,
            user=UserOut(
                id=current_user.id or 0,
                username=current_user.username,
                email=current_user.email,
                fullname=current_user.fullname,
                profile_picture=current_user.profile_picture,
                disabled=current_user.disabled,
                roles=[Role(role.name.value) for role in current_user.roles]
            ),
            market=MarketOut(
                id=market.id or 0,
                name=market.name,
                tax_number=market.tax_number
            ),
            postal_code=receipt.postal_code,
            city=receipt.city,
            street_name=receipt.street_name,
            street_number=receipt.street_number,
            items=[
                ReceiptItemOut(
                    id=item.id or 0,
                    name=item.name,
                    price=item.quantity * item.unit_price,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    unit=item.unit
                )
                for item in items
            ],
            total=total
        )
        
        logger.info(f"Receipt recognition completed successfully for user: {current_user.username}, receipt_id: {receipt.id}")
        return response

@router.get("/", response_model=ReceiptListOut)
async def get_receipts(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Kihagyandó rekordok száma"),
    limit: int = Query(10, ge=1, le=100, description="Visszaadandó rekordok száma (max 100)"),
    user_id: Optional[int] = Query(None, description="Szűrés felhasználó ID alapján (csak adminoknak)"),
    market_id: Optional[int] = Query(None, description="Szűrés market ID alapján"),
    market_name: Optional[str] = Query(None, description="Szűrés market név alapján (tartalmazó keresés)"),
    item_name: Optional[str] = Query(None, description="Szűrés tétel neve alapján (tartalmazó keresés)"),
    date_from: Optional[datetime] = Query(None, description="Szűrés kezdő dátum alapján"),
    date_to: Optional[datetime] = Query(None, description="Szűrés vég dátum alapján"),
    order_by: str = Query("date", description="Rendezés oszlop szerint: 'date', 'receipt_number', 'id'"),
    order_dir: str = Query("desc", description="Rendezés iránya: 'asc' vagy 'desc'")
):
    """Get receipts with optional filtering and sorting - admin users see all, regular users see only their own"""
    logger.info(f"Receipt list request from user: {current_user.username}")
    logger.debug(f"Query parameters: skip={skip}, limit={limit}, user_id={user_id}, market_id={market_id}, market_name={market_name}, item_name={item_name}, date_from={date_from}, date_to={date_to}, order_by={order_by}, order_dir={order_dir}")
    
    is_admin = is_admin_user(current_user)
    logger.debug(f"User admin status: {is_admin}")
    
    with Session(engine) as session:
        # Get total count for pagination
        logger.debug("Getting total receipt count")
        total_count = get_receipts_count(
            session=session,
            current_user=current_user,
            user_id=user_id,
            market_id=market_id,
            market_name=market_name,
            item_name=item_name,
            date_from=date_from,
            date_to=date_to
        )
        logger.debug(f"Total receipts found: {total_count}")
        
        # Get paginated receipts
        logger.debug("Fetching paginated receipts")
        receipts = get_receipts_paginated(
            session=session,
            current_user=current_user,
            user_id=user_id,
            market_id=market_id,
            market_name=market_name,
            item_name=item_name,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit,
            order_by=order_by,
            order_dir=order_dir
        )
        logger.debug(f"Retrieved {len(receipts)} receipts")
        
        # Build complete response for each receipt
        logger.debug("Building response data for receipts")
        response_receipts = []
        for i, receipt in enumerate(receipts):
            logger.debug(f"Processing receipt {i+1}/{len(receipts)}: ID={receipt.id}")
            
            # Get market and user
            market = session.exec(select(Market).where(Market.id == receipt.market_id)).first()
            user = session.exec(select(User).where(User.id == receipt.user_id)).first()
            items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt.id)).all()
            
            # Skip if market or user not found
            if not market or not user:
                logger.warning(f"Skipping receipt {receipt.id} - missing market or user data")
                continue
            
            # Calculate total for this receipt
            total = sum(item.unit_price * item.quantity for item in items)
            logger.debug(f"Receipt {receipt.id} total: {total}, items count: {len(items)}")
            
            # Create response object
            response = ReceiptOut(
                id=receipt.id or 0,
                date=receipt.date,
                receipt_number=receipt.receipt_number,
                image_path=receipt.image_path,
                original_filename=receipt.original_filename,
                user=UserOut(
                    id=user.id or 0,
                    username=user.username,
                    email=user.email,
                    fullname=user.fullname,
                    profile_picture=user.profile_picture,
                    disabled=user.disabled,
                    roles=[]  # Note: roles are not loaded here for performance
                ),
                market=MarketOut(
                    id=market.id or 0,
                    name=market.name,
                    tax_number=market.tax_number
                ),
                postal_code=receipt.postal_code,
                city=receipt.city,
                street_name=receipt.street_name,
                street_number=receipt.street_number,
                items=[
                    ReceiptItemOut(
                        id=item.id or 0,
                        name=item.name,
                        price=item.unit_price * item.quantity,
                        unit_price=item.unit_price,
                        quantity=item.quantity,
                        unit=item.unit
                    )
                    for item in items
                ],
                total=total
            )
            response_receipts.append(response)
        
        # Create paginated response
        result = ReceiptListOut(
            receipts=response_receipts,
            skip=skip,
            limit=limit,
            total=total_count,
            has_next=skip + limit < total_count,
            has_previous=skip > 0
        )
        
        logger.info(f"Receipt list request completed - returned {len(response_receipts)} receipts out of {total_count} total")
        return result


@router.put("/{receipt_id}", response_model=ReceiptOut)
async def update_receipt(
    receipt_id: int,
    update_data: ReceiptUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update receipt data, items, and market"""
    logger.info(f"Receipt update request: receipt_id={receipt_id}, user={current_user.username}")
    logger.debug(f"Update data: {update_data.dict(exclude_unset=True)}")
    
    with Session(engine) as session:
        # Get the receipt and verify ownership
        logger.debug(f"Looking for receipt: {receipt_id}")
        receipt = session.exec(select(Receipt).where(Receipt.id == receipt_id)).first()
        if not receipt:
            logger.warning(f"Receipt not found: {receipt_id}")
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        logger.debug(f"Receipt found: {receipt.id}, owner: {receipt.user_id}")
        
        # Check if user owns the receipt or is admin
        is_admin = is_admin_user(current_user)
        is_owner = receipt.user_id == current_user.id
        logger.debug(f"Permission check: is_admin={is_admin}, is_owner={is_owner}")
        
        if not is_owner and not is_admin:
            logger.warning(f"Unauthorized receipt update attempt: user={current_user.username}, receipt_id={receipt_id}")
            raise HTTPException(status_code=403, detail="Not authorized to update this receipt")
        
        # Update market if market_id is provided
        if update_data.market_id is not None:
            logger.debug(f"Updating market to: {update_data.market_id}")
            market = session.exec(select(Market).where(Market.id == update_data.market_id)).first()
            if not market:
                logger.warning(f"Market not found: {update_data.market_id}")
                raise HTTPException(status_code=404, detail="Market not found")
            receipt.market_id = update_data.market_id
        
        # Update receipt fields if provided
        if update_data.date is not None:
            logger.debug(f"Updating date to: {update_data.date}")
            receipt.date = update_data.date
        if update_data.receipt_number is not None:
            logger.debug(f"Updating receipt number to: {update_data.receipt_number}")
            receipt.receipt_number = update_data.receipt_number
        if update_data.postal_code is not None:
            logger.debug(f"Updating postal code to: {update_data.postal_code}")
            receipt.postal_code = update_data.postal_code
        if update_data.city is not None:
            logger.debug(f"Updating city to: {update_data.city}")
            receipt.city = update_data.city
        if update_data.street_name is not None:
            logger.debug(f"Updating street name to: {update_data.street_name}")
            receipt.street_name = update_data.street_name
        if update_data.street_number is not None:
            logger.debug(f"Updating street number to: {update_data.street_number}")
            receipt.street_number = update_data.street_number
        
        # Handle items update if provided
        if update_data.items is not None:
            logger.debug(f"Updating receipt items: {len(update_data.items)} items provided")
            
            # Get existing items
            existing_items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt_id)).all()
            existing_item_ids = {item.id for item in existing_items if item.id}
            logger.debug(f"Existing items: {len(existing_items)}, IDs: {existing_item_ids}")
            
            # Track items to keep
            items_to_keep = set()
            
            # Process each item in the update request
            for i, item_data in enumerate(update_data.items):
                logger.debug(f"Processing item {i+1}: id={item_data.id}, name={item_data.name}")
                
                if item_data.id is not None:
                    # Update existing item
                    existing_item = session.exec(select(ReceiptItem).where(ReceiptItem.id == item_data.id)).first()
                    if existing_item and existing_item.receipt_id == receipt_id:
                        logger.debug(f"Updating existing item: {item_data.id}")
                        existing_item.name = item_data.name
                        existing_item.unit_price = item_data.unit_price
                        existing_item.quantity = item_data.quantity
                        existing_item.unit = item_data.unit
                        items_to_keep.add(item_data.id)
                    else:
                        logger.error(f"Item not found or doesn't belong to receipt: {item_data.id}")
                        raise HTTPException(status_code=400, detail=f"Item with id {item_data.id} not found or doesn't belong to this receipt")
                else:
                    # Add new item
                    logger.debug(f"Adding new item: {item_data.name}")
                    new_item = ReceiptItem(
                        name=item_data.name,
                        unit_price=item_data.unit_price,
                        quantity=item_data.quantity,
                        unit=item_data.unit,
                        receipt_id=receipt_id
                    )
                    session.add(new_item)
            
            # Delete items that are not in the update request
            items_to_delete = existing_item_ids - items_to_keep
            logger.debug(f"Items to delete: {items_to_delete}")
            
            for item_id in items_to_delete:
                item_to_delete = session.exec(select(ReceiptItem).where(ReceiptItem.id == item_id)).first()
                if item_to_delete:
                    logger.debug(f"Deleting item: {item_id}")
                    session.delete(item_to_delete)
        
        logger.debug("Saving receipt updates to database")
        session.commit()
        session.refresh(receipt)
        
        # Get updated data for response
        logger.debug("Fetching updated data for response")
        market = session.exec(select(Market).where(Market.id == receipt.market_id)).first()
        user = session.exec(select(User).where(User.id == receipt.user_id)).first()
        items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt_id)).all()
        
        if not market or not user:
            logger.error("Failed to retrieve related data after update")
            raise HTTPException(status_code=500, detail="Failed to retrieve related data")
        
        # Calculate total
        total = sum(item.unit_price * item.quantity for item in items)
        logger.debug(f"Updated receipt total: {total}")
        
        # Create response
        response = ReceiptOut(
            id=receipt.id or 0,
            date=receipt.date,
            receipt_number=receipt.receipt_number,
            image_path=receipt.image_path,
            original_filename=receipt.original_filename,
            user=UserOut(
                id=user.id or 0,
                username=user.username,
                email=user.email,
                fullname=user.fullname,
                profile_picture=user.profile_picture,
                disabled=user.disabled,
                roles=[Role(role.name.value) for role in user.roles]
            ),
            market=MarketOut(
                id=market.id or 0,
                name=market.name,
                tax_number=market.tax_number
            ),
            postal_code=receipt.postal_code,
            city=receipt.city,
            street_name=receipt.street_name,
            street_number=receipt.street_number,
            items=[
                ReceiptItemOut(
                    id=item.id or 0,
                    name=item.name,
                    price=item.unit_price * item.quantity,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    unit=item.unit
                )
                for item in items
            ],
            total=total
        )
        
        logger.info(f"Receipt update completed successfully: receipt_id={receipt_id}")
        return response


@router.put("/market/{market_id}", response_model=MarketOut)
async def update_market(
    market_id: int,
    market_data: MarketUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update market information"""
    logger.info(f"Market update request: market_id={market_id}, user={current_user.username}")
    logger.debug(f"Market update data: name={market_data.name}, tax_number={market_data.tax_number}")
    
    with Session(engine) as session:
        # Get the market
        logger.debug(f"Looking for market: {market_id}")
        market = session.exec(select(Market).where(Market.id == market_id)).first()
        if not market:
            logger.warning(f"Market not found: {market_id}")
            raise HTTPException(status_code=404, detail="Market not found")
        
        logger.debug(f"Market found: {market.name}")
        
        # Update market fields
        logger.debug("Updating market fields")
        market.name = market_data.name
        market.tax_number = market_data.tax_number
        
        session.commit()
        session.refresh(market)
        
        logger.info(f"Market update completed successfully: market_id={market_id}")
        return MarketOut(
            id=market.id or 0,
            name=market.name,
            tax_number=market.tax_number
        )


@router.get("/market/{market_id}", response_model=MarketOut)
async def get_market(
    market_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get market by ID"""
    logger.info(f"Market get request: market_id={market_id}, user={current_user.username}")
    
    with Session(engine) as session:
        logger.debug(f"Looking for market: {market_id}")
        market = session.exec(select(Market).where(Market.id == market_id)).first()
        if not market:
            logger.warning(f"Market not found: {market_id}")
            raise HTTPException(status_code=404, detail="Market not found")
        
        logger.debug(f"Market found: {market.name}")
        logger.info(f"Market get request completed: market_id={market_id}")
        
        return MarketOut(
            id=market.id or 0,
            name=market.name,
            tax_number=market.tax_number
        )


@router.get("/markets", response_model=List[MarketOut])
async def get_markets(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Kihagyandó rekordok száma"),
    limit: int = Query(100, ge=1, le=1000, description="Visszaadandó rekordok száma (max 1000)"),
    name: Optional[str] = Query(None, description="Szűrés név alapján (tartalmazó keresés)"),
    tax_number: Optional[str] = Query(None, description="Szűrés adószám alapján (tartalmazó keresés)")
):
    """Get all markets with optional filtering"""
    logger.info(f"Markets list request from user: {current_user.username}")
    logger.debug(f"Query parameters: skip={skip}, limit={limit}, name={name}, tax_number={tax_number}")
    
    with Session(engine) as session:
        query = select(Market)
        
        # Apply filters
        if name:
            logger.debug(f"Applying name filter: {name}")
            query = query.where(text(f"markets.name LIKE '%{name}%'"))
        if tax_number:
            logger.debug(f"Applying tax number filter: {tax_number}")
            query = query.where(text(f"markets.tax_number LIKE '%{tax_number}%'"))
        
        # Apply pagination
        logger.debug(f"Applying pagination: skip={skip}, limit={limit}")
        query = query.offset(skip).limit(limit)
        
        logger.debug("Executing markets query")
        markets = session.exec(query).all()
        logger.debug(f"Retrieved {len(markets)} markets")
        
        result = [
            MarketOut(
                id=market.id or 0,
                name=market.name,
                tax_number=market.tax_number
            )
            for market in markets
        ]
        
        logger.info(f"Markets list request completed - returned {len(result)} markets")
        return result


@router.post("/market", response_model=MarketOut)
async def create_market(
    market_data: MarketUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new market"""
    logger.info(f"Market creation request from user: {current_user.username}")
    logger.debug(f"Market creation data: name={market_data.name}, tax_number={market_data.tax_number}")
    
    with Session(engine) as session:
        # Check if market with same name and tax number already exists
        logger.debug("Checking for existing market with same name and tax number")
        existing_market = session.exec(select(Market).where(
            Market.name == market_data.name,
            Market.tax_number == market_data.tax_number
        )).first()
        
        if existing_market:
            logger.warning(f"Market already exists: name={market_data.name}, tax_number={market_data.tax_number}")
            raise HTTPException(status_code=400, detail="Market with this name and tax number already exists")
        
        # Create new market
        logger.debug("Creating new market")
        new_market = Market(
            name=market_data.name,
            tax_number=market_data.tax_number
        )
        
        session.add(new_market)
        session.commit()
        session.refresh(new_market)
        
        logger.info(f"Market created successfully: market_id={new_market.id}")
        return MarketOut(
            id=new_market.id or 0,
            name=new_market.name,
            tax_number=new_market.tax_number
        )


@router.delete("/market/{market_id}")
async def delete_market(
    market_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a market (only if no receipts are associated with it)"""
    logger.info(f"Market deletion request: market_id={market_id}, user={current_user.username}")
    
    with Session(engine) as session:
        # Get the market
        logger.debug(f"Looking for market to delete: {market_id}")
        market = session.exec(select(Market).where(Market.id == market_id)).first()
        if not market:
            logger.warning(f"Market not found for deletion: {market_id}")
            raise HTTPException(status_code=404, detail="Market not found")
        
        logger.debug(f"Market found for deletion: {market.name}")
        
        # Check if there are any receipts associated with this market
        logger.debug("Checking for associated receipts")
        receipts_count = session.exec(select(func.count()).where(Receipt.market_id == market_id)).one()
        logger.debug(f"Associated receipts count: {receipts_count}")
        
        if receipts_count and receipts_count > 0:
            logger.warning(f"Cannot delete market - has {receipts_count} associated receipts: {market_id}")
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete market. There are {receipts_count} receipts associated with this market."
            )
        
        # Delete the market
        logger.debug("Deleting market")
        session.delete(market)
        session.commit()
        
        logger.info(f"Market deleted successfully: market_id={market_id}")
        return {"message": "Market deleted successfully"}


@router.post("/receipt", response_model=ReceiptOut)
async def create_receipt_manual(
    receipt_data: ReceiptCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Manuális receipt létrehozás (admin bármely userhez, mezei user csak magához)"""
    logger.info(f"Manual receipt creation request from user: {current_user.username}")
    logger.debug(f"Receipt creation data: market_id={receipt_data.market_id}, user_id={receipt_data.user_id}, date={receipt_data.date}")
    
    with Session(engine) as session:
        # Market ellenőrzés
        logger.debug(f"Looking for market: {receipt_data.market_id}")
        market = session.exec(select(Market).where(Market.id == receipt_data.market_id)).first()
        if not market:
            logger.warning(f"Market not found: {receipt_data.market_id}")
            raise HTTPException(status_code=404, detail="Market not found")
        
        logger.debug(f"Market found: {market.name}")
        
        # User kiválasztás
        user_id: int
        is_admin = is_admin_user(current_user)
        logger.debug(f"User admin status: {is_admin}")
        
        if is_admin and receipt_data.user_id is not None:
            user_id = int(receipt_data.user_id)
            logger.debug(f"Admin creating receipt for user: {user_id}")
            user = session.exec(select(User).where(User.id == user_id)).first()
            if not user:
                logger.warning(f"Target user not found: {user_id}")
                raise HTTPException(status_code=404, detail="User not found")
            logger.debug(f"Target user found: {user.username}")
        else:
            user_id = int(current_user.id or 0)
            user = current_user
            logger.debug(f"Creating receipt for current user: {user.username}")
        
        # Receipt létrehozás
        logger.debug("Creating receipt record")
        receipt = Receipt(
            date=receipt_data.date,
            receipt_number=receipt_data.receipt_number,
            market_id=receipt_data.market_id,
            user_id=user_id,
            image_path=receipt_data.image_path,
            original_filename=receipt_data.original_filename,
            postal_code=receipt_data.postal_code,
            city=receipt_data.city,
            street_name=receipt_data.street_name,
            street_number=receipt_data.street_number
        )
        session.add(receipt)
        session.commit()
        session.refresh(receipt)
        logger.debug(f"Receipt created with ID: {receipt.id}")
        
        # Items kezelése
        items = []
        total = 0.0
        
        if receipt_data.items and receipt.id:
            logger.debug(f"Processing {len(receipt_data.items)} receipt items")
            for i, item_data in enumerate(receipt_data.items):
                logger.debug(f"Processing item {i+1}: name={item_data.name}, unit_price={item_data.unit_price}, quantity={item_data.quantity}")
                receipt_item = ReceiptItem(
                    name=item_data.name,
                    receipt_id=receipt.id,
                    unit_price=item_data.unit_price,
                    quantity=item_data.quantity,
                    unit=item_data.unit
                )
                session.add(receipt_item)
                items.append(receipt_item)
            session.commit()
            logger.debug("All receipt items saved successfully")
            
            # Calculate total
            total = sum(item.unit_price * item.quantity for item in items)
            logger.debug(f"Receipt total calculated: {total}")
        
        response = ReceiptOut(
            id=receipt.id or 0,
            date=receipt.date,
            receipt_number=receipt.receipt_number,
            image_path=receipt.image_path,
            original_filename=receipt.original_filename,
            user=UserOut(
                id=user.id or 0,
                username=user.username,
                email=user.email,
                fullname=user.fullname,
                profile_picture=user.profile_picture,
                disabled=user.disabled,
                roles=[Role(role.name.value) for role in user.roles]
            ),
            market=MarketOut(
                id=market.id or 0,
                name=market.name,
                tax_number=market.tax_number
            ),
            postal_code=receipt.postal_code,
            city=receipt.city,
            street_name=receipt.street_name,
            street_number=receipt.street_number,
            items=[
                ReceiptItemOut(
                    id=item.id or 0,
                    name=item.name,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    unit=item.unit,
                    price=item.unit_price * item.quantity,
                )
                for item in items
            ],
            total=total
        )
        
        logger.info(f"Manual receipt creation completed successfully: receipt_id={receipt.id}")
        return response


@router.delete("/receipt/{receipt_id}")
async def delete_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_user)
):
    """Receipt törlése (mezei user csak a sajátját, admin mindent)"""
    logger.info(f"Receipt deletion request: receipt_id={receipt_id}, user={current_user.username}")
    
    with Session(engine) as session:
        logger.debug(f"Looking for receipt to delete: {receipt_id}")
        receipt = session.exec(select(Receipt).where(Receipt.id == receipt_id)).first()
        if not receipt:
            logger.warning(f"Receipt not found for deletion: {receipt_id}")
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        logger.debug(f"Receipt found: owner={receipt.user_id}")
        
        is_admin = is_admin_user(current_user)
        is_owner = receipt.user_id == current_user.id
        logger.debug(f"Permission check: is_admin={is_admin}, is_owner={is_owner}")
        
        if not (is_admin or is_owner):
            logger.warning(f"Unauthorized receipt deletion attempt: user={current_user.username}, receipt_id={receipt_id}")
            raise HTTPException(status_code=403, detail="Not authorized to delete this receipt")
        
        # Törlés előtt töröljük a hozzá tartozó tételeket is
        logger.debug("Deleting associated receipt items")
        items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt_id)).all()
        for item in items:
            session.delete(item)
        logger.debug(f"Deleted {len(items)} receipt items")
        
        logger.debug("Deleting receipt")
        session.delete(receipt)
        session.commit()
        
        logger.info(f"Receipt deleted successfully: receipt_id={receipt_id}")
        return {"message": "Receipt deleted successfully"}


@router.get("/receipt/{receipt_id}/image")
async def download_receipt_image(
    receipt_id: int,
    current_user: User = Depends(get_current_user)
):
    """Receipt képének letöltése (mezei user csak a sajátját, admin mindent)"""
    logger.info(f"Receipt image download request: receipt_id={receipt_id}, user={current_user.username}")
    
    with Session(engine) as session:
        logger.debug(f"Looking for receipt: {receipt_id}")
        receipt = session.exec(select(Receipt).where(Receipt.id == receipt_id)).first()
        if not receipt:
            logger.warning(f"Receipt not found: {receipt_id}")
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        logger.debug(f"Receipt found: owner={receipt.user_id}")
        
        # Ellenőrizzük, hogy a felhasználó jogosult-e a receipt képének letöltésére
        is_admin = is_admin_user(current_user)
        is_owner = receipt.user_id == current_user.id
        logger.debug(f"Permission check: is_admin={is_admin}, is_owner={is_owner}")
        
        if not (is_admin or is_owner):
            logger.warning(f"Unauthorized receipt image download attempt: user={current_user.username}, receipt_id={receipt_id}")
            raise HTTPException(status_code=403, detail="Not authorized to download this receipt image")
        
        # Ellenőrizzük, hogy a képfájl létezik-e
        if not receipt.image_path or not os.path.exists(receipt.image_path):
            logger.warning(f"Receipt image file not found: {receipt.image_path}")
            raise HTTPException(status_code=404, detail="Receipt image file not found")

        filename = receipt.original_filename
        if not Path(filename).suffix:
            filename = "result.jpg"

        # Content-Type meghatározása a mimetypes modullal
        media_type, _ = mimetypes.guess_type(receipt.image_path)
        if not media_type:
            media_type = 'image/*'  # fallback
        
        logger.debug(f"Serving image file: {receipt.image_path}, media_type: {media_type}")
        
        # Visszaadjuk a fájlt a megfelelő Content-Type-dal
        logger.info(f"Receipt image download completed: receipt_id={receipt_id}")
        return FileResponse(
            path=receipt.image_path,
            filename=filename,
            media_type=media_type
        )
