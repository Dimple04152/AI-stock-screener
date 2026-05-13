import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8001"

st.set_page_config(page_title="AI-Powered Stock Screener", layout="wide")

if "token" not in st.session_state:
    st.session_state["token"] = None

def login(username, password):
    res = requests.post(f"{API_URL}/auth/login", data={"username": username, "password": password})
    if res.status_code == 200:
        st.session_state["token"] = res.json().get("access_token")
        st.success("Logged in successfully!")
        st.rerun()
    else:
        st.error("Invalid credentials")

def logout():
    st.session_state["token"] = None
    st.rerun()

# --- Sidebar Auth ---
with st.sidebar:
    if st.session_state["token"] is None:
        st.header("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            login(username, password)
        st.write("Or use 'testuser' / 'password123'")
    else:
        st.header("Welcome!")
        if st.button("Logout"):
            logout()

if st.session_state["token"]:
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    
    tab1, tab2, tab3, tab4 = st.tabs(["AI Screener", "Portfolio", "Alerts", "Companies"])
    
    with tab1:
        st.header("AI Stock Screener")
        st.markdown("Ask anything like: *Technology companies with PE ratio less than 30*")
        query = st.text_input("Enter your natural language query:")
        if st.button("Search"):
            with st.spinner("Analyzing and fetching data..."):
                try:
                    res = requests.post(f"{API_URL}/query/", json={"query": query}, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        results = data.get("results", [])
                        if results:
                            df = pd.DataFrame(results)
                            st.dataframe(df)
                        else:
                            st.info(data.get("message", "No results found."))
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    with tab2:
        st.header("Your Portfolio")
        try:
            res = requests.get(f"{API_URL}/portfolio/", headers=headers)
            if res.status_code == 200:
                data = res.json()
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                else:
                    st.info("Your portfolio is empty.")
        except:
            pass
            
        with st.expander("Add to Portfolio"):
            sym = st.text_input("Symbol (e.g. AAPL)")
            qty = st.number_input("Quantity", min_value=1, step=1)
            price = st.number_input("Purchase Price", min_value=0.0)
            if st.button("Add"):
                requests.post(f"{API_URL}/portfolio/", json={"symbol": sym, "quantity": qty, "purchase_price": price}, headers=headers)
                st.rerun()

    with tab3:
        st.header("Alerts")
        try:
            res = requests.get(f"{API_URL}/alerts/", headers=headers)
            if res.status_code == 200:
                data = res.json()
                if data:
                    st.dataframe(pd.DataFrame(data))
                else:
                    st.info("No alerts configured.")
        except:
            pass
            
        with st.expander("Create Alert"):
            field = st.selectbox("Field", ["pe_ratio", "revenue_growth", "eps"])
            op = st.selectbox("Operator", ["<", ">", "<=", ">=", "="])
            val = st.number_input("Threshold", value=0.0)
            if st.button("Create"):
                requests.post(f"{API_URL}/alerts/", json={"field": field, "operator": op, "threshold": val}, headers=headers)
                st.rerun()

    with tab4:
        st.header("Company Explorer")
        try:
            res = requests.get(f"{API_URL}/companies/", headers=headers)
            if res.status_code == 200:
                st.dataframe(pd.DataFrame(res.json()))
        except:
            pass
else:
    st.info("Please log in to access the AI Screener.")
