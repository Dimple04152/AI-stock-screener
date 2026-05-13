from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import hashlib

from database import get_db
from auth_dependency import get_current_user
from models import User
from llm.parser import parse_query_to_dsl
from dsl.validator import validate_dsl
from execution.query_executor import execute_query
from cache import get_cache, set_cache

router = APIRouter(prefix="/query", tags=["query"])

class QueryRequest(BaseModel):
    query: str

@router.post("/")
def run_query(request: QueryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Simple cache key generation
    query_hash = hashlib.md5(request.query.encode()).hexdigest()
    cache_key = f"query_{query_hash}"
    
    cached_result = get_cache(cache_key)
    if cached_result:
        return cached_result
        
    try:
        # 1. Parse natural language to DSL
        dsl_dict = parse_query_to_dsl(request.query)
        
        # 2. Validate DSL
        dsl = validate_dsl(dsl_dict)
        
        # 3. Compile and Execute
        result = execute_query(db, dsl)
        
        # Cache the result
        set_cache(cache_key, result, ttl=300)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
