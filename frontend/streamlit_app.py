import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import yfinance as yf

# Use environment variable for Docker compatibility
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="AI-Powered Stock Screener", layout="wide", page_icon="📈")

# Initialize Session State
if "token" not in st.session_state:
    st.session_state["token"] = None
if "query_history" not in st.session_state:
    st.session_state["query_history"] = []

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
    st.session_state["query_history"] = []
    st.rerun()

# --- Custom Styling ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar Auth ---
with st.sidebar:
    st.title("🚀 Stock Screener AI")
    if st.session_state["token"] is None:
        st.header("Login")
        username = st.text_input("Username", value="testuser")
        password = st.text_input("Password", type="password", value="password123")
        if st.button("Login"):
            login(username, password)
    else:
        st.header("Account")
        st.write(f"Logged in as active user")
        if st.button("Logout"):
            logout()
        
        st.divider()
        st.header("Recent Queries")
        for q in st.session_state["query_history"][-5:]:
            st.caption(f"🔍 {q}")

if st.session_state["token"]:
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    
    tab1, tab2, tab3 = st.tabs(["🔍 AI Screener", "💼 Portfolio", "⚙️ Alerts"])
    
    with tab1:
        st.title("Natural Language Screener")
        st.info("Try: 'Technology stocks with PE < 40' or 'Healthcare companies'")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            query = st.text_input("Search with AI:", placeholder="Enter your financial query...")
        with col2:
            st.write("##") # Spacer
            search_btn = st.button("Analyze")

        if search_btn and query:
            # Save query to history
            if query not in st.session_state["query_history"]:
                st.session_state["query_history"].append(query)
            
            with st.spinner("🤖 AI is translating your query and searching database..."):
                try:
                    res = requests.post(f"{API_URL}/query/", json={"query": query}, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        results = data.get("results", [])
                        if results:
                            df = pd.DataFrame(results)
                            st.success(f"Found {len(results)} matches!")
                            
                            # Metrics Overview
                            m1, m2, m3 = st.columns(3)
                            m1.metric("Results", len(results))
                            m2.metric("Avg PE", round(df['pe_ratio'].mean(), 2) if 'pe_ratio' in df.columns else "N/A")
                            m3.metric("Top Sector", df['sector'].mode()[0] if 'sector' in df.columns else "N/A")

                            # Data Table
                            st.dataframe(df, width='stretch')
                            
                            # Visualizations
                            col_v1, col_v2 = st.columns(2)
                            with col_v1:
                                if 'pe_ratio' in df.columns and not df['pe_ratio'].isna().all():
                                    st.subheader("Valuation Overview (PE Ratio)")
                                    fig = px.bar(df, x='symbol', y='pe_ratio', color='sector', 
                                                title="PE Ratio Comparison", template="plotly_white")
                                    st.plotly_chart(fig, width='stretch')
                                else:
                                    st.info("Valuation data (PE Ratio) unavailable for these results.")
                            
                            with col_v2:
                                st.subheader("Sector Composition")
                                fig_s = px.pie(df, names='sector', hole=0.4, title="Results by Sector")
                                st.plotly_chart(fig_s, width='stretch')
                        else:
                            st.warning("No companies matched your criteria.")
                    else:
                        st.error(f"Backend Error: {res.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

    with tab2:
        st.title("💼 My Investment Portfolio")
        try:
            res = requests.get(f"{API_URL}/portfolio/", headers=headers)
            if res.status_code == 200:
                data = res.json()
                if data:
                    df_p = pd.DataFrame(data)
                    
                    # Portfolio Summary Cards
                    total_value = df_p['total_value'].sum()
                    total_pl = df_p['profit_loss'].sum()
                    avg_pl_pct = df_p['pl_percent'].mean()
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Market Value", f"${total_value:,.2f}")
                    m2.metric("Total Unrealized P/L", f"${total_pl:,.2f}", delta=f"{total_pl:,.2f}")
                    m3.metric("Avg Performance", f"{avg_pl_pct:.2f}%")

                    st.divider()

                    # Portfolio Performance Line Chart
                    st.subheader("Portfolio Value Trend (Last 30 Days)")
                    with st.spinner("Calculating historical performance..."):
                        try:
                            # Fetch 30d history for all symbols in portfolio
                            all_hist = []
                            for sym in df_p['symbol'].unique():
                                ticker = yf.Ticker(sym)
                                hist = ticker.history(period="1mo")['Close']
                                hist.name = sym
                                all_hist.append(hist)

                            if all_hist:
                                # Merge all historical data on date
                                hist_df = pd.concat(all_hist, axis=1).ffill()
                                # Calculate total value per day (Qty * Price)
                                # We need to map quantities to symbols
                                quantities = df_p.set_index('symbol')['quantity'].to_dict()
                                portfolio_trend = pd.Series(0, index=hist_df.index)
                                for sym in hist_df.columns:
                                    portfolio_trend += hist_df[sym] * quantities[sym]

                                trend_df = portfolio_trend.reset_index()
                                trend_df.columns = ['Date', 'Portfolio Value']

                                fig_line = px.line(trend_df, x='Date', y='Portfolio Value', 
                                                  title="Total Portfolio Value Over Time",
                                                  template="plotly_white")
                                st.plotly_chart(fig_line, width='stretch')
                        except Exception as e:
                            st.caption(f"Historical chart unavailable: {e}")

                    # Main Portfolio Dashboard

                    col_p1, col_p2 = st.columns([2, 1])
                    
                    with col_p1:
                        st.subheader("Holdings Details")
                        # Format the table for better display
                        display_df = df_p[['symbol', 'company_name', 'sector', 'quantity', 'purchase_price', 'current_price', 'total_value', 'pl_percent']]
                        st.dataframe(display_df.style.format({
                            'purchase_price': '${:.2f}',
                            'current_price': '${:.2f}',
                            'total_value': '${:.2f}',
                            'pl_percent': '{:.2f}%'
                        }), width='stretch')
                        
                        st.subheader("Profit/Loss by Asset")
                        fig_pl = px.bar(df_p, x='symbol', y='profit_loss', color='profit_loss',
                                       color_continuous_scale=['red', 'green'],
                                       title="Absolute P/L per Holding")
                        st.plotly_chart(fig_pl, width='stretch')

                    with col_p2:
                        st.subheader("Asset Allocation")
                        fig_alloc = px.pie(df_p, values='total_value', names='symbol', hole=0.5,
                                          title="Value Distribution")
                        st.plotly_chart(fig_alloc, width='stretch')
                        
                        st.subheader("Sector Diversification")
                        fig_sec = px.pie(df_p, values='total_value', names='sector',
                                        title="Exposure by Sector")
                        st.plotly_chart(fig_sec, width='stretch')

                    # Treemap for a bird's eye view
                    st.subheader("Portfolio Heatmap")
                    fig_tree = px.treemap(df_p, path=['sector', 'symbol'], values='total_value',
                                         color='pl_percent', color_continuous_scale='RdYlGn',
                                         title="Portfolio Composition & Performance")
                    st.plotly_chart(fig_tree, width='stretch')
                else:
                    st.info("Your portfolio is empty. Add your first stock below.")
        except Exception as e:
            st.error(f"Error loading portfolio: {e}")
            
        st.divider()
        with st.expander("➕ Add New Transaction"):
            c1, c2, c3 = st.columns(3)
            with c1: sym = st.text_input("Symbol")
            with c2: qty = st.number_input("Shares", min_value=1)
            with c3: price = st.number_input("Price Paid", min_value=0.0)
            if st.button("Add to Portfolio"):
                requests.post(f"{API_URL}/portfolio/", json={"symbol": sym, "quantity": qty, "purchase_price": price}, headers=headers)
                st.rerun()

    with tab3:
        st.header("Smart Alerts")
        col_a, col_b = st.columns([1, 2])
        
        with col_a:
            st.subheader("Create Alert")
            field = st.selectbox("Field", ["pe_ratio", "revenue_growth", "eps"])
            op = st.selectbox("Operator", ["<", ">", "<=", ">="])
            val = st.number_input("Threshold Value")
            if st.button("Set Alert"):
                requests.post(f"{API_URL}/alerts/", json={"field": field, "operator": op, "threshold": val}, headers=headers)
                st.success("Alert saved!")
                st.rerun()
        
        with col_b:
            st.subheader("Active Alerts")
            try:
                res = requests.get(f"{API_URL}/alerts/", headers=headers)
                if res.status_code == 200:
                    a_data = res.json()
                    if a_data:
                        st.table(pd.DataFrame(a_data))
                    else:
                        st.caption("No alerts set yet.")
            except:
                st.error("Failed to load alerts.")

else:
    st.title("AI-Powered Stock Screener")
    st.warning("🔒 Please login via the sidebar to start screening stocks with AI.")
    st.image("https://images.unsplash.com/photo-1611974717482-982c7c00eb8f?auto=format&fit=crop&q=80&w=1000", caption="Institutional-grade screening at your fingertips.")
