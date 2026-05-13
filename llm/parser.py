import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key and api_key != "your_gemini_api_key_here":
    genai.configure(api_key=api_key)

def parse_query_to_dsl(query: str) -> dict:
    prompt = f"""
    You are a financial query parser. Convert the following natural language query into a structured DSL JSON format.
    Return ONLY valid JSON. Do not return markdown wrapping or any explanations.

    Allowed fields: sector, pe_ratio, revenue, symbol, market_cap, eps, revenue_growth, net_income
    Allowed operators: =, <, >, <=, >=
    Logic must be "AND" or "OR".

    DSL Structure:
    {{
      "filters": [
        {{
          "field": "...",
          "operator": "...",
          "value": ...
        }}
      ],
      "logic": "AND",
      "time_filter": {{
        "type": "quarter",
        "value": "YYYY-QX"
      }} // Optional. Only include if time is explicitly mentioned.
    }}

    Query: {query}
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
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
