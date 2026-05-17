from dsl.schema import DSLQuery

FIELD_MAPPING = {
    "symbol": ("symbols", "s.symbol"),
    "sector": ("symbols", "s.sector"),
    "company_name": ("symbols", "s.company_name"),
    "pe_ratio": ("fundamentals", "f.pe_ratio"),
    "eps": ("fundamentals", "f.eps"),
    "market_cap": ("fundamentals", "f.market_cap"),
    "revenue_growth": ("fundamentals", "f.revenue_growth"),
    "revenue": ("historical_metrics", "h.revenue"),
    "net_income": ("historical_metrics", "h.net_income")
}

def compile_dsl_to_sql(dsl: DSLQuery) -> tuple[str, list]:
    # We select fields that exist across tables we might join
    base_query = "SELECT DISTINCT s.id, s.symbol, s.company_name, s.sector, f.pe_ratio, f.eps, f.market_cap, f.revenue_growth"
    
    joins = set()
    joins.add("LEFT JOIN fundamentals f ON s.id = f.company_id") # Always join for results
    where_clauses = []
    params = []

    # If any fields come from fundamentals or historical_metrics, we add them to SELECT maybe?
    # For simplicity, returning just basic symbol info from the query.
    
    for f in dsl.filters:
        table, column = FIELD_MAPPING.get(f.field, (None, None))
        if not table:
            continue
        
        if table == "fundamentals":
            joins.add("LEFT JOIN fundamentals f ON s.id = f.company_id")
        elif table == "historical_metrics":
            joins.add("LEFT JOIN historical_metrics h ON s.id = h.company_id")
            
        # Add to where clause
        where_clauses.append(f"{column} {f.operator} :p_{len(params)}")
        params.append(f.value)

    if dsl.time_filter and dsl.time_filter.type == "quarter":
        joins.add("LEFT JOIN historical_metrics h ON s.id = h.company_id")
        where_clauses.append(f"h.quarter = :p_{len(params)}")
        params.append(dsl.time_filter.value)
        
    # Construct query string
    join_str = " ".join(joins)
    where_str = ""
    if where_clauses:
        logic_op = f" {dsl.logic} "
        where_str = "WHERE " + logic_op.join(where_clauses)
        
    final_sql = f"{base_query} FROM symbols s {join_str} {where_str}"
    
    # We will use SQLAlchemy text(), so we bind parameters as dictionary
    param_dict = {f"p_{i}": val for i, val in enumerate(params)}
    
    return final_sql, param_dict
