import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlmodel import Session, select
import shutil
import os
from typing import List

from backend.auth.models import User, RoleEnum
from backend.auth.routes import get_current_user, engine
from backend.receipt.ai.agent import recognize_receipt
from backend.receipt.models import Market, Address, Receipt, ReceiptItem
from backend.receipt.schemas import ReceiptResponse

# Központi konfiguráció
UPLOADS_DIR = "receipt_images"
os.makedirs(UPLOADS_DIR, exist_ok=True)
router = APIRouter(prefix="/receipt", tags=["receipt"])

def is_admin_user(user: User) -> bool:
    """Check if the user has admin role"""
    return any(role.name == RoleEnum.admin for role in user.roles)

@router.post("/recognize", response_model=ReceiptResponse)
async def create_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    # Generate UUID filename with original extension
    file_extension = os.path.splitext(file.filename)[1]
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
        market_data = receipt_data['market'] if isinstance(receipt_data, dict) else receipt_data.market.dict()
        market = session.exec(select(Market).where(Market.name == market_data['name'], Market.tax_number == market_data['tax_number'])).first()
        if not market:
            market = Market(**market_data)
            session.add(market)
            session.commit()
            session.refresh(market)
        # Address
        address_data = receipt_data['address'] if isinstance(receipt_data, dict) else receipt_data.address.dict()
        address = session.exec(select(Address).where(
            Address.postal_code == address_data['postal_code'],
            Address.city == address_data['city'],
            Address.street_name == address_data['street_name'],
            Address.street_number == address_data['street_number']
        )).first()
        if not address:
            address = Address(**address_data)
            session.add(address)
            session.commit()
            session.refresh(address)
        # 4. Save Receipt with user and file info
        receipt = Receipt(
            date=receipt_data['date'] if isinstance(receipt_data, dict) else receipt_data.date,
            receipt_number=receipt_data['receipt_number'] if isinstance(receipt_data, dict) else receipt_data.receipt_number,
            market_id=market.id,
            address_id=address.id,
            user_id=current_user.id,
            image_path=file_path,
            original_filename=file.filename
        )
        session.add(receipt)
        session.commit()
        session.refresh(receipt)
        # 5. Save ReceiptItems
        items = receipt_data['items'] if isinstance(receipt_data, dict) else [item.dict() for item in receipt_data.items]
        for item in items:
            receipt_item = ReceiptItem(
                name=item['name'],
                price=item['price'],
                receipt_id=receipt.id
            )
            session.add(receipt_item)
        session.commit()
        # 6. Return the created receipt (with items, market, and address)
        receipt.items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt.id)).all()
        
        # Create a complete response using the schema
        response = ReceiptResponse(
            id=receipt.id,
            date=receipt.date,
            receipt_number=receipt.receipt_number,
            image_path=receipt.image_path,
            original_filename=receipt.original_filename,
            user={
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "fullname": current_user.fullname,
                "profile_picture": current_user.profile_picture,
                "disabled": current_user.disabled,
                "roles": [role.name for role in current_user.roles]
            },
            market={
                "id": market.id,
                "name": market.name,
                "tax_number": market.tax_number
            },
            address={
                "id": address.id,
                "postal_code": address.postal_code,
                "city": address.city,
                "street_name": address.street_name,
                "street_number": address.street_number
            },
            items=[
                {
                    "id": item.id,
                    "name": item.name,
                    "price": item.price
                }
                for item in receipt.items
            ]
        )
        return response

@router.get("/", response_model=List[ReceiptResponse])
async def get_receipts(
    current_user: User = Depends(get_current_user)
):
    """Get receipts - admin users see all, regular users see only their own"""
    with Session(engine) as session:
        # Build query based on user permissions
        if is_admin_user(current_user):
            # Admin can see all receipts
            receipts = session.exec(select(Receipt)).all()
        else:
            # Regular users can only see their own receipts
            receipts = session.exec(select(Receipt).where(Receipt.user_id == current_user.id)).all()
        
        # Build complete response for each receipt
        response_receipts = []
        for receipt in receipts:
            # Get market, address, and user
            market = session.exec(select(Market).where(Market.id == receipt.market_id)).first()
            address = session.exec(select(Address).where(Address.id == receipt.address_id)).first()
            user = session.exec(select(User).where(User.id == receipt.user_id)).first()
            items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt.id)).all()
            
            # Create response object
            response = ReceiptResponse(
                id=receipt.id,
                date=receipt.date,
                receipt_number=receipt.receipt_number,
                image_path=receipt.image_path,
                original_filename=receipt.original_filename,
                user={
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "fullname": user.fullname,
                    "profile_picture": user.profile_picture,
                    "disabled": user.disabled,
                    "roles": [role.name for role in user.roles]
                },
                market={
                    "id": market.id,
                    "name": market.name,
                    "tax_number": market.tax_number
                },
                address={
                    "id": address.id,
                    "postal_code": address.postal_code,
                    "city": address.city,
                    "street_name": address.street_name,
                    "street_number": address.street_number
                },
                items=[
                    {
                        "id": item.id,
                        "name": item.name,
                        "price": item.price
                    }
                    for item in items
                ]
            )
            response_receipts.append(response)
        
        return response_receipts