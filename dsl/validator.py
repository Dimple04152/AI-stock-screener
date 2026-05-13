from .schema import DSLQuery

ALLOWED_FIELDS = {"sector", "pe_ratio", "revenue", "symbol", "market_cap", "eps", "revenue_growth", "net_income"}
ALLOWED_OPERATORS = {"=", "<", ">", "<=", ">="}
ALLOWED_LOGIC = {"AND", "OR"}

def validate_dsl(dsl_dict: dict) -> DSLQuery:
    # First, validate basic structure using Pydantic
    try:
        query = DSLQuery(**dsl_dict)
    except Exception as e:
        raise ValueError(f"Invalid DSL structure: {e}")

    # Validate logic
    if query.logic.upper() not in ALLOWED_LOGIC:
        raise ValueError(f"Invalid logic: {query.logic}. Allowed: {ALLOWED_LOGIC}")

    # Validate filters
    for f in query.filters:
        if f.field not in ALLOWED_FIELDS:
            raise ValueError(f"Invalid field: {f.field}. Allowed: {ALLOWED_FIELDS}")
        if f.operator not in ALLOWED_OPERATORS:
            raise ValueError(f"Invalid operator: {f.operator}. Allowed: {ALLOWED_OPERATORS}")
    
    # Validate time filter if present
    if query.time_filter:
        if query.time_filter.type != "quarter":
            raise ValueError("Only 'quarter' time filter type is currently supported.")
        # Minimal validation for QX format e.g. 2024-Q2
        if not ("-Q" in query.time_filter.value and len(query.time_filter.value) == 7):
            raise ValueError(f"Invalid quarter format: {query.time_filter.value}. Expected YYYY-QX.")
    
    return query
