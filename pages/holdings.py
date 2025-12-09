"""
Holdings Page - Detailed Holdings Analysis
Displays detailed holdings table, correlation heatmap, sector analysis, and top gainers/losers.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_fetchers import get_live_price, get_stock_info, get_correlation_matrix
from utils.visualizations import (
    create_correlation_heatmap,
    create_sector_performance_chart,
    create_holdings_performance_bars
)


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


def show():
    """Render the Holdings page"""
    st.title("Current Holdings")
    st.markdown("### Detailed analysis of your portfolio positions")

    # Get portfolio data
    summary = get_portfolio_summary()

    if summary.empty:
        st.info("No holdings to display yet. Add your first transaction to get started!")
        return

    # Add sector information for stocks
    stock_holdings = summary[summary['asset_type'] == 'Stocks'].copy()
    if not stock_holdings.empty:
        with st.spinner("Fetching stock information..."):
            sectors = []
            for ticker in stock_holdings['ticker']:
                info = get_stock_info(ticker)
                sectors.append(info.get('sector', 'Unknown'))
            stock_holdings['sector'] = sectors

        # Merge sector info back to main summary
        summary = summary.merge(
            stock_holdings[['ticker', 'sector']],
            on='ticker',
            how='left'
        )
        summary['sector'] = summary['sector'].fillna('N/A')
    else:
        summary['sector'] = 'N/A'

    # Summary Statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_value = summary['current_value'].sum()
        st.metric("Total Holdings Value", f"A${total_value:,.2f}")

    with col2:
        num_holdings = len(summary)
        st.metric("Number of Holdings", num_holdings)

    with col3:
        avg_gain = summary['gain_loss_pct'].mean()
        st.metric("Average Return", f"{avg_gain:+.2f}%")

    with col4:
        num_profitable = len(summary[summary['gain_loss'] > 0])
        st.metric("Profitable Holdings", f"{num_profitable}/{num_holdings}")

    st.markdown("---")

    # Interactive Holdings Table
    st.markdown("#### Holdings Table")

    # Create display dataframe with formatted values
    display_df = summary.copy()

    # Add allocation percentage
    display_df['allocation_pct'] = (display_df['current_value'] / display_df['current_value'].sum() * 100)

    # Format for display
    display_df['avg_price_fmt'] = display_df['avg_price'].apply(lambda x: f"A${x:,.2f}")
    display_df['current_price_fmt'] = display_df['current_price'].apply(lambda x: f"A${x:,.2f}")
    display_df['total_invested_fmt'] = display_df['total_invested'].apply(lambda x: f"A${x:,.2f}")
    display_df['current_value_fmt'] = display_df['current_value'].apply(lambda x: f"A${x:,.2f}")
    display_df['gain_loss_fmt'] = display_df['gain_loss'].apply(lambda x: f"A${x:,.2f}")
    display_df['gain_loss_pct_fmt'] = display_df['gain_loss_pct'].apply(lambda x: f"{x:+.2f}%")
    display_df['allocation_pct_fmt'] = display_df['allocation_pct'].apply(lambda x: f"{x:.1f}%")

    # Select columns for display
    table_df = display_df[[
        'asset_name', 'ticker', 'asset_type', 'sector', 'quantity',
        'avg_price_fmt', 'current_price_fmt', 'total_invested_fmt',
        'current_value_fmt', 'gain_loss_fmt', 'gain_loss_pct_fmt', 'allocation_pct_fmt'
    ]].copy()

    table_df.columns = [
        'Asset', 'Ticker', 'Type', 'Sector', 'Quantity',
        'Avg Price', 'Current Price', 'Invested',
        'Current Value', 'Gain/Loss', 'Return %', 'Allocation %'
    ]

    # Display with sorting options
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )

    # Download button for holdings data
    csv = summary.to_csv(index=False)
    st.download_button(
        label="Download Holdings Data (CSV)",
        data=csv,
        file_name=f"portfolio_holdings_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

    st.markdown("---")

    # Performance Visualization
    st.markdown("#### Holdings Performance")
    fig = create_holdings_performance_bars(summary)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Top Gainers and Losers
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Top Gainers")
        gainers = summary.nlargest(5, 'gain_loss_pct')[['asset_name', 'gain_loss', 'gain_loss_pct']]

        if not gainers.empty:
            for idx, row in gainers.iterrows():
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"**{row['asset_name']}**")
                with col_b:
                    st.write(f":{'' if row['gain_loss_pct'] >= 0 else ''}[{row['gain_loss_pct']:+.2f}%]")
                st.caption(f"Gain: A${row['gain_loss']:,.2f}")
                st.divider()
        else:
            st.info("No gainers yet")

    with col2:
        st.markdown("#### Top Losers")
        losers = summary.nsmallest(5, 'gain_loss_pct')[['asset_name', 'gain_loss', 'gain_loss_pct']]

        if not losers.empty:
            for idx, row in losers.iterrows():
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"**{row['asset_name']}**")
                with col_b:
                    st.write(f":{'' if row['gain_loss_pct'] >= 0 else ''}[{row['gain_loss_pct']:+.2f}%]")
                st.caption(f"Loss: A${row['gain_loss']:,.2f}")
                st.divider()
        else:
            st.info("No losers yet")

    st.markdown("---")

    # Sector Analysis (if applicable)
    if not stock_holdings.empty and 'sector' in summary.columns:
        st.markdown("#### Sector Analysis")

        # Sector allocation
        sector_summary = summary[summary['sector'] != 'N/A'].groupby('sector').agg({
            'current_value': 'sum',
            'gain_loss': 'sum',
            'total_invested': 'sum'
        }).reset_index()

        if not sector_summary.empty:
            sector_summary['gain_loss_pct'] = (
                sector_summary['gain_loss'] / sector_summary['total_invested'] * 100
            )

            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown("**Sector Allocation**")
                for _, row in sector_summary.iterrows():
                    pct = (row['current_value'] / summary['current_value'].sum() * 100)
                    st.write(f"**{row['sector']}**: {pct:.1f}%")
                    st.caption(f"Value: A${row['current_value']:,.2f}")

            with col2:
                # Sector performance chart
                fig = create_sector_performance_chart(summary)
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Correlation Matrix (for stocks only)
    if not stock_holdings.empty and len(stock_holdings) > 1:
        st.markdown("#### Stock Correlation Matrix")
        st.caption("Shows how your stocks move together. Values close to 1 indicate strong positive correlation.")

        with st.spinner("Calculating correlations..."):
            try:
                # Get list of stock tickers
                tickers = stock_holdings['ticker'].tolist()

                # Calculate correlation over last 3 months
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                correlation_df = get_correlation_matrix(tickers, start_date)

                if not correlation_df.empty:
                    fig = create_correlation_heatmap(correlation_df)
                    st.plotly_chart(fig, use_container_width=True)

                    # Correlation insights
                    st.markdown("**Correlation Insights:**")

                    # Find highly correlated pairs (> 0.7)
                    high_corr = []
                    for i in range(len(correlation_df.columns)):
                        for j in range(i+1, len(correlation_df.columns)):
                            corr_value = correlation_df.iloc[i, j]
                            if corr_value > 0.7:
                                high_corr.append({
                                    'pair': f"{correlation_df.columns[i]} & {correlation_df.columns[j]}",
                                    'correlation': corr_value
                                })

                    if high_corr:
                        st.warning(f"**High Correlation Detected**: The following stock pairs move very similarly, which may reduce diversification benefits:")
                        for pair in high_corr:
                            st.write(f"- {pair['pair']}: {pair['correlation']:.2f}")
                    else:
                        st.success("No highly correlated stock pairs detected. Good diversification!")

                else:
                    st.info("Not enough historical data to calculate correlations.")

            except Exception as e:
                st.error(f"Error calculating correlation matrix: {str(e)}")

    # Holdings by Asset Type
    st.markdown("---")
    st.markdown("#### Holdings by Asset Type")

    type_summary = summary.groupby('asset_type').agg({
        'current_value': 'sum',
        'gain_loss': 'sum',
        'total_invested': 'sum'
    }).reset_index()

    type_summary['gain_loss_pct'] = (
        type_summary['gain_loss'] / type_summary['total_invested'] * 100
    )
    type_summary['allocation_pct'] = (
        type_summary['current_value'] / type_summary['current_value'].sum() * 100
    )

    for _, row in type_summary.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"**{row['asset_type']}**")

            with col2:
                st.metric("Value", f"A${row['current_value']:,.2f}")

            with col3:
                st.metric("Return", f"{row['gain_loss_pct']:+.2f}%")

            with col4:
                st.metric("Allocation", f"{row['allocation_pct']:.1f}%")

            st.divider()


# Run the page
if __name__ == "__main__":
    show()
