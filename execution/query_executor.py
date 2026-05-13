from sqlalchemy.orm import Session
from sqlalchemy import text
from sql_compiler import compile_dsl_to_sql
from dsl.schema import DSLQuery
import logging

logger = logging.getLogger(__name__)

def execute_query(db: Session, dsl: DSLQuery):
    try:
        sql, params = compile_dsl_to_sql(dsl)
        logger.info(f"Executing SQL: {sql} with params {params}")
        
        result = db.execute(text(sql), params)
        rows = result.mappings().all()
        
        if not rows:
            return {"results": [], "message": "No results found"}
            
        return {"results": [dict(row) for row in rows]}
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise RuntimeError("Database execution failed") from e
