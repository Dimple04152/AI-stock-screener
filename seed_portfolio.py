from database import SessionLocal
from models import User, Symbol, PortfolioItem
import random

def seed_portfolio():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == 'testuser').first()
        if not user:
            print("User 'testuser' not found. Run seed.py first.")
            return

        # Clear existing portfolio to start fresh with 20 items
        db.query(PortfolioItem).filter(PortfolioItem.user_id == user.id).delete()

        symbols = db.query(Symbol).all()
        if len(symbols) < 20:
            print(f"Only {len(symbols)} symbols found. Run expand_db_100.py first.")
            return

        selected_symbols = random.sample(symbols, 20)
        
        for sym in selected_symbols:
            # Random quantity and purchase price (roughly around current market ranges)
            qty = random.randint(5, 50)
            # Fetch a rough current price to make purchase price realistic (some profit, some loss)
            base_price = 100.0 # fallback
            
            # Simple logic: purchase price is +/- 15% of a random base
            purchase_price = round(random.uniform(50, 300), 2)
            
            item = PortfolioItem(
                user_id=user.id,
                company_id=sym.id,
                quantity=qty,
                purchase_price=purchase_price
            )
            db.add(item)
            print(f"Added {qty} shares of {sym.symbol} at ${purchase_price}")
        
        db.commit()
        print("\n✅ Successfully added 20 companies to the investment portfolio!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_portfolio()
