import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlmodel import Session, select, func
import shutil
import os
import mimetypes
from typing import List, Optional
import time
from sqlalchemy import text

from auth.models import User
from auth.routes import get_current_user, engine
from auth.schemas import Role
from receipt.ai.agent import recognize_receipt
from receipt.models import Market, Receipt, ReceiptItem
from receipt.schemas import ReceiptOut, MarketOut, ReceiptItemOut, UserOut, ReceiptListOut, \
    ReceiptUpdateRequest, MarketUpdateRequest, ReceiptCreateRequest
from receipt.utils import is_admin_user, get_receipts_count, get_receipts_paginated

# Központi konfiguráció
UPLOADS_DIR = "receipt_images"
os.makedirs(UPLOADS_DIR, exist_ok=True)
router = APIRouter(prefix="/receipt", tags=["receipt"])



@router.post("/recognize", response_model=ReceiptOut)
async def create_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # Generate UUID filename with original extension
    file_extension = os.path.splitext(file.filename)[-1]
    uuid_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOADS_DIR, uuid_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Recognize receipt
    try:
        receipt_data = recognize_receipt(file_path)
    except Exception as e:
        # Clean up file if recognition fails
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Receipt recognition failed: {str(e)}")

    # 3. Upsert Market and Address
    with Session(engine) as session:
        # Market
        market_data = receipt_data.market  # type: ignore
        market = session.exec(select(Market).where(
            Market.name == market_data.name, 
            Market.tax_number == market_data.tax_number
        )).first()
        if not market:
            market = Market(name=market_data.name, tax_number=market_data.tax_number)
            session.add(market)
            session.commit()
            session.refresh(market)
        
        # 4. Save Receipt with user and file info
        if not market.id or not current_user.id:
            raise HTTPException(status_code=500, detail="Failed to create required entities")
        
        # Get address data from AI recognition
        address_data = receipt_data.address  # type: ignore

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
        
        # 5. Save ReceiptItems
        if not receipt.id:
            raise HTTPException(status_code=500, detail="Failed to create receipt")
            
        for item in receipt_data.items:  # type: ignore
            receipt_item = ReceiptItem(
                name=item.name,
                unit_price=item.unit_price,
                quantity=item.quantity,
                unit=item.unit,
                receipt_id=receipt.id
            )
            session.add(receipt_item)
        session.commit()
        
        # 6. Return the created receipt (with items, market, and address)
        items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt.id)).all()
        
        # Calculate total
        total = sum(item.unit_price * item.quantity for item in items)
        
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
    with Session(engine) as session:
        # Get total count for pagination
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
        
        # Get paginated receipts
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
        print(receipts)
        
        # Build complete response for each receipt
        response_receipts = []
        for item in receipts:
            receipt = item[0]
            # Get market and user
            market = session.exec(select(Market).where(Market.id == receipt.market_id)).first()
            user = session.exec(select(User).where(User.id == receipt.user_id)).first()
            items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt.id)).all()
            
            # Skip if market or user not found
            if not market or not user:
                continue
            
            # Calculate total for this receipt
            total = item[1]
            
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
        return ReceiptListOut(
            receipts=response_receipts,
            skip=skip,
            limit=limit,
            total=total_count,
            has_next=skip + limit < total_count,
            has_previous=skip > 0
        )


@router.put("/{receipt_id}", response_model=ReceiptOut)
async def update_receipt(
    receipt_id: int,
    update_data: ReceiptUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update receipt data, items, and market"""
    with Session(engine) as session:
        # Get the receipt and verify ownership
        receipt = session.exec(select(Receipt).where(Receipt.id == receipt_id)).first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        # Check if user owns the receipt or is admin
        if receipt.user_id != current_user.id and not is_admin_user(current_user):
            raise HTTPException(status_code=403, detail="Not authorized to update this receipt")
        
        # Update market if market_id is provided
        if update_data.market_id is not None:
            market = session.exec(select(Market).where(Market.id == update_data.market_id)).first()
            if not market:
                raise HTTPException(status_code=404, detail="Market not found")
            receipt.market_id = update_data.market_id
        
        # Update receipt fields if provided
        if update_data.date is not None:
            receipt.date = update_data.date
        if update_data.receipt_number is not None:
            receipt.receipt_number = update_data.receipt_number
        if update_data.postal_code is not None:
            receipt.postal_code = update_data.postal_code
        if update_data.city is not None:
            receipt.city = update_data.city
        if update_data.street_name is not None:
            receipt.street_name = update_data.street_name
        if update_data.street_number is not None:
            receipt.street_number = update_data.street_number
        
        # Handle items update if provided
        if update_data.items is not None:
            # Get existing items
            existing_items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt_id)).all()
            existing_item_ids = {item.id for item in existing_items if item.id}
            
            # Track items to keep
            items_to_keep = set()
            
            # Process each item in the update request
            for item_data in update_data.items:
                if item_data.id is not None:
                    # Update existing item
                    existing_item = session.exec(select(ReceiptItem).where(ReceiptItem.id == item_data.id)).first()
                    if existing_item and existing_item.receipt_id == receipt_id:
                        existing_item.name = item_data.name
                        existing_item.unit_price = item_data.unit_price
                        existing_item.quantity = item_data.quantity
                        existing_item.unit = item_data.unit
                        items_to_keep.add(item_data.id)
                    else:
                        raise HTTPException(status_code=400, detail=f"Item with id {item_data.id} not found or doesn't belong to this receipt")
                else:
                    # Add new item
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
            for item_id in items_to_delete:
                item_to_delete = session.exec(select(ReceiptItem).where(ReceiptItem.id == item_id)).first()
                if item_to_delete:
                    session.delete(item_to_delete)
        
        session.commit()
        session.refresh(receipt)
        
        # Get updated data for response
        market = session.exec(select(Market).where(Market.id == receipt.market_id)).first()
        user = session.exec(select(User).where(User.id == receipt.user_id)).first()
        items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt_id)).all()
        
        if not market or not user:
            raise HTTPException(status_code=500, detail="Failed to retrieve related data")
        
        # Calculate total
        total = sum(item.unit_price * item.quantity for item in items)
        
        # Create response
        return ReceiptOut(
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


@router.put("/market/{market_id}", response_model=MarketOut)
async def update_market(
    market_id: int,
    market_data: MarketUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update market information"""
    with Session(engine) as session:
        # Get the market
        market = session.exec(select(Market).where(Market.id == market_id)).first()
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Update market fields
        market.name = market_data.name
        market.tax_number = market_data.tax_number
        
        session.commit()
        session.refresh(market)
        
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
    with Session(engine) as session:
        market = session.exec(select(Market).where(Market.id == market_id)).first()
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        
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
    with Session(engine) as session:
        query = select(Market)
        
        # Apply filters
        if name:
            query = query.where(text(f"markets.name LIKE '%{name}%'"))
        if tax_number:
            query = query.where(text(f"markets.tax_number LIKE '%{tax_number}%'"))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        markets = session.exec(query).all()
        
        return [
            MarketOut(
                id=market.id or 0,
                name=market.name,
                tax_number=market.tax_number
            )
            for market in markets
        ]


@router.post("/market", response_model=MarketOut)
async def create_market(
    market_data: MarketUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new market"""
    with Session(engine) as session:
        # Check if market with same name and tax number already exists
        existing_market = session.exec(select(Market).where(
            Market.name == market_data.name,
            Market.tax_number == market_data.tax_number
        )).first()
        
        if existing_market:
            raise HTTPException(status_code=400, detail="Market with this name and tax number already exists")
        
        # Create new market
        new_market = Market(
            name=market_data.name,
            tax_number=market_data.tax_number
        )
        
        session.add(new_market)
        session.commit()
        session.refresh(new_market)
        
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
    with Session(engine) as session:
        # Get the market
        market = session.exec(select(Market).where(Market.id == market_id)).first()
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Check if there are any receipts associated with this market
        receipts_count = session.exec(select(func.count()).where(Receipt.market_id == market_id)).one()
        if receipts_count and receipts_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete market. There are {receipts_count} receipts associated with this market."
            )
        
        # Delete the market
        session.delete(market)
        session.commit()
        
        return {"message": "Market deleted successfully"}


@router.post("/receipt", response_model=ReceiptOut)
async def create_receipt_manual(
    receipt_data: ReceiptCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Manuális receipt létrehozás (admin bármely userhez, mezei user csak magához)"""
    with Session(engine) as session:
        # Market ellenőrzés
        market = session.exec(select(Market).where(Market.id == receipt_data.market_id)).first()
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        # User kiválasztás
        user_id: int
        if is_admin_user(current_user) and receipt_data.user_id is not None:
            user_id = int(receipt_data.user_id)
            user = session.exec(select(User).where(User.id == user_id)).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            user_id = int(current_user.id or 0)
            user = current_user
        # Receipt létrehozás
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
        # Items kezelése
        items = []
        total = 0.0
        
        if receipt_data.items and receipt.id:
            for item_data in receipt_data.items:
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
            
            # Calculate total
            total = sum(item.unit_price * item.quantity for item in items)
        
        return ReceiptOut(
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


@router.delete("/receipt/{receipt_id}")
async def delete_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_user)
):
    """Receipt törlése (mezei user csak a sajátját, admin mindent)"""
    with Session(engine) as session:
        receipt = session.exec(select(Receipt).where(Receipt.id == receipt_id)).first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        if not (is_admin_user(current_user) or receipt.user_id == current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to delete this receipt")
        # Törlés előtt töröljük a hozzá tartozó tételeket is
        items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt_id)).all()
        for item in items:
            session.delete(item)
        session.delete(receipt)
        session.commit()
        return {"message": "Receipt deleted successfully"}


@router.get("/receipt/{receipt_id}/image")
async def download_receipt_image(
    receipt_id: int,
    current_user: User = Depends(get_current_user)
):
    """Receipt képének letöltése (mezei user csak a sajátját, admin mindent)"""
    with Session(engine) as session:
        receipt = session.exec(select(Receipt).where(Receipt.id == receipt_id)).first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        # Ellenőrizzük, hogy a felhasználó jogosult-e a receipt képének letöltésére
        if not (is_admin_user(current_user) or receipt.user_id == current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to download this receipt image")
        
        # Ellenőrizzük, hogy a képfájl létezik-e
        if not receipt.image_path or not os.path.exists(receipt.image_path):
            raise HTTPException(status_code=404, detail="Receipt image file not found")

        filename = receipt.original_filename
        if not Path(filename).suffix:
            filename = "result.jpg"

        # Content-Type meghatározása a mimetypes modullal
        media_type, _ = mimetypes.guess_type(receipt.image_path)
        if not media_type:
            media_type = 'image/*'  # fallback
        
        # Visszaadjuk a fájlt a megfelelő Content-Type-dal
        return FileResponse(
            path=receipt.image_path,
            filename=filename,
            media_type=media_type
        )
