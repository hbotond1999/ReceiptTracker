#!/usr/bin/env python3
"""
Teszt adat generátor script
Generál 10 boltot és 5000-10000 számlát tesztelési célokra
"""

import random
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import SQLModel, Session, create_engine, select
from dotenv import load_dotenv

# Add the current directory to sys.path so we can import our models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth.models import User
from receipt.models import Receipt, Market, ReceiptItem

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

# Test data lists
MARKET_NAMES = [
    "Tesco", "Auchan", "Spar", "CBA", "Penny Market",
    "Lidl", "Aldi", "Interspar", "Coop", "Match"
]

HUNGARIAN_CITIES = [
    "Budapest", "Debrecen", "Szeged", "Miskolc", "Pécs",
    "Győr", "Nyíregyháza", "Kecskemét", "Székesfehérvár", "Szombathely",
    "Szolnok", "Tatabánya", "Kaposvár", "Békéscsaba", "Zalaegerszeg"
]

STREET_NAMES = [
    "Fő utca", "Kossuth utca", "Petőfi utca", "Dózsa György utca", "Rákóczi utca",
    "Arany János utca", "Vörösmarty utca", "Széchenyi utca", "József Attila utca",
    "Móricz Zsigmond utca", "Bartók Béla utca", "Kodály Zoltán utca"
]

PRODUCT_NAMES = [
    "Kenyér", "Tej", "Tojás", "Sajt", "Sonka", "Csirke", "Marhahús",
    "Alma", "Banán", "Narancs", "Paradicsom", "Uborka", "Hagyma",
    "Krumpli", "Rizs", "Tészta", "Cukor", "Só", "Olaj", "Vaj",
    "Joghurt", "Kefir", "Túró", "Kolbász", "Virsli", "Bacon",
    "Brokkoli", "Sárgarépa", "Paprika", "Saláta", "Szőlő", "Körte",
    "Eper", "Cseresznye", "Sör", "Víz", "Üdítő", "Kávé", "Tea",
    "Csokoládé", "Keksz", "Chips", "Mosószer", "Fogkrém", "Sampon"
]

def generate_tax_number() -> str:
    """Generate a realistic Hungarian tax number"""
    return f"{random.randint(10000000, 99999999)}-{random.randint(1, 9)}-{random.randint(10, 99)}"

def generate_receipt_number() -> str:
    """Generate a realistic receipt number"""
    return f"#{random.randint(100000, 999999)}"

def generate_address() -> tuple:
    """Generate a realistic Hungarian address"""
    postal_code = f"{random.randint(1000, 9999)}"
    city = random.choice(HUNGARIAN_CITIES)
    street_name = random.choice(STREET_NAMES)
    street_number = f"{random.randint(1, 200)}"
    return postal_code, city, street_name, street_number

def generate_random_date() -> datetime:
    """Generate a random date within the last 2 years"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years ago
    random_days = random.randint(0, 730)
    return start_date + timedelta(days=random_days)

def create_markets(session: Session) -> List[Market]:
    """Create test markets"""
    markets = []
    print("Creating markets...")
    
    for i, market_name in enumerate(MARKET_NAMES):
        market = Market(
            name=market_name,
            tax_number=generate_tax_number()
        )
        session.add(market)
        markets.append(market)
        print(f"  - {market_name}")
    
    session.commit()
    print(f"Created {len(markets)} markets")
    return markets

def create_receipts_and_items(session: Session, markets: List[Market], users: List[User], count: int):
    """Create test receipts and receipt items"""
    print(f"Creating {count} receipts...")
    
    for i in range(count):
        # Generate receipt data
        postal_code, city, street_name, street_number = generate_address()
        
        selected_market = random.choice(markets)
        selected_user = random.choice(users)
        
        receipt = Receipt(
            date=generate_random_date(),
            receipt_number=generate_receipt_number(),
            market_id=selected_market.id or 0,
            user_id=selected_user.id or 0,
            image_path=f"receipt_images/receipt_{i+1}.jpg",
            original_filename=f"receipt_{i+1}.jpg",
            postal_code=postal_code,
            city=city,
            street_name=street_name,
            street_number=street_number
        )
        session.add(receipt)
        session.commit()
        session.refresh(receipt)
        
        # Generate 1-10 items per receipt
        item_count = random.randint(1, 10)
        total_price = 0
        
        for j in range(item_count):
            item = ReceiptItem(
                name=random.choice(PRODUCT_NAMES),
                price=round(random.uniform(100, 5000), 2),  # 100-5000 HUF
                receipt_id=receipt.id or 0
            )
            session.add(item)
            total_price += item.price
        
        if (i + 1) % 100 == 0:
            print(f"  - Created {i + 1} receipts...")
            session.commit()
    
    session.commit()
    print(f"Created {count} receipts with items")

def get_existing_users(session: Session) -> List[User]:
    """Get existing users from the database"""
    users = session.exec(select(User)).all()
    return list(users)

def main():
    """Main function to generate test data"""
    print("=== Receipt Tracker Test Data Generator ===")
    print("This script will generate test data for the Receipt Tracker application.")
    print("- 10 markets")
    print("- 5000-10000 receipts")
    print("- Multiple items per receipt")
    print()
    
    # Confirm before proceeding
    response = input("Do you want to proceed? (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return
    
    # Create database tables if they don't exist
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # Check if users exist
        existing_users = get_existing_users(session)
        if not existing_users:
            print("ERROR: No users found in the database!")
            print("Please create at least one user before running this script.")
            print("You can use the create_admin.py script to create an admin user.")
            return
        
        print(f"Found {len(existing_users)} existing users")
        
        # Check if markets already exist
        existing_markets = session.exec(select(Market)).all()
        if existing_markets:
            print(f"Found {len(existing_markets)} existing markets")
            response = input("Do you want to create additional markets? (y/N): ")
            if response.lower() == 'y':
                markets = create_markets(session)
                markets.extend(existing_markets)
            else:
                markets = list(existing_markets)
        else:
            markets = create_markets(session)
        
        # Generate receipts
        receipt_count = random.randint(5000, 10000)
        print(f"\nGenerating {receipt_count} receipts...")
        
        create_receipts_and_items(session, markets, existing_users, receipt_count)
        
        # Summary
        print("\n=== Generation Complete ===")
        print(f"Markets: {len(markets)}")
        print(f"Receipts: {receipt_count}")
        print(f"Users: {len(existing_users)}")
        
        # Database statistics
        total_receipts = len(session.exec(select(Receipt)).all())
        total_items = len(session.exec(select(ReceiptItem)).all())
        total_markets = len(session.exec(select(Market)).all())
        
        print(f"\nDatabase totals:")
        print(f"- Total markets: {total_markets}")
        print(f"- Total receipts: {total_receipts}")
        print(f"- Total receipt items: {total_items}")
        print(f"- Average items per receipt: {total_items/total_receipts:.2f}")

if __name__ == "__main__":
    main() 