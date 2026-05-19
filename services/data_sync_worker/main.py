import time
import yfinance as yf
import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func

# Minimal DB setup for the worker
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myuser:mypassword@localhost:5433/stock_screener")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redefining models here for independence (or we could copy models.py)
class Symbol(Base):
    __tablename__ = "symbols"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    company_name = Column(String)
    sector = Column(String)

class Fundamental(Base):
    __tablename__ = "fundamentals"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("symbols.id"))
    pe_ratio = Column(Float)
    eps = Column(Float)
    market_cap = Column(Float)
    revenue_growth = Column(Float)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class HistoricalMetric(Base):
    __tablename__ = "historical_metrics"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("symbols.id"))
    quarter = Column(String) # e.g., "2023-Q4"
    revenue = Column(Float)
    net_income = Column(Float)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "3600")) # Default 1 hour

def sync_data():
    db = SessionLocal()
    try:
        symbols = db.query(Symbol).all()
        logger.info(f"Found {len(symbols)} symbols to update.")
        
        for symbol_obj in symbols:
            logger.info(f"Fetching data for {symbol_obj.symbol}...")
            try:
                ticker = yf.Ticker(symbol_obj.symbol)
                
                # 1. Update Fundamentals
                info = ticker.info
                fundamental = db.query(Fundamental).filter(Fundamental.company_id == symbol_obj.id).first()
                if not fundamental:
                    fundamental = Fundamental(company_id=symbol_obj.id)
                    db.add(fundamental)
                
                fundamental.pe_ratio = info.get('trailingPE') or info.get('forwardPE')
                fundamental.eps = info.get('trailingEps')
                fundamental.market_cap = info.get('marketCap')
                fundamental.revenue_growth = info.get('revenueGrowth')
                
                # 2. Update Historical Metrics (Quarterly)
                income_stmt = ticker.quarterly_income_stmt
                if income_stmt is not None and not income_stmt.empty:
                    for date in income_stmt.columns[:4]:
                        year = date.year
                        month = date.month
                        quarter = (month - 1) // 3 + 1
                        q_str = f"{year}-Q{quarter}"
                        
                        metric = db.query(HistoricalMetric).filter(
                            HistoricalMetric.company_id == symbol_obj.id,
                            HistoricalMetric.quarter == q_str
                        ).first()
                        
                        if not metric:
                            metric = HistoricalMetric(company_id=symbol_obj.id, quarter=q_str)
                            db.add(metric)
                        
                        metric.revenue = float(income_stmt.loc['Total Revenue', date]) if 'Total Revenue' in income_stmt.index else None
                        metric.net_income = float(income_stmt.loc['Net Income', date]) if 'Net Income' in income_stmt.index else None
                
                logger.info(f"Updated {symbol_obj.symbol} fundamentals and history.")
                
            except Exception as e:
                logger.error(f"Error updating {symbol_obj.symbol}: {e}")
                db.rollback()
                
        db.commit()
        logger.info("Synchronization complete.")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting Data Sync Worker...")
    while True:
        try:
            sync_data()
        except Exception as e:
            logger.error(f"Sync loop error: {e}")
        
        logger.info(f"Sleeping for {SYNC_INTERVAL} seconds...")
        time.sleep(SYNC_INTERVAL)
