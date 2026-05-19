from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from parser import parse_query_to_dsl
from dsl.validator import validate_dsl

app = FastAPI(title="LLM Query Microservice")

class QueryRequest(BaseModel):
    query: str

@app.post("/parse")
def parse_query(request: QueryRequest):
    try:
        dsl_dict = parse_query_to_dsl(request.query)
        # We can validate it here or just return the dict and let the main backend validate it.
        # Validating here ensures the microservice returns a valid DSL.
        dsl = validate_dsl(dsl_dict)
        return dsl.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}
