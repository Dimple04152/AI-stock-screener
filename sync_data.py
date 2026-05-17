import yfinance as yf
from database import SessionLocal
from models import Symbol, Fundamental, HistoricalMetric
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                    # Get the most recent quarters (e.g., last 4)
                    for date in income_stmt.columns[:4]:
                        # Format date as YYYY-QX
                        year = date.year
                        month = date.month
                        quarter = (month - 1) // 3 + 1
                        q_str = f"{year}-Q{quarter}"
                        
                        # Check if record exists
                        metric = db.query(HistoricalMetric).filter(
                            HistoricalMetric.company_id == symbol_obj.id,
                            HistoricalMetric.quarter == q_str
                        ).first()
                        
                        if not metric:
                            metric = HistoricalMetric(company_id=symbol_obj.id, quarter=q_str)
                            db.add(metric)
                        
                        # Extract revenue and net income
                        # Note: yfinance field names can vary, using common ones
                        metric.revenue = float(income_stmt.loc['Total Revenue', date]) if 'Total Revenue' in income_stmt.index else None
                        metric.net_income = float(income_stmt.loc['Net Income', date]) if 'Net Income' in income_stmt.index else None
                
                logger.info(f"Updated {symbol_obj.symbol} fundamentals and history.")
                
            except Exception as e:
                logger.error(f"Error updating {symbol_obj.symbol}: {e}")
                
        db.commit()
        logger.info("Synchronization complete.")
    finally:
        db.close()

if __name__ == "__main__":
    sync_data()
