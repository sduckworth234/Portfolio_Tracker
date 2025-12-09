import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import yfinance as yf

# Page configuration
st.set_page_config(page_title="Personal Finance Portfolio Tracker", page_icon="💰", layout="wide")

# File to store portfolio data
DATA_FILE = "portfolio_data.json"

# Initialize session state
if 'portfolio' not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            st.session_state.portfolio = json.load(f)
    else:
        st.session_state.portfolio = []

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
        st.error(f"Error fetching price: {str(e)}")
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

def delete_transaction(index):
    """Delete a transaction by index"""
    if 0 <= index < len(st.session_state.portfolio):
        st.session_state.portfolio.pop(index)
        save_data()
        return True
    return False

def get_portfolio_summary():
    """Calculate portfolio summary statistics with live prices"""
    if not st.session_state.portfolio:
        return pd.DataFrame()

    df = pd.DataFrame(st.session_state.portfolio)

    # Calculate net quantities and cost basis
    summary_list = []
    for (asset_name, asset_type, ticker), group in df.groupby(['asset_name', 'asset_type', 'ticker']):
        buys = group[group['transaction_type'] == 'Buy']
        sells = group[group['transaction_type'] == 'Sell']

        quantity = buys['quantity'].sum() - sells['quantity'].sum()

        if quantity > 0:
            total_invested = buys['total_value'].sum() - sells['total_value'].sum()
            avg_price = total_invested / quantity if quantity > 0 else 0

            # Get live price for stocks and crypto
            current_price = avg_price
            if asset_type in ['Stocks', 'Crypto']:
                live_price = get_live_price(ticker)
                if live_price:
                    current_price = live_price

            current_value = quantity * current_price
            gain_loss = current_value - total_invested
            gain_loss_pct = (gain_loss / total_invested * 100) if total_invested > 0 else 0

            summary_list.append({
                'asset_name': asset_name,
                'asset_type': asset_type,
                'ticker': ticker,
                'quantity': quantity,
                'avg_price': avg_price,
                'current_price': current_price,
                'total_invested': total_invested,
                'current_value': current_value,
                'gain_loss': gain_loss,
                'gain_loss_pct': gain_loss_pct
            })

    return pd.DataFrame(summary_list) if summary_list else pd.DataFrame()

# App title
st.title("💰 Personal Finance Portfolio Tracker")
st.markdown("### 🇦🇺 All values in AUD")
st.markdown("---")

# Get forex rate for display
usd_to_aud = get_forex_rate('USD', 'AUD')
st.sidebar.info(f"Current USD/AUD: ${usd_to_aud:.4f}")

# Sidebar for adding transactions
with st.sidebar:
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
                        # Convert to AUD
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

    if st.button("Add Transaction", type="primary"):
        if asset_name and quantity > 0 and price > 0:
            add_transaction(asset_name, asset_type, quantity, price, date, transaction_type, ticker)
            st.success(f"Added {transaction_type} transaction for {asset_name}")
            st.rerun()
        else:
            st.error("Please fill in all fields correctly")

    st.markdown("---")

    if st.button("Clear All Data", type="secondary"):
        st.session_state.portfolio = []
        save_data()
        st.rerun()

# Main content
tab1, tab2, tab3 = st.tabs(["📊 Portfolio Overview", "📈 Holdings", "📝 Transaction History"])

with tab1:
    st.header("Portfolio Overview")

    summary = get_portfolio_summary()

    if not summary.empty:
        # Portfolio metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_value = summary['current_value'].sum()
            st.metric("Current Portfolio Value", f"A${total_value:,.2f}")

        with col2:
            total_invested = summary['total_invested'].sum()
            st.metric("Total Invested", f"A${total_invested:,.2f}")

        with col3:
            total_gain = summary['gain_loss'].sum()
            total_gain_pct = (total_gain / total_invested * 100) if total_invested > 0 else 0
            st.metric("Total Gain/Loss", f"A${total_gain:,.2f}", f"{total_gain_pct:+.2f}%")

        with col4:
            num_assets = len(summary)
            st.metric("Number of Assets", num_assets)

        st.markdown("---")

        # Portfolio allocation pie chart
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Portfolio Allocation by Asset")
            fig = px.pie(summary, values='current_value', names='asset_name',
                        title='Assets Distribution (by Current Value)')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Portfolio Allocation by Type")
            type_summary = summary.groupby('asset_type')['current_value'].sum().reset_index()
            fig = px.pie(type_summary, values='current_value', names='asset_type',
                        title='Asset Types Distribution')
            st.plotly_chart(fig, use_container_width=True)

        # Performance chart
        st.subheader("Performance by Asset")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Invested',
            x=summary['asset_name'],
            y=summary['total_invested'],
            marker_color='lightblue'
        ))
        fig.add_trace(go.Bar(
            name='Current Value',
            x=summary['asset_name'],
            y=summary['current_value'],
            marker_color='green'
        ))
        fig.update_layout(
            barmode='group',
            xaxis_title="Asset",
            yaxis_title="Value (AUD)",
            title="Investment vs Current Value"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No portfolio data yet. Add your first transaction using the sidebar!")

with tab2:
    st.header("Current Holdings")

    summary = get_portfolio_summary()

    if not summary.empty:
        # Display holdings table
        display_df = summary.copy()
        display_df['avg_price'] = display_df['avg_price'].apply(lambda x: f"A${x:,.2f}")
        display_df['current_price'] = display_df['current_price'].apply(lambda x: f"A${x:,.2f}")
        display_df['total_invested'] = display_df['total_invested'].apply(lambda x: f"A${x:,.2f}")
        display_df['current_value'] = display_df['current_value'].apply(lambda x: f"A${x:,.2f}")
        display_df['gain_loss'] = display_df.apply(
            lambda x: f"A${float(x['gain_loss'].replace('A$', '').replace(',', '')):,.2f}"
            if isinstance(x['gain_loss'], str) else f"A${x['gain_loss']:,.2f}",
            axis=1
        )
        display_df['gain_loss_pct'] = summary['gain_loss_pct'].apply(lambda x: f"{x:+.2f}%")

        display_df = display_df[['asset_name', 'ticker', 'asset_type', 'quantity', 'avg_price',
                                'current_price', 'total_invested', 'current_value', 'gain_loss', 'gain_loss_pct']]
        display_df.columns = ['Asset', 'Ticker', 'Type', 'Qty', 'Avg Price', 'Current Price',
                             'Invested', 'Current Value', 'Gain/Loss', 'Return %']

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Gainers and losers
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🟢 Top Gainers")
            gainers = summary.nlargest(3, 'gain_loss_pct')[['asset_name', 'gain_loss_pct']]
            for _, row in gainers.iterrows():
                st.metric(row['asset_name'], f"{row['gain_loss_pct']:+.2f}%")

        with col2:
            st.subheader("🔴 Top Losers")
            losers = summary.nsmallest(3, 'gain_loss_pct')[['asset_name', 'gain_loss_pct']]
            for _, row in losers.iterrows():
                st.metric(row['asset_name'], f"{row['gain_loss_pct']:+.2f}%")
    else:
        st.info("No holdings to display yet.")

with tab3:
    st.header("Transaction History")

    if st.session_state.portfolio:
        st.subheader("All Transactions")

        # Column headers
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.5, 2, 1.5, 1.5, 1.5, 1, 1.5, 1.5, 1])
        with col1:
            st.markdown("**Date**")
        with col2:
            st.markdown("**Asset**")
        with col3:
            st.markdown("**Ticker**")
        with col4:
            st.markdown("**Type**")
        with col5:
            st.markdown("**Transaction**")
        with col6:
            st.markdown("**Qty**")
        with col7:
            st.markdown("**Price**")
        with col8:
            st.markdown("**Total**")
        with col9:
            st.markdown("**Delete**")

        st.markdown("---")

        # Create a sorted copy with original indices
        transactions_with_index = [(i, t) for i, t in enumerate(st.session_state.portfolio)]
        transactions_with_index.sort(key=lambda x: x[1]['date'], reverse=True)

        # Display transactions with delete buttons
        for original_idx, transaction in transactions_with_index:
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.5, 2, 1.5, 1.5, 1.5, 1, 1.5, 1.5, 1])

            with col1:
                st.text(transaction['date'])
            with col2:
                st.text(transaction['asset_name'])
            with col3:
                st.text(transaction.get('ticker', transaction['asset_name']))
            with col4:
                st.text(transaction['asset_type'])
            with col5:
                badge_color = "🟢" if transaction['transaction_type'] == 'Buy' else "🔴"
                st.text(f"{badge_color} {transaction['transaction_type']}")
            with col6:
                st.text(f"{transaction['quantity']:.4f}")
            with col7:
                st.text(f"A${transaction['price']:,.2f}")
            with col8:
                st.text(f"A${transaction['total_value']:,.2f}")
            with col9:
                if st.button("🗑️", key=f"delete_{original_idx}", help="Delete transaction"):
                    if delete_transaction(original_idx):
                        st.success("Transaction deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete transaction")

        st.markdown("---")

        # Transaction timeline
        st.subheader("Transaction Timeline")
        df_timeline = pd.DataFrame(st.session_state.portfolio)
        df_timeline['date'] = pd.to_datetime(df_timeline['date'])

        fig = px.scatter(df_timeline, x='date', y='total_value',
                        color='transaction_type', size='total_value',
                        hover_data=['asset_name', 'quantity', 'price'],
                        title='Transaction Timeline (AUD)')
        fig.update_layout(xaxis_title="Date", yaxis_title="Transaction Value (AUD)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transactions recorded yet.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit | Personal Finance Portfolio Tracker | Live prices powered by Yahoo Finance")
st.caption("Note: Live prices update every 5 minutes. Stock prices are converted from USD to AUD using current forex rates.")
