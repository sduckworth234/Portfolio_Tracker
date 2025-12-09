import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os

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

def save_data():
    """Save portfolio data to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(st.session_state.portfolio, f, indent=2)

def add_transaction(asset_name, asset_type, quantity, price, date, transaction_type):
    """Add a new transaction to the portfolio"""
    transaction = {
        'asset_name': asset_name,
        'asset_type': asset_type,
        'quantity': quantity,
        'price': price,
        'date': date.strftime('%Y-%m-%d'),
        'transaction_type': transaction_type,
        'total_value': quantity * price
    }
    st.session_state.portfolio.append(transaction)
    save_data()

def get_portfolio_summary():
    """Calculate portfolio summary statistics"""
    if not st.session_state.portfolio:
        return pd.DataFrame()

    df = pd.DataFrame(st.session_state.portfolio)

    # Calculate net quantities (buys - sells)
    summary = df.groupby(['asset_name', 'asset_type']).apply(
        lambda x: pd.Series({
            'quantity': x[x['transaction_type'] == 'Buy']['quantity'].sum() -
                       x[x['transaction_type'] == 'Sell']['quantity'].sum(),
            'total_invested': (x[x['transaction_type'] == 'Buy']['total_value'].sum() -
                             x[x['transaction_type'] == 'Sell']['total_value'].sum()),
            'avg_price': x['price'].mean()
        })
    ).reset_index()

    return summary[summary['quantity'] > 0]

# App title
st.title("💰 Personal Finance Portfolio Tracker")
st.markdown("---")

# Sidebar for adding transactions
with st.sidebar:
    st.header("Add Transaction")

    asset_name = st.text_input("Asset Name", placeholder="e.g., Apple, Bitcoin, USD")
    asset_type = st.selectbox("Asset Type", ["Stocks", "Crypto", "Cash", "Bonds", "Real Estate", "Other"])
    transaction_type = st.radio("Transaction Type", ["Buy", "Sell"])
    quantity = st.number_input("Quantity", min_value=0.0, step=0.01, format="%.4f")
    price = st.number_input("Price per Unit", min_value=0.0, step=0.01, format="%.2f")
    date = st.date_input("Date", value=datetime.now())

    if st.button("Add Transaction", type="primary"):
        if asset_name and quantity > 0 and price > 0:
            add_transaction(asset_name, asset_type, quantity, price, date, transaction_type)
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
        col1, col2, col3 = st.columns(3)

        with col1:
            total_value = summary['total_invested'].sum()
            st.metric("Total Portfolio Value", f"${total_value:,.2f}")

        with col2:
            num_assets = len(summary)
            st.metric("Number of Assets", num_assets)

        with col3:
            asset_types = summary['asset_type'].nunique()
            st.metric("Asset Types", asset_types)

        st.markdown("---")

        # Portfolio allocation pie chart
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Portfolio Allocation by Asset")
            fig = px.pie(summary, values='total_invested', names='asset_name',
                        title='Assets Distribution')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Portfolio Allocation by Type")
            type_summary = summary.groupby('asset_type')['total_invested'].sum().reset_index()
            fig = px.pie(type_summary, values='total_invested', names='asset_type',
                        title='Asset Types Distribution')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No portfolio data yet. Add your first transaction using the sidebar!")

with tab2:
    st.header("Current Holdings")

    summary = get_portfolio_summary()

    if not summary.empty:
        # Display holdings table
        display_df = summary.copy()
        display_df['total_invested'] = display_df['total_invested'].apply(lambda x: f"${x:,.2f}")
        display_df['avg_price'] = display_df['avg_price'].apply(lambda x: f"${x:,.2f}")
        display_df.columns = ['Asset Name', 'Asset Type', 'Quantity', 'Total Invested', 'Avg Price']

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Bar chart of holdings
        st.subheader("Holdings Value")
        summary_chart = summary.copy()
        fig = px.bar(summary_chart, x='asset_name', y='total_invested',
                    color='asset_type', title='Value by Asset')
        fig.update_layout(xaxis_title="Asset", yaxis_title="Value ($)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No holdings to display yet.")

with tab3:
    st.header("Transaction History")

    if st.session_state.portfolio:
        df = pd.DataFrame(st.session_state.portfolio)
        df = df.sort_values('date', ascending=False)

        # Display transaction history
        display_df = df.copy()
        display_df['total_value'] = display_df['total_value'].apply(lambda x: f"${x:,.2f}")
        display_df['price'] = display_df['price'].apply(lambda x: f"${x:,.2f}")
        display_df.columns = ['Asset Name', 'Asset Type', 'Quantity', 'Price', 'Date',
                              'Type', 'Total Value']

        st.dataframe(display_df[['Date', 'Asset Name', 'Asset Type', 'Type', 'Quantity',
                                'Price', 'Total Value']],
                    use_container_width=True, hide_index=True)

        # Transaction timeline
        st.subheader("Transaction Timeline")
        df_timeline = df.copy()
        df_timeline['date'] = pd.to_datetime(df_timeline['date'])

        fig = px.scatter(df_timeline, x='date', y='total_value',
                        color='transaction_type', size='total_value',
                        hover_data=['asset_name', 'quantity', 'price'],
                        title='Transaction Timeline')
        fig.update_layout(xaxis_title="Date", yaxis_title="Transaction Value ($)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transactions recorded yet.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit | Personal Finance Portfolio Tracker")
