"""
Personal Finance Portfolio Tracker
Main entry point with multi-page navigation
"""

import streamlit as st
import json
import os
from datetime import datetime
import yfinance as yf
from datetime import timedelta

# Import page modules
from pages import overview, holdings, performance, transactions, news

# Page configuration
st.set_page_config(
    page_title="Personal Finance Portfolio Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# File to store portfolio data
DATA_FILE = "portfolio_data.json"

# Initialize session state
if 'portfolio' not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            st.session_state.portfolio = json.load(f)
    else:
        st.session_state.portfolio = []

# Initialize current page if not set
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Overview'


# Utility Functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_live_price(ticker):
    """Fetch live price for a ticker symbol"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period='1d')
        if not data.empty:
            return data['Close'].iloc[-1]
        return None
    except:
        return None


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_historical_price(ticker, date):
    """Fetch historical price for a ticker on a specific date"""
    try:
        # Add buffer days to ensure we get data
        start_date = (date - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = (date + timedelta(days=1)).strftime('%Y-%m-%d')

        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date)

        if not data.empty:
            # Get the closest date
            closest_date = min(data.index, key=lambda x: abs(x.date() - date))
            return data.loc[closest_date, 'Close']
        return None
    except Exception as e:
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_forex_rate(from_currency='USD', to_currency='AUD'):
    """Get forex conversion rate"""
    try:
        if from_currency == to_currency:
            return 1.0

        # Use forex pair
        ticker = f"{from_currency}{to_currency}=X"
        forex = yf.Ticker(ticker)
        data = forex.history(period='1d')

        if not data.empty:
            return data['Close'].iloc[-1]
        return 1.52  # Fallback approximate USD to AUD rate
    except:
        return 1.52  # Fallback approximate USD to AUD rate


def save_data():
    """Save portfolio data to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(st.session_state.portfolio, f, indent=2)


def add_transaction(asset_name, asset_type, quantity, price, date, transaction_type, ticker=None):
    """Add a new transaction to the portfolio"""
    transaction = {
        'asset_name': asset_name,
        'asset_type': asset_type,
        'quantity': quantity,
        'price': price,
        'date': date.strftime('%Y-%m-%d'),
        'transaction_type': transaction_type,
        'total_value': quantity * price,
        'ticker': ticker if ticker else asset_name
    }
    st.session_state.portfolio.append(transaction)
    save_data()


# Sidebar - Add Transaction Form
with st.sidebar:
    st.title("💰 Portfolio Tracker")
    st.markdown("### All values in AUD 🇦🇺")

    # Get forex rate for display
    usd_to_aud = get_forex_rate('USD', 'AUD')
    st.info(f"USD/AUD: ${usd_to_aud:.4f}")

    st.markdown("---")

    st.header("Add Transaction")

    asset_type = st.selectbox("Asset Type", ["Stocks", "Crypto", "Cash", "Bonds", "Real Estate", "Other"])

    # Show ticker input for stocks and crypto
    if asset_type in ["Stocks", "Crypto"]:
        ticker = st.text_input("Ticker Symbol", placeholder="e.g., AAPL, BTC-USD, CBA.AX")
        asset_name = st.text_input("Display Name (optional)", placeholder="Leave empty to use ticker")
        if not asset_name:
            asset_name = ticker
    else:
        asset_name = st.text_input("Asset Name", placeholder="e.g., Property, Cash, Gold")
        ticker = asset_name

    transaction_type = st.radio("Transaction Type", ["Buy", "Sell"])

    # Date selection
    date = st.date_input("Date", value=datetime.now())

    # Auto-fetch price button for stocks/crypto
    price = 0.0
    if asset_type in ["Stocks", "Crypto"] and ticker:
        col1, col2 = st.columns([2, 1])
        with col1:
            price = st.number_input("Price per Unit (AUD)", min_value=0.0, step=0.01, format="%.2f", value=price)
        with col2:
            if st.button("📊 Fetch", help="Fetch historical price for selected date"):
                with st.spinner("Fetching..."):
                    hist_price = get_historical_price(ticker, date)
                    if hist_price:
                        # Convert to AUD if needed
                        price_aud = hist_price * usd_to_aud
                        st.success(f"${price_aud:.2f}")
                        st.session_state.fetched_price = price_aud

        # Update price if fetched
        if 'fetched_price' in st.session_state:
            price = st.session_state.fetched_price
            del st.session_state.fetched_price
    else:
        price = st.number_input("Price per Unit (AUD)", min_value=0.0, step=0.01, format="%.2f")

    quantity = st.number_input("Quantity", min_value=0.0, step=0.01, format="%.4f")

    if st.button("Add Transaction", type="primary", use_container_width=True):
        if asset_name and quantity > 0 and price > 0:
            add_transaction(asset_name, asset_type, quantity, price, date, transaction_type, ticker)
            st.success(f"Added {transaction_type} transaction for {asset_name}")
            st.rerun()
        else:
            st.error("Please fill in all fields correctly")

    st.markdown("---")

    # Quick Stats in Sidebar
    if st.session_state.portfolio:
        st.markdown("### Quick Stats")

        # Calculate quick metrics
        from utils.data_fetchers import get_live_price as get_price_cached

        holdings_value = 0
        for txn in st.session_state.portfolio:
            if txn['transaction_type'] == 'Buy':
                holdings_value += txn['total_value']
            else:
                holdings_value -= txn['total_value']

        st.metric("Net Invested", f"A${holdings_value:,.0f}")
        st.metric("Total Transactions", len(st.session_state.portfolio))

    st.markdown("---")

    # Data management
    with st.expander("Data Management"):
        if st.button("Export Data", use_container_width=True):
            import pandas as pd
            df = pd.DataFrame(st.session_state.portfolio)
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                f"portfolio_backup_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )

        if st.button("Clear All Data", type="secondary", use_container_width=True):
            if st.checkbox("Confirm deletion"):
                st.session_state.portfolio = []
                save_data()
                st.success("Data cleared!")
                st.rerun()


# Main Navigation
st.sidebar.markdown("---")
st.sidebar.markdown("### Navigation")

# Create navigation buttons
pages = {
    "📊 Overview": overview,
    "💼 Holdings": holdings,
    "📈 Performance": performance,
    "📝 Transactions": transactions,
    "📰 News": news
}

# Radio buttons for navigation
selected_page = st.sidebar.radio(
    "Go to",
    list(pages.keys()),
    index=0,
    label_visibility="collapsed"
)

# Update current page
st.session_state.current_page = selected_page

# Render the selected page
current_page_name = selected_page.split(" ", 1)[1]  # Remove emoji
pages[selected_page].show()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit")
st.sidebar.caption("Live prices via Yahoo Finance")
st.sidebar.caption("v2.0 - Multi-Page Dashboard")

# Main page footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("💰 Personal Finance Portfolio Tracker")
with col2:
    st.caption("Prices update every 5 minutes")
with col3:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
