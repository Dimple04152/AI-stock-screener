import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
from dsl.validator import ALLOWED_FIELDS

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def parse_query_to_dsl(query: str) -> dict:
    prompt = f"""
    You are a financial query parser. Convert the following natural language query into a structured DSL JSON format.
    
    ### Guidelines:
    1. Return ONLY valid JSON.
    2. Do not include markdown code blocks (e.g., ```json).
    3. Do not include any explanations or extra text.
    4. Allowed fields: {', '.join(ALLOWED_FIELDS)}
    5. Allowed operators: =, <, >, <=, >=
    6. Logic must be "AND" or "OR".
    7. For time-based queries, use "time_filter".
    
    ### DSL Schema:
    {{
      "filters": [
        {{
          "field": "string",
          "operator": "string",
          "value": number or string
        }}
      ],
      "logic": "AND" | "OR",
      "time_filter": {{
        "type": "quarter",
        "value": "YYYY-QX"
      }} // Optional.
    }}

    ### Examples:
    - "Tech stocks with PE < 20": 
      {{"filters": [{{"field": "sector", "operator": "=", "value": "Technology"}}, {{"field": "pe_ratio", "operator": "<", "value": 20}}], "logic": "AND"}}
    
    - "Companies with net income > 5B in 2024-Q1":
      {{"filters": [{{"field": "net_income", "operator": ">", "value": 5000000000}}], "logic": "AND", "time_filter": {{"type": "quarter", "value": "2024-Q1"}}}}

    Query: {query}
    """
    
    try:
        model = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(prompt)
    except Exception as e:
        raise RuntimeError(f"Error communicating with Gemini API: {e}")
    
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:-3].strip()
    elif text.startswith("```"):
        text = text[3:-3].strip()
        
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM output as JSON. Output: {text}") from e
