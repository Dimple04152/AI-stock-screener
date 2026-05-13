from database import SessionLocal, engine, Base
from models import User, Symbol, Fundamental, HistoricalMetric
from auth_utils import get_password_hash

def seed_db():
    print("Dropping and recreating tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    print("Seeding users...")
    user1 = User(username="testuser", hashed_password=get_password_hash("password123"))
    db.add(user1)
    
    print("Seeding symbols...")
    aapl = Symbol(symbol="AAPL", company_name="Apple Inc", sector="Technology")
    msft = Symbol(symbol="MSFT", company_name="Microsoft Corp", sector="Technology")
    jnj = Symbol(symbol="JNJ", company_name="Johnson & Johnson", sector="Healthcare")
    
    db.add_all([aapl, msft, jnj])
    db.commit()
    
    print("Seeding fundamentals...")
    db.add(Fundamental(company_id=aapl.id, pe_ratio=28.5, eps=6.1, market_cap=2.8e12, revenue_growth=5.2))
    db.add(Fundamental(company_id=msft.id, pe_ratio=35.2, eps=9.6, market_cap=3.0e12, revenue_growth=15.0))
    db.add(Fundamental(company_id=jnj.id, pe_ratio=15.0, eps=10.5, market_cap=4.0e11, revenue_growth=2.1))
    
    print("Seeding historical metrics...")
    db.add(HistoricalMetric(company_id=aapl.id, quarter="2024-Q1", revenue=119.58e9, net_income=33.92e9))
    db.add(HistoricalMetric(company_id=msft.id, quarter="2024-Q1", revenue=61.86e9, net_income=21.94e9))
    db.add(HistoricalMetric(company_id=jnj.id, quarter="2024-Q1", revenue=21.38e9, net_income=5.35e9))
    
    db.commit()
    print("Database seeded successfully!")
    db.close()

if __name__ == "__main__":
    seed_db()
