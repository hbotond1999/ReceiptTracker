#!/usr/bin/env python3
"""
Teszt adat generátor script
Generál 10 boltot és 5000-10000 számlát tesztelési célokra
Többszálú feldolgozással
"""

import random
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import SQLModel, Session, create_engine, select
from dotenv import load_dotenv
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from dataclasses import dataclass

# Add the current directory to sys.path so we can import our models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth.models import User
from receipt.models import Receipt, Market, ReceiptItem

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
# SQLite specific configuration for better concurrency
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, 
        pool_size=1,  # SQLite works better with fewer connections
        max_overflow=0,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False, "timeout": 30}
    )
else:
    # PostgreSQL/MySQL configuration
    engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=30)

# Thread-safe lock for progress reporting
progress_lock = threading.Lock()

@dataclass
class GenerationStats:
    receipts_created: int = 0
    items_created: int = 0
    
    def add_receipt(self, item_count: int):
        with progress_lock:
            self.receipts_created += 1
            self.items_created += item_count

# Global stats object
stats = GenerationStats()

# Test data lists
MARKET_NAMES = [
    "Tesco", "Auchan", "CBA","Lidl",
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

# Units for different product types
UNITS = [
    "db", "kg", "l"
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
    end_date = datetime.now() - timedelta(days=2)
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

def create_receipt_batch(market_ids: List[int], user_ids: List[int], batch_size: int, thread_id: int) -> None:
    """Create a batch of receipts with items in a separate thread"""
    try:
        with Session(engine) as session:
            # Process receipts one by one to avoid deadlocks
            for i in range(batch_size):
                # Generate receipt data
                postal_code, city, street_name, street_number = generate_address()
                
                selected_market_id = random.choice(market_ids)
                selected_user_id = random.choice(user_ids)
                
                receipt = Receipt(
                    date=generate_random_date(),
                    receipt_number=generate_receipt_number(),
                    market_id=selected_market_id,
                    user_id=selected_user_id,
                    image_path=f"receipt_images/receipt_{thread_id}_{i+1}.jpg",
                    original_filename=f"receipt_{thread_id}_{i+1}.jpg",
                    postal_code=postal_code,
                    city=city,
                    street_name=street_name,
                    street_number=street_number
                )
                
                # Add and commit receipt immediately
                session.add(receipt)
                session.commit()
                session.refresh(receipt)
                
                # Generate items for this receipt
                item_count = random.randint(1, 10)
                items_to_add = []
                
                for j in range(item_count):
                    item = ReceiptItem(
                        name=random.choice(PRODUCT_NAMES),
                        unit_price=round(random.uniform(50, 2000), 2),  # 50-2000 HUF per unit
                        quantity=round(random.uniform(0.1, 5.0), 2),  # 0.1-5.0 units
                        unit=random.choice(UNITS),
                        receipt_id=receipt.id or 0
                    )
                    items_to_add.append(item)
                
                # Bulk insert items for this receipt
                if items_to_add:
                    session.add_all(items_to_add)
                    session.commit()
                
                stats.add_receipt(item_count)
                
                # Progress update every 10 receipts
                if (i + 1) % 10 == 0:
                    with progress_lock:
                        print(f"Thread {thread_id}: {i + 1}/{batch_size} receipts processed")
            
    except Exception as e:
        print(f"Error in thread {thread_id}: {e}")
        import traceback
        traceback.print_exc()
        raise

def create_receipts_and_items_parallel(session: Session, markets: List[Market], users: List[User], count: int):
    """Create test receipts and receipt items using multiple threads"""
    print(f"Creating {count} receipts using parallel processing...")
    
    # Extract IDs for thread safety
    market_ids = [market.id for market in markets if market.id]
    user_ids = [user.id for user in users if user.id]
    
    # Calculate optimal batch size and thread count
    # SQLite works better with fewer threads due to locking
    if "sqlite" in DATABASE_URL:
        max_threads = min(os.cpu_count() or 2, 4)  # Limit to 4 threads max for SQLite
    else:
        max_threads = min(os.cpu_count() or 4, 10)  # Limit to 10 threads max for other DBs
    
    batch_size = max(20, count // max_threads)  # At least 20 receipts per batch
    
    print(f"Using {max_threads} threads with batch size of {batch_size}")
    
    # Create thread pool and submit tasks
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = []
        remaining_count = count
        thread_id = 0
        
        while remaining_count > 0:
            current_batch_size = min(batch_size, remaining_count)
            future = executor.submit(create_receipt_batch, market_ids, user_ids, current_batch_size, thread_id)
            futures.append(future)
            remaining_count -= current_batch_size
            thread_id += 1
        
        # Monitor progress
        completed = 0
        start_time = time.time()
        
        for future in as_completed(futures):
            try:
                future.result()  # This will raise any exceptions that occurred
                completed += 1
                
                with progress_lock:
                    elapsed = time.time() - start_time
                    receipts_per_second = stats.receipts_created / elapsed if elapsed > 0 else 0
                    print(f"Progress: {stats.receipts_created}/{count} receipts "
                          f"({stats.items_created} items) - "
                          f"{receipts_per_second:.1f} receipts/sec - "
                          f"Completed batches: {completed}/{len(futures)}")
            
            except Exception as e:
                print(f"Batch failed: {e}")
                raise
    
    total_time = time.time() - start_time
    print(f"\nCompleted in {total_time:.2f} seconds")
    print(f"Average speed: {stats.receipts_created / total_time:.1f} receipts/second")
    print(f"Created {stats.receipts_created} receipts with {stats.items_created} items")

def get_existing_users(session: Session) -> List[User]:
    """Get existing users from the database"""
    users = session.exec(select(User)).all()
    return list(users)

def main():
    """Main function to generate test data"""
    print("=== Receipt Tracker Test Data Generator (Multithreaded) ===")
    print("This script will generate test data for the Receipt Tracker application.")
    print("- 10 markets")
    print("- Configurable number of receipts (supports up to 1M+)")
    print("- Multiple items per receipt")
    print("- Uses multithreading for fast generation")
    print()
    
    # Get receipt count from user
    try:
        receipt_count = int(input("How many receipts to generate? (default: 500): ") or "500")
        if receipt_count <= 0:
            print("Invalid number. Using default: 500")
            receipt_count = 500
    except ValueError:
        print("Invalid input. Using default: 500")
        receipt_count = 500
    
    print(f"Will generate {receipt_count} receipts")
    
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
        
        # Generate receipts using parallel processing
        print(f"\nGenerating {receipt_count} receipts...")
        start_time = time.time()
        
        create_receipts_and_items_parallel(session, markets, existing_users, receipt_count)
        
        total_time = time.time() - start_time
        
        # Summary
        print("\n=== Generation Complete ===")
        print(f"Markets: {len(markets)}")
        print(f"Receipts: {stats.receipts_created}")
        print(f"Items: {stats.items_created}")
        print(f"Users: {len(existing_users)}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average speed: {stats.receipts_created / total_time:.1f} receipts/second")

if __name__ == "__main__":
    main() 