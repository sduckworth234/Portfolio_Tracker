"""
Overview Page - Portfolio Dashboard Home
Displays key metrics, portfolio value timeline, and allocation visualizations.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_fetchers import get_live_price, get_market_indicators, calculate_portfolio_history, get_benchmark_data
from utils.calculations import calculate_time_weighted_return, calculate_simple_return, calculate_ytd_return
from utils.visualizations import (
    create_portfolio_value_chart,
    create_treemap,
    create_sunburst_chart,
    create_allocation_pie,
    create_multi_benchmark_comparison
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
    """Render the Overview page"""
    st.title("Portfolio Overview")
    st.markdown("### Your complete financial dashboard")

    # Get portfolio data
    summary = get_portfolio_summary()

    if summary.empty:
        st.info("No portfolio data yet. Add your first transaction using the sidebar to get started!")
        return

    # Calculate portfolio metrics
    total_value = summary['current_value'].sum()
    total_invested = summary['total_invested'].sum()
    total_gain = summary['gain_loss'].sum()
    total_gain_pct = (total_gain / total_invested * 100) if total_invested > 0 else 0

    # Get market indicators
    with st.spinner("Fetching market data..."):
        market_indicators = get_market_indicators()

    # Get best and worst performers
    best_performer = summary.nlargest(1, 'gain_loss_pct').iloc[0] if not summary.empty else None
    worst_performer = summary.nsmallest(1, 'gain_loss_pct').iloc[0] if not summary.empty else None

    # Calculate portfolio concentration
    from utils.calculations import calculate_portfolio_concentration
    concentration = calculate_portfolio_concentration(summary, 'current_value')

    # ROW 1: Key Metrics
    st.markdown("#### Key Portfolio Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Portfolio Value",
            f"A${total_value:,.2f}",
            delta=f"{total_gain_pct:+.2f}%",
            help="Current total value of all holdings"
        )

    with col2:
        st.metric(
            "Total Invested",
            f"A${total_invested:,.2f}",
            help="Total amount invested (cost basis)"
        )

    with col3:
        st.metric(
            "Total Gain/Loss",
            f"A${total_gain:,.2f}",
            delta=f"{total_gain_pct:+.2f}%",
            help="Absolute and percentage gain/loss"
        )

    with col4:
        # Try to calculate YTD return
        try:
            history = calculate_portfolio_history(st.session_state.portfolio)
            if not history.empty:
                history = history.set_index('date')
                ytd = calculate_ytd_return(history, 'value')
                st.metric(
                    "YTD Return",
                    f"{ytd:+.2f}%",
                    help="Year-to-date return"
                )
            else:
                st.metric("YTD Return", "N/A")
        except:
            st.metric("YTD Return", "N/A")

    # ROW 2: Additional Metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if best_performer is not None:
            st.metric(
                "Best Performer",
                best_performer['asset_name'],
                delta=f"{best_performer['gain_loss_pct']:+.2f}%",
                help="Top performing asset"
            )
        else:
            st.metric("Best Performer", "N/A")

    with col2:
        if worst_performer is not None:
            st.metric(
                "Worst Performer",
                worst_performer['asset_name'],
                delta=f"{worst_performer['gain_loss_pct']:+.2f}%",
                help="Worst performing asset"
            )
        else:
            st.metric("Worst Performer", "N/A")

    with col3:
        num_assets = len(summary)
        st.metric(
            "Number of Holdings",
            num_assets,
            help="Total number of different assets"
        )

    with col4:
        top_1_concentration = concentration['top_1_pct']
        st.metric(
            "Top Holding Weight",
            f"{top_1_concentration:.1f}%",
            help="Percentage of portfolio in largest holding"
        )

    st.markdown("---")

    # Market Indicators Section
    st.markdown("#### Market Indicators")
    col1, col2, col3 = st.columns(3)

    with col1:
        if 'asx200_price' in market_indicators:
            st.metric(
                "ASX 200",
                f"${market_indicators['asx200_price']:.2f}",
                delta=f"{market_indicators.get('asx200_change_pct', 0):+.2f}%",
                help="ASX 200 index (via STW.AX)"
            )
        else:
            st.metric("ASX 200", "N/A")

    with col2:
        if 'vix' in market_indicators:
            st.metric(
                "VIX (Fear Index)",
                f"{market_indicators['vix']:.2f}",
                help="Market volatility indicator"
            )
        else:
            st.metric("VIX", "N/A")

    with col3:
        if 'usd_aud' in market_indicators:
            st.metric(
                "USD/AUD",
                f"${market_indicators['usd_aud']:.4f}",
                help="Current exchange rate"
            )
        else:
            st.metric("USD/AUD", "N/A")

    st.markdown("---")

    # Portfolio Value Over Time Chart
    st.markdown("#### Portfolio Value Timeline")

    with st.spinner("Loading portfolio history..."):
        try:
            history = calculate_portfolio_history(st.session_state.portfolio)

            if not history.empty:
                # Create the timeline chart with transaction markers
                fig = create_portfolio_value_chart(history, st.session_state.portfolio)
                st.plotly_chart(fig, use_container_width=True)

                # Calculate and display Time-Weighted Return
                twr = calculate_time_weighted_return(history)
                simple_return = calculate_simple_return(total_invested, total_value)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Time-Weighted Return",
                        f"{twr:+.2f}%",
                        help="TWR eliminates the impact of cash flows, measuring pure investment performance"
                    )
                with col2:
                    st.metric(
                        "Simple Return",
                        f"{simple_return:+.2f}%",
                        help="Simple return = (Current Value - Invested) / Invested"
                    )
                with col3:
                    # Calculate CAGR if we have enough history
                    if len(history) > 30:  # At least a month of data
                        days = (history['date'].max() - history['date'].min()).days
                        years = days / 365.25
                        if years > 0:
                            from utils.calculations import calculate_cagr
                            initial_value = history['value'].iloc[0]
                            final_value = history['value'].iloc[-1]
                            cagr = calculate_cagr(initial_value, final_value, years)
                            st.metric(
                                "CAGR",
                                f"{cagr:+.2f}%",
                                help="Compound Annual Growth Rate"
                            )
                        else:
                            st.metric("CAGR", "N/A")
                    else:
                        st.metric("CAGR", "N/A", help="Need more history")

            else:
                st.info("Not enough data to display portfolio timeline. Add more transactions!")
        except Exception as e:
            st.error(f"Error loading portfolio history: {str(e)}")

    st.markdown("---")

    # Quick Benchmark Comparison
    st.markdown("#### Quick Benchmark Comparison")

    with st.expander("Compare with Market Benchmarks", expanded=False):
        st.markdown("Quickly compare your portfolio performance against major indices.")

        col1, col2 = st.columns([3, 1])

        with col1:
            quick_benchmarks = st.multiselect(
                "Select benchmarks",
                options=['ASX 200', 'S&P 500', 'NASDAQ', 'VTS', 'VGS'],
                default=['ASX 200'],
                key="overview_benchmarks"
            )

        with col2:
            quick_normalize = st.checkbox("Normalize", value=True, key="overview_normalize")

        if quick_benchmarks:
            try:
                history = calculate_portfolio_history(st.session_state.portfolio)

                if not history.empty:
                    start_date = history['date'].min().strftime('%Y-%m-%d')
                    benchmark_data_dict = {}

                    with st.spinner("Fetching benchmark data..."):
                        for benchmark_name in quick_benchmarks:
                            bench_data = get_benchmark_data(benchmark_name, start_date)
                            if not bench_data.empty:
                                benchmark_data_dict[benchmark_name] = bench_data

                    if benchmark_data_dict:
                        fig = create_multi_benchmark_comparison(
                            history,
                            benchmark_data_dict,
                            normalize=quick_normalize
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        # Quick performance summary
                        st.markdown("**Performance Summary**")
                        perf_cols = st.columns(len(benchmark_data_dict) + 1)

                        portfolio_return = ((history['value'].iloc[-1] / history['value'].iloc[0]) - 1) * 100

                        with perf_cols[0]:
                            st.metric("Your Portfolio", f"{portfolio_return:+.2f}%")

                        for idx, (bench_name, bench_data) in enumerate(benchmark_data_dict.items(), 1):
                            if idx < len(perf_cols):
                                with perf_cols[idx]:
                                    bench_return = ((bench_data['Close'].iloc[-1] / bench_data['Close'].iloc[0]) - 1) * 100
                                    diff = portfolio_return - bench_return
                                    st.metric(
                                        bench_name,
                                        f"{bench_return:+.2f}%",
                                        delta=f"{diff:+.2f}% diff",
                                        delta_color="normal" if diff >= 0 else "inverse"
                                    )

                        st.info("For detailed performance analysis, visit the Performance page.")
            except Exception as e:
                st.error(f"Error loading benchmark comparison: {str(e)}")

    st.markdown("---")

    # Allocation Visualizations
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Portfolio Treemap")
        with st.spinner("Creating treemap..."):
            try:
                fig = create_treemap(summary)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating treemap: {str(e)}")

    with col2:
        st.markdown("#### Asset Type Allocation")
        with st.spinner("Creating allocation chart..."):
            try:
                fig = create_allocation_pie(summary, group_by='asset_type')
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating allocation chart: {str(e)}")

    # Sunburst Chart
    st.markdown("---")
    st.markdown("#### Hierarchical Portfolio View")
    with st.spinner("Creating sunburst chart..."):
        try:
            fig = create_sunburst_chart(summary)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating sunburst chart: {str(e)}")

    # Portfolio Insights
    st.markdown("---")
    st.markdown("#### Portfolio Insights")

    insights = []

    # Concentration risk
    if concentration['top_1_pct'] > 30:
        insights.append({
            'type': 'warning',
            'title': 'High Concentration Risk',
            'message': f"Your largest holding represents {concentration['top_1_pct']:.1f}% of your portfolio. Consider diversifying."
        })

    # Performance insights
    if total_gain_pct > 10:
        insights.append({
            'type': 'success',
            'title': 'Strong Performance',
            'message': f"Your portfolio is up {total_gain_pct:.2f}%! Great job!"
        })
    elif total_gain_pct < -10:
        insights.append({
            'type': 'error',
            'title': 'Portfolio Down',
            'message': f"Your portfolio is down {abs(total_gain_pct):.2f}%. Consider reviewing your strategy."
        })

    # Asset type diversification
    asset_types = summary['asset_type'].nunique()
    if asset_types == 1:
        insights.append({
            'type': 'info',
            'title': 'Limited Diversification',
            'message': "Your portfolio contains only one asset type. Consider diversifying across asset classes."
        })

    # Display insights
    if insights:
        for insight in insights:
            if insight['type'] == 'warning':
                st.warning(f"**{insight['title']}**: {insight['message']}")
            elif insight['type'] == 'success':
                st.success(f"**{insight['title']}**: {insight['message']}")
            elif insight['type'] == 'error':
                st.error(f"**{insight['title']}**: {insight['message']}")
            else:
                st.info(f"**{insight['title']}**: {insight['message']}")
    else:
        st.info("No specific insights at this time. Keep monitoring your portfolio!")


# Run the page
if __name__ == "__main__":
    show()
