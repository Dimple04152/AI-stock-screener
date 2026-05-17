import yfinance as yf
from database import SessionLocal
from models import Symbol, Fundamental, HistoricalMetric
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A larger list of popular stocks across different sectors
EXPANDED_SYMBOLS = [
    {"symbol": "AAPL", "name": "Apple Inc", "sector": "Technology"},
    {"symbol": "MSFT", "name": "Microsoft Corp", "sector": "Technology"},
    {"symbol": "GOOGL", "name": "Alphabet Inc", "sector": "Technology"},
    {"symbol": "AMZN", "name": "Amazon.com Inc", "sector": "Consumer Cyclical"},
    {"symbol": "TSLA", "name": "Tesla Inc", "sector": "Consumer Cyclical"},
    {"symbol": "NVDA", "name": "NVIDIA Corp", "sector": "Technology"},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co", "sector": "Financial Services"},
    {"symbol": "V", "name": "Visa Inc", "sector": "Financial Services"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
    {"symbol": "UNH", "name": "UnitedHealth Group Inc", "sector": "Healthcare"},
    {"symbol": "WMT", "name": "Walmart Inc", "sector": "Consumer Defensive"},
    {"symbol": "PG", "name": "Procter & Gamble Co", "sector": "Consumer Defensive"},
    {"symbol": "XOM", "name": "Exxon Mobil Corp", "sector": "Energy"},
    {"symbol": "CVX", "name": "Chevron Corp", "sector": "Energy"},
    {"symbol": "LLY", "name": "Eli Lilly and Co", "sector": "Healthcare"},
    {"symbol": "MA", "name": "Mastercard Inc", "sector": "Financial Services"},
    {"symbol": "HD", "name": "Home Depot Inc", "sector": "Consumer Cyclical"},
    {"symbol": "ABBV", "name": "AbbVie Inc", "sector": "Healthcare"},
    {"symbol": "KO", "name": "Coca-Cola Co", "sector": "Consumer Defensive"},
    {"symbol": "PEP", "name": "PepsiCo Inc", "sector": "Consumer Defensive"}
]

def expand_and_sync():
    db = SessionLocal()
    try:
        for item in EXPANDED_SYMBOLS:
            # 1. Ensure Symbol exists
            symbol_obj = db.query(Symbol).filter(Symbol.symbol == item["symbol"]).first()
            if not symbol_obj:
                logger.info(f"Adding new symbol: {item['symbol']}")
                symbol_obj = Symbol(symbol=item["symbol"], company_name=item["name"], sector=item["sector"])
                db.add(symbol_obj)
                db.flush() # Get ID
            
            # 2. Fetch and Sync from yfinance
            logger.info(f"Syncing data for {item['symbol']}...")
            try:
                ticker = yf.Ticker(item["symbol"])
                info = ticker.info
                
                # Update Fundamental
                fundamental = db.query(Fundamental).filter(Fundamental.company_id == symbol_obj.id).first()
                if not fundamental:
                    fundamental = Fundamental(company_id=symbol_obj.id)
                    db.add(fundamental)
                
                fundamental.pe_ratio = info.get('trailingPE') or info.get('forwardPE')
                fundamental.eps = info.get('trailingEps')
                fundamental.market_cap = info.get('marketCap')
                fundamental.revenue_growth = info.get('revenueGrowth')
                
                # Update Historical Metrics
                income_stmt = ticker.quarterly_income_stmt
                if income_stmt is not None and not income_stmt.empty:
                    for date in income_stmt.columns[:2]: # Just last 2 quarters for speed
                        year, month = date.year, date.month
                        q_str = f"{year}-Q{(month - 1) // 3 + 1}"
                        
                        metric = db.query(HistoricalMetric).filter(
                            HistoricalMetric.company_id == symbol_obj.id, 
                            HistoricalMetric.quarter == q_str
                        ).first()
                        
                        if not metric:
                            metric = HistoricalMetric(company_id=symbol_obj.id, quarter=q_str)
                            db.add(metric)
                        
                        metric.revenue = float(income_stmt.loc['Total Revenue', date]) if 'Total Revenue' in income_stmt.index else None
                        metric.net_income = float(income_stmt.loc['Net Income', date]) if 'Net Income' in income_stmt.index else None
                
                logger.info(f"✅ {item['symbol']} synced.")
            except Exception as e:
                logger.error(f"❌ Failed to sync {item['symbol']}: {e}")
        
        db.commit()
        logger.info("Database expanded and synchronized successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    expand_and_sync()
