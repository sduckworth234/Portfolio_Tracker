"""
Transactions Page - Transaction Management
Displays transaction history, timeline visualization, and management tools.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def delete_transaction(index):
    """Delete a transaction by index"""
    if 0 <= index < len(st.session_state.portfolio):
        st.session_state.portfolio.pop(index)
        # Save to file
        import json
        DATA_FILE = "portfolio_data.json"
        with open(DATA_FILE, 'w') as f:
            json.dump(st.session_state.portfolio, f, indent=2)
        return True
    return False


def show():
    """Render the Transactions page"""
    st.title("Transaction History")
    st.markdown("### View and manage all portfolio transactions")

    if not st.session_state.portfolio:
        st.info("No transactions recorded yet. Add your first transaction using the sidebar!")
        return

    # Transaction summary statistics
    df_all = pd.DataFrame(st.session_state.portfolio)
    df_all['date'] = pd.to_datetime(df_all['date'])

    buys = df_all[df_all['transaction_type'] == 'Buy']
    sells = df_all[df_all['transaction_type'] == 'Sell']

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Transactions", len(df_all))

    with col2:
        st.metric("Buy Transactions", len(buys))

    with col3:
        st.metric("Sell Transactions", len(sells))

    with col4:
        total_invested = buys['total_value'].sum() - sells['total_value'].sum()
        st.metric("Net Invested", f"A${total_invested:,.2f}")

    st.markdown("---")

    # Filter options
    st.markdown("#### Filter Transactions")
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_type = st.selectbox(
            "Transaction Type",
            ["All", "Buy", "Sell"]
        )

    with col2:
        asset_types = ["All"] + sorted(df_all['asset_type'].unique().tolist())
        filter_asset_type = st.selectbox(
            "Asset Type",
            asset_types
        )

    with col3:
        # Date range filter
        min_date = df_all['date'].min().date()
        max_date = df_all['date'].max().date()
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

    # Apply filters
    filtered_df = df_all.copy()

    if filter_type != "All":
        filtered_df = filtered_df[filtered_df['transaction_type'] == filter_type]

    if filter_asset_type != "All":
        filtered_df = filtered_df[filtered_df['asset_type'] == filter_asset_type]

    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['date'].dt.date >= start_date) &
            (filtered_df['date'].dt.date <= end_date)
        ]

    st.markdown("---")

    # Display filtered transaction count
    st.markdown(f"**Showing {len(filtered_df)} of {len(df_all)} transactions**")

    # Transactions table
    st.markdown("#### Transaction Details")

    if not filtered_df.empty:
        # Create display dataframe
        display_df = filtered_df.copy()
        display_df['date_str'] = display_df['date'].dt.strftime('%Y-%m-%d')
        display_df = display_df.sort_values('date', ascending=False)

        # Add formatted columns
        display_df['price_fmt'] = display_df['price'].apply(lambda x: f"A${x:,.2f}")
        display_df['total_value_fmt'] = display_df['total_value'].apply(lambda x: f"A${x:,.2f}")
        display_df['quantity_fmt'] = display_df['quantity'].apply(lambda x: f"{x:,.4f}".rstrip('0').rstrip('.'))

        # Select and rename columns
        table_df = display_df[[
            'date_str', 'asset_name', 'ticker', 'asset_type',
            'transaction_type', 'quantity_fmt', 'price_fmt', 'total_value_fmt'
        ]].copy()

        table_df.columns = [
            'Date', 'Asset', 'Ticker', 'Type',
            'Transaction', 'Quantity', 'Price', 'Total Value'
        ]

        # Apply color coding to transaction type
        def color_transaction_type(val):
            color = 'green' if val == 'Buy' else 'red'
            return f'color: {color}'

        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )

        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Transactions (CSV)",
            data=csv,
            file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    else:
        st.info("No transactions match the selected filters.")

    st.markdown("---")

    # Transaction Timeline Visualization
    st.markdown("#### Transaction Timeline")

    if not df_all.empty:
        # Create scatter plot
        fig = px.scatter(
            df_all,
            x='date',
            y='total_value',
            color='transaction_type',
            size='total_value',
            hover_data=['asset_name', 'quantity', 'price', 'asset_type'],
            title='Transaction Timeline (by Value)',
            color_discrete_map={'Buy': '#06D6A0', 'Sell': '#EF476F'}
        )

        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Transaction Value (AUD)',
            height=500,
            template='plotly_white'
        )

        fig.update_yaxes(tickprefix='A$', tickformat=',.0f')

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Transaction breakdown by asset type
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Transactions by Asset Type")
        type_counts = df_all['asset_type'].value_counts().reset_index()
        type_counts.columns = ['Asset Type', 'Count']

        fig = px.pie(
            type_counts,
            names='Asset Type',
            values='Count',
            title='Transaction Distribution by Asset Type'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Buy vs Sell Volume")
        txn_type_counts = df_all['transaction_type'].value_counts().reset_index()
        txn_type_counts.columns = ['Transaction Type', 'Count']

        fig = px.bar(
            txn_type_counts,
            x='Transaction Type',
            y='Count',
            title='Buy vs Sell Transactions',
            color='Transaction Type',
            color_discrete_map={'Buy': '#06D6A0', 'Sell': '#EF476F'}
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Monthly transaction summary
    st.markdown("#### Monthly Transaction Summary")

    df_monthly = df_all.copy()
    df_monthly['month'] = df_monthly['date'].dt.to_period('M').astype(str)

    monthly_summary = df_monthly.groupby(['month', 'transaction_type'])['total_value'].sum().reset_index()

    if not monthly_summary.empty:
        fig = px.bar(
            monthly_summary,
            x='month',
            y='total_value',
            color='transaction_type',
            title='Monthly Transaction Volume',
            barmode='group',
            color_discrete_map={'Buy': '#06D6A0', 'Sell': '#EF476F'},
            labels={'total_value': 'Total Value (AUD)', 'month': 'Month'}
        )

        fig.update_layout(
            xaxis_title='Month',
            yaxis_title='Total Value (AUD)',
            height=400,
            template='plotly_white'
        )

        fig.update_yaxes(tickprefix='A$', tickformat=',.0f')

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Delete transactions section
    with st.expander("Transaction Management", expanded=False):
        st.warning("Use caution when deleting transactions. This action cannot be undone.")

        st.markdown("#### Delete Individual Transactions")

        # Create a sorted list for deletion
        transactions_with_index = [(i, t) for i, t in enumerate(st.session_state.portfolio)]
        transactions_with_index.sort(key=lambda x: x[1]['date'], reverse=True)

        # Show recent transactions for deletion
        st.markdown("**Recent Transactions:**")

        # Header row
        col1, col2, col3, col4, col5, col6 = st.columns([1.5, 2, 1.5, 1, 2, 1])
        with col1:
            st.markdown("**Date**")
        with col2:
            st.markdown("**Asset**")
        with col3:
            st.markdown("**Type**")
        with col4:
            st.markdown("**Qty**")
        with col5:
            st.markdown("**Value**")
        with col6:
            st.markdown("**Action**")

        st.markdown("---")

        # Initialize delete confirmation state
        if 'delete_confirm' not in st.session_state:
            st.session_state.delete_confirm = None

        for original_idx, transaction in transactions_with_index[:20]:  # Show last 20
            col1, col2, col3, col4, col5, col6 = st.columns([1.5, 2, 1.5, 1, 2, 1])

            with col1:
                st.text(transaction['date'])
            with col2:
                st.text(transaction['asset_name'][:20])  # Truncate long names
            with col3:
                badge = "🟢 BUY" if transaction['transaction_type'] == 'Buy' else "🔴 SELL"
                st.text(badge)
            with col4:
                st.text(f"{transaction['quantity']:.2f}")
            with col5:
                st.text(f"A${transaction['total_value']:,.2f}")
            with col6:
                # Check if this transaction is pending confirmation
                if st.session_state.delete_confirm == original_idx:
                    if st.button("✓ Confirm", key=f"confirm_txn_{original_idx}", type="primary"):
                        if delete_transaction(original_idx):
                            st.session_state.delete_confirm = None
                            st.success("Transaction deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete")
                    if st.button("✗ Cancel", key=f"cancel_txn_{original_idx}"):
                        st.session_state.delete_confirm = None
                        st.rerun()
                else:
                    if st.button("🗑️", key=f"delete_txn_{original_idx}", help="Delete this transaction"):
                        st.session_state.delete_confirm = original_idx
                        st.rerun()

        st.markdown("---")

        # Bulk operations
        st.markdown("#### Bulk Operations")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Export All Transactions", type="secondary"):
                csv = df_all.to_csv(index=False)
                st.download_button(
                    label="Download Full Transaction History",
                    data=csv,
                    file_name=f"full_transaction_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        with col2:
            st.markdown("**Clear All Data**")
            if st.button("Clear All Transactions", type="secondary"):
                if st.checkbox("I understand this will delete all transaction data"):
                    st.session_state.portfolio = []
                    import json
                    DATA_FILE = "portfolio_data.json"
                    with open(DATA_FILE, 'w') as f:
                        json.dump(st.session_state.portfolio, f, indent=2)
                    st.success("All transactions cleared!")
                    st.rerun()

    # Transaction statistics by asset
    st.markdown("---")
    st.markdown("#### Transaction Statistics by Asset")

    asset_stats = df_all.groupby('asset_name').agg({
        'transaction_type': 'count',
        'total_value': 'sum',
        'quantity': 'sum'
    }).reset_index()

    asset_stats.columns = ['Asset', 'Total Transactions', 'Total Value', 'Total Quantity']
    asset_stats = asset_stats.sort_values('Total Value', ascending=False)

    # Format for display
    asset_stats['Total Value'] = asset_stats['Total Value'].apply(lambda x: f"A${x:,.2f}")
    asset_stats['Total Quantity'] = asset_stats['Total Quantity'].apply(lambda x: f"{x:,.4f}".rstrip('0').rstrip('.'))

    st.dataframe(
        asset_stats,
        use_container_width=True,
        hide_index=True
    )


# Run the page
if __name__ == "__main__":
    show()
