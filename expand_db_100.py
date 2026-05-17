import yfinance as yf
from database import SessionLocal
from models import Symbol, Fundamental, HistoricalMetric
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A broad list of ~100 popular global stocks across various sectors
EXPANDED_SYMBOLS = [
    # Technology
    {"symbol": "AAPL", "name": "Apple Inc", "sector": "Technology"},
    {"symbol": "MSFT", "name": "Microsoft Corp", "sector": "Technology"},
    {"symbol": "GOOGL", "name": "Alphabet Inc", "sector": "Technology"},
    {"symbol": "NVDA", "name": "NVIDIA Corp", "sector": "Technology"},
    {"symbol": "AVGO", "name": "Broadcom Inc", "sector": "Technology"},
    {"symbol": "ORCL", "name": "Oracle Corp", "sector": "Technology"},
    {"symbol": "ADBE", "name": "Adobe Inc", "sector": "Technology"},
    {"symbol": "CRM", "name": "Salesforce Inc", "sector": "Technology"},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "sector": "Technology"},
    {"symbol": "QCOM", "name": "Qualcomm Inc", "sector": "Technology"},
    {"symbol": "INTC", "name": "Intel Corp", "sector": "Technology"},
    {"symbol": "CSCO", "name": "Cisco Systems Inc", "sector": "Technology"},
    {"symbol": "IBM", "name": "IBM Corp", "sector": "Technology"},
    {"symbol": "AMAT", "name": "Applied Materials Inc", "sector": "Technology"},
    
    # Communication Services
    {"symbol": "META", "name": "Meta Platforms Inc", "sector": "Communication Services"},
    {"symbol": "NFLX", "name": "Netflix Inc", "sector": "Communication Services"},
    {"symbol": "DIS", "name": "Walt Disney Co", "sector": "Communication Services"},
    {"symbol": "TMUS", "name": "T-Mobile US Inc", "sector": "Communication Services"},
    {"symbol": "VZ", "name": "Verizon Communications", "sector": "Communication Services"},
    {"symbol": "T", "name": "AT&T Inc", "sector": "Communication Services"},
    {"symbol": "CMCSA", "name": "Comcast Corp", "sector": "Communication Services"},
    
    # Consumer Cyclical
    {"symbol": "AMZN", "name": "Amazon.com Inc", "sector": "Consumer Cyclical"},
    {"symbol": "TSLA", "name": "Tesla Inc", "sector": "Consumer Cyclical"},
    {"symbol": "HD", "name": "Home Depot Inc", "sector": "Consumer Cyclical"},
    {"symbol": "MCD", "name": "McDonald's Corp", "sector": "Consumer Cyclical"},
    {"symbol": "NKE", "name": "NIKE Inc", "sector": "Consumer Cyclical"},
    {"symbol": "SBUX", "name": "Starbucks Corp", "sector": "Consumer Cyclical"},
    {"symbol": "LOW", "name": "Lowe's Companies Inc", "sector": "Consumer Cyclical"},
    {"symbol": "BKNG", "name": "Booking Holdings Inc", "sector": "Consumer Cyclical"},
    {"symbol": "TJX", "name": "TJX Companies Inc", "sector": "Consumer Cyclical"},
    {"symbol": "ABNB", "name": "Airbnb Inc", "sector": "Consumer Cyclical"},
    
    # Financial Services
    {"symbol": "JPM", "name": "JPMorgan Chase & Co", "sector": "Financial Services"},
    {"symbol": "V", "name": "Visa Inc", "sector": "Financial Services"},
    {"symbol": "MA", "name": "Mastercard Inc", "sector": "Financial Services"},
    {"symbol": "BAC", "name": "Bank of America Corp", "sector": "Financial Services"},
    {"symbol": "WFC", "name": "Wells Fargo & Co", "sector": "Financial Services"},
    {"symbol": "GS", "name": "Goldman Sachs Group", "sector": "Financial Services"},
    {"symbol": "MS", "name": "Morgan Stanley", "sector": "Financial Services"},
    {"symbol": "AXP", "name": "American Express Co", "sector": "Financial Services"},
    {"symbol": "PYPL", "name": "PayPal Holdings Inc", "sector": "Financial Services"},
    {"symbol": "BLK", "name": "BlackRock Inc", "sector": "Financial Services"},
    {"symbol": "C", "name": "Citigroup Inc", "sector": "Financial Services"},
    {"symbol": "BRK-B", "name": "Berkshire Hathaway Inc", "sector": "Financial Services"},
    
    # Healthcare
    {"symbol": "LLY", "name": "Eli Lilly and Co", "sector": "Healthcare"},
    {"symbol": "UNH", "name": "UnitedHealth Group Inc", "sector": "Healthcare"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
    {"symbol": "ABBV", "name": "AbbVie Inc", "sector": "Healthcare"},
    {"symbol": "MRK", "name": "Merck & Co Inc", "sector": "Healthcare"},
    {"symbol": "TMO", "name": "Thermo Fisher Scientific", "sector": "Healthcare"},
    {"symbol": "ABT", "name": "Abbott Laboratories", "sector": "Healthcare"},
    {"symbol": "DHR", "name": "Danaher Corp", "sector": "Healthcare"},
    {"symbol": "PFE", "name": "Pfizer Inc", "sector": "Healthcare"},
    {"symbol": "AMGN", "name": "Amgen Inc", "sector": "Healthcare"},
    {"symbol": "ISRG", "name": "Intuitive Surgical Inc", "sector": "Healthcare"},
    {"symbol": "SYK", "name": "Stryker Corp", "sector": "Healthcare"},
    {"symbol": "BMY", "name": "Bristol-Myers Squibb", "sector": "Healthcare"},
    {"symbol": "GILD", "name": "Gilead Sciences Inc", "sector": "Healthcare"},
    
    # Consumer Defensive
    {"symbol": "WMT", "name": "Walmart Inc", "sector": "Consumer Defensive"},
    {"symbol": "PG", "name": "Procter & Gamble Co", "sector": "Consumer Defensive"},
    {"symbol": "KO", "name": "Coca-Cola Co", "sector": "Consumer Defensive"},
    {"symbol": "PEP", "name": "PepsiCo Inc", "sector": "Consumer Defensive"},
    {"symbol": "COST", "name": "Costco Wholesale Corp", "sector": "Consumer Defensive"},
    {"symbol": "PM", "name": "Philip Morris International", "sector": "Consumer Defensive"},
    {"symbol": "MDLZ", "name": "Mondelez International", "sector": "Consumer Defensive"},
    {"symbol": "TGT", "name": "Target Corp", "sector": "Consumer Defensive"},
    {"symbol": "EL", "name": "Estee Lauder Companies", "sector": "Consumer Defensive"},
    
    # Energy
    {"symbol": "XOM", "name": "Exxon Mobil Corp", "sector": "Energy"},
    {"symbol": "CVX", "name": "Chevron Corp", "sector": "Energy"},
    {"symbol": "COP", "name": "ConocoPhillips", "sector": "Energy"},
    {"symbol": "SLB", "name": "Schlumberger Ltd", "sector": "Energy"},
    {"symbol": "EOG", "name": "EOG Resources Inc", "sector": "Energy"},
    {"symbol": "MPC", "name": "Marathon Petroleum", "sector": "Energy"},
    {"symbol": "PSX", "name": "Phillips 66", "sector": "Energy"},
    
    # Industrials
    {"symbol": "CAT", "name": "Caterpillar Inc", "sector": "Industrials"},
    {"symbol": "GE", "name": "General Electric Co", "sector": "Industrials"},
    {"symbol": "UNP", "name": "Union Pacific Corp", "sector": "Industrials"},
    {"symbol": "HON", "name": "Honeywell International", "sector": "Industrials"},
    {"symbol": "RTX", "name": "Raytheon Technologies", "sector": "Industrials"},
    {"symbol": "LMT", "name": "Lockheed Martin Corp", "sector": "Industrials"},
    {"symbol": "UPS", "name": "United Parcel Service", "sector": "Industrials"},
    {"symbol": "DE", "name": "Deere & Co", "sector": "Industrials"},
    {"symbol": "BA", "name": "Boeing Co", "sector": "Industrials"},
    {"symbol": "MMM", "name": "3M Co", "sector": "Industrials"},
    
    # Utilities & Basic Materials
    {"symbol": "NEE", "name": "NextEra Energy Inc", "sector": "Utilities"},
    {"symbol": "DUK", "name": "Duke Energy Corp", "sector": "Utilities"},
    {"symbol": "SO", "name": "Southern Co", "sector": "Utilities"},
    {"symbol": "LIN", "name": "Linde plc", "sector": "Basic Materials"},
    {"symbol": "APD", "name": "Air Products & Chemicals", "sector": "Basic Materials"},
    {"symbol": "FCX", "name": "Freeport-McMoRan Inc", "sector": "Basic Materials"},
    {"symbol": "SHW", "name": "Sherwin-Williams Co", "sector": "Basic Materials"},
    
    # Real Estate
    {"symbol": "PLD", "name": "Prologis Inc", "sector": "Real Estate"},
    {"symbol": "AMT", "name": "American Tower Corp", "sector": "Real Estate"},
    {"symbol": "EQIX", "name": "Equinix Inc", "sector": "Real Estate"},
    {"symbol": "CCI", "name": "Crown Castle Inc", "sector": "Real Estate"},
]

def expand_and_sync():
    db = SessionLocal()
    try:
        logger.info(f"Targeting {len(EXPANDED_SYMBOLS)} symbols.")
        for item in EXPANDED_SYMBOLS:
            # 1. Ensure Symbol exists
            symbol_obj = db.query(Symbol).filter(Symbol.symbol == item["symbol"]).first()
            if not symbol_obj:
                logger.info(f"Adding new symbol: {item['symbol']}")
                symbol_obj = Symbol(symbol=item["symbol"], company_name=item["name"], sector=item["sector"])
                db.add(symbol_obj)
                db.flush()
            
            # 2. Sync from yfinance (with error handling and minor delay to avoid rate limits)
            try:
                ticker = yf.Ticker(item["symbol"])
                info = ticker.info
                
                fundamental = db.query(Fundamental).filter(Fundamental.company_id == symbol_obj.id).first()
                if not fundamental:
                    fundamental = Fundamental(company_id=symbol_obj.id)
                    db.add(fundamental)
                
                fundamental.pe_ratio = info.get('trailingPE') or info.get('forwardPE')
                fundamental.eps = info.get('trailingEps')
                fundamental.market_cap = info.get('marketCap')
                fundamental.revenue_growth = info.get('revenueGrowth')
                
                logger.info(f"✅ {item['symbol']} data updated.")
                time.sleep(0.1) # Small delay
                
            except Exception as e:
                logger.error(f"❌ Error syncing {item['symbol']}: {e}")
                
        db.commit()
        logger.info("Database successfully expanded to 100+ companies.")
    finally:
        db.close()

if __name__ == "__main__":
    expand_and_sync()
