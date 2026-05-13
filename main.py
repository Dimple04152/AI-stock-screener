from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from backend.routes import auth, query, portfolio, alerts, companies

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-Powered Stock Screener API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(query.router)
app.include_router(portfolio.router)
app.include_router(alerts.router)
app.include_router(companies.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI-Powered Stock Screener API"}
