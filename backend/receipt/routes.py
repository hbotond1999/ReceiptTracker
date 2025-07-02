import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlmodel import Session, select
import shutil
import os

from backend.auth.models import User
from backend.auth.routes import get_current_user, engine
from backend.receipt.ai.agent import recognize_receipt
from backend.receipt.models import Market, Address, Receipt, ReceiptItem

# Központi konfiguráció
UPLOADS_DIR = "receipt_images"
os.makedirs(UPLOADS_DIR, exist_ok=True)
router = APIRouter(prefix="/receipt", tags=["receipt"])

@router.post("/recognize")
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
        # 6. Return the created receipt (with items)
        receipt.items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt.id)).all()
        return receipt