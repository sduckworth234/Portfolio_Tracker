"""
Performance Page - Risk Analytics & Benchmark Comparison
Displays advanced performance metrics, risk analytics, and benchmark comparison.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_fetchers import (
    get_live_price,
    get_asx200_data,
    calculate_portfolio_history
)
from utils.calculations import (
    calculate_sharpe_ratio,
    calculate_volatility,
    calculate_beta,
    calculate_maximum_drawdown,
    calculate_daily_returns,
    calculate_portfolio_concentration,
    calculate_time_weighted_return,
    calculate_cagr
)
from utils.visualizations import (
    create_benchmark_comparison_chart,
    create_returns_distribution
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
    """Render the Performance page"""
    st.title("Performance & Risk Analytics")
    st.markdown("### Advanced metrics and benchmark comparison")

    # Get portfolio data
    summary = get_portfolio_summary()

    if summary.empty:
        st.info("No portfolio data yet. Add transactions to see performance analytics!")
        return

    # Calculate portfolio history
    with st.spinner("Calculating portfolio performance..."):
        try:
            history = calculate_portfolio_history(st.session_state.portfolio)

            if history.empty or len(history) < 2:
                st.warning("Not enough historical data for performance analysis. Add more transactions!")
                return

            # Calculate returns
            returns = calculate_daily_returns(history.set_index('date')['value'])

            # Basic metrics
            total_value = summary['current_value'].sum()
            total_invested = summary['total_invested'].sum()
            total_return_pct = ((total_value - total_invested) / total_invested * 100) if total_invested > 0 else 0

            # Time period
            days = (history['date'].max() - history['date'].min()).days
            years = days / 365.25

            # Calculate advanced metrics
            twr = calculate_time_weighted_return(history)

            # CAGR (if we have enough history)
            if years > 0:
                initial_value = history['value'].iloc[0]
                final_value = history['value'].iloc[-1]
                cagr = calculate_cagr(initial_value, final_value, years)
            else:
                cagr = 0

            # Risk metrics
            sharpe = calculate_sharpe_ratio(returns)
            volatility = calculate_volatility(returns)

            # Maximum drawdown
            history_indexed = history.set_index('date')
            max_dd, peak_date, trough_date = calculate_maximum_drawdown(history_indexed['value'])

            # Portfolio concentration
            concentration = calculate_portfolio_concentration(summary, 'current_value')

            # Display Performance Metrics
            st.markdown("#### Return Metrics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Total Return",
                    f"{total_return_pct:+.2f}%",
                    help="Simple return = (Current - Invested) / Invested"
                )

            with col2:
                st.metric(
                    "Time-Weighted Return",
                    f"{twr:+.2f}%",
                    help="Eliminates impact of cash flows"
                )

            with col3:
                if years > 0:
                    st.metric(
                        "CAGR",
                        f"{cagr:+.2f}%",
                        help="Compound Annual Growth Rate"
                    )
                else:
                    st.metric("CAGR", "N/A")

            with col4:
                st.metric(
                    "Time Period",
                    f"{days} days",
                    help=f"Approximately {years:.1f} years"
                )

            st.markdown("---")

            # Risk Metrics
            st.markdown("#### Risk Metrics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                # Color code Sharpe ratio
                sharpe_color = "normal"
                if sharpe > 1:
                    sharpe_color = "normal"  # Good
                elif sharpe < 0:
                    sharpe_color = "inverse"  # Bad

                st.metric(
                    "Sharpe Ratio",
                    f"{sharpe:.2f}",
                    help="Risk-adjusted return. >1 is good, >2 is very good"
                )

                # Add interpretation
                if sharpe > 2:
                    st.caption("Excellent risk-adjusted returns")
                elif sharpe > 1:
                    st.caption("Good risk-adjusted returns")
                elif sharpe > 0:
                    st.caption("Positive risk-adjusted returns")
                else:
                    st.caption("Negative risk-adjusted returns")

            with col2:
                st.metric(
                    "Volatility (Annual)",
                    f"{volatility:.2f}%",
                    help="Annualized standard deviation of returns"
                )

                # Add interpretation
                if volatility < 10:
                    st.caption("Low volatility")
                elif volatility < 20:
                    st.caption("Moderate volatility")
                else:
                    st.caption("High volatility")

            with col3:
                st.metric(
                    "Maximum Drawdown",
                    f"-{max_dd:.2f}%",
                    help="Largest peak-to-trough decline"
                )

                if peak_date and trough_date:
                    st.caption(f"From {peak_date} to {trough_date}")

            with col4:
                st.metric(
                    "Top Holding Weight",
                    f"{concentration['top_1_pct']:.1f}%",
                    help="Portfolio concentration in largest holding"
                )

                # Add concentration risk assessment
                if concentration['top_1_pct'] > 30:
                    st.caption("High concentration risk")
                elif concentration['top_1_pct'] > 20:
                    st.caption("Moderate concentration")
                else:
                    st.caption("Well diversified")

            st.markdown("---")

            # Concentration Analysis
            st.markdown("#### Portfolio Concentration")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Top 1 Holding",
                    f"{concentration['top_1_pct']:.1f}%"
                )

            with col2:
                st.metric(
                    "Top 3 Holdings",
                    f"{concentration['top_3_pct']:.1f}%"
                )

            with col3:
                st.metric(
                    "Top 5 Holdings",
                    f"{concentration['top_5_pct']:.1f}%"
                )

            with col4:
                hhi = concentration['herfindahl_index']
                st.metric(
                    "HHI",
                    f"{hhi:.0f}",
                    help="Herfindahl-Hirschman Index (0-10000, higher = more concentrated)"
                )

                # HHI interpretation
                if hhi < 1500:
                    st.caption("Well diversified")
                elif hhi < 2500:
                    st.caption("Moderately concentrated")
                else:
                    st.caption("Highly concentrated")

            st.markdown("---")

            # ASX 200 Benchmark Comparison
            st.markdown("#### Benchmark Comparison (ASX 200)")

            with st.spinner("Fetching ASX 200 data..."):
                try:
                    # Fetch ASX 200 data for the same period
                    start_date = history['date'].min().strftime('%Y-%m-%d')
                    asx_data = get_asx200_data(start_date)

                    if not asx_data.empty:
                        # Align dates
                        asx_df = pd.DataFrame({
                            'date': asx_data.index,
                            'Close': asx_data['Close'].values
                        })
                        asx_df['date'] = pd.to_datetime(asx_df['date'])

                        # Calculate benchmark metrics
                        asx_returns = calculate_daily_returns(asx_data['Close'])
                        asx_return_pct = ((asx_data['Close'].iloc[-1] - asx_data['Close'].iloc[0]) / asx_data['Close'].iloc[0] * 100)

                        # Calculate beta
                        beta = calculate_beta(returns, asx_returns)

                        # Display comparison metrics
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "Your Portfolio Return",
                                f"{total_return_pct:+.2f}%"
                            )

                        with col2:
                            st.metric(
                                "ASX 200 Return",
                                f"{asx_return_pct:+.2f}%"
                            )

                        with col3:
                            outperformance = total_return_pct - asx_return_pct
                            st.metric(
                                "Outperformance",
                                f"{outperformance:+.2f}%",
                                delta=f"{outperformance:+.2f}%",
                                delta_color="normal" if outperformance >= 0 else "inverse"
                            )

                        # Beta metric
                        st.markdown("---")
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "Beta",
                                f"{beta:.2f}",
                                help="Portfolio sensitivity to ASX 200. β=1 moves with market, β>1 more volatile, β<1 less volatile"
                            )

                            # Beta interpretation
                            if beta > 1.2:
                                st.caption("More volatile than market")
                            elif beta < 0.8:
                                st.caption("Less volatile than market")
                            else:
                                st.caption("Similar to market volatility")

                        with col2:
                            # Calculate alpha (excess return adjusted for beta)
                            alpha = total_return_pct - (beta * asx_return_pct)
                            st.metric(
                                "Alpha",
                                f"{alpha:+.2f}%",
                                help="Risk-adjusted excess return vs benchmark"
                            )

                        with col3:
                            # Information ratio (if we have enough data)
                            if len(returns) > 30:
                                tracking_diff = returns - asx_returns.reindex(returns.index, fill_value=0)
                                tracking_error = tracking_diff.std() * np.sqrt(252) * 100
                                st.metric(
                                    "Tracking Error",
                                    f"{tracking_error:.2f}%",
                                    help="Volatility of excess returns vs benchmark"
                                )

                        # Normalized comparison chart
                        st.markdown("---")
                        st.markdown("**Performance Comparison (Normalized to 100)**")

                        fig = create_benchmark_comparison_chart(history, asx_data)
                        st.plotly_chart(fig, use_container_width=True)

                    else:
                        st.warning("Could not fetch ASX 200 data for comparison.")

                except Exception as e:
                    st.error(f"Error comparing with ASX 200: {str(e)}")

            st.markdown("---")

            # Returns Distribution
            st.markdown("#### Returns Distribution")

            if len(returns) > 30:
                fig = create_returns_distribution(returns)
                st.plotly_chart(fig, use_container_width=True)

                # Calculate and display distribution statistics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    mean_return = returns.mean() * 100
                    st.metric("Mean Daily Return", f"{mean_return:+.3f}%")

                with col2:
                    median_return = returns.median() * 100
                    st.metric("Median Daily Return", f"{median_return:+.3f}%")

                with col3:
                    std_return = returns.std() * 100
                    st.metric("Std Dev (Daily)", f"{std_return:.3f}%")

                with col4:
                    # Calculate skewness
                    skewness = returns.skew()
                    st.metric(
                        "Skewness",
                        f"{skewness:.2f}",
                        help="<0 = left tail, >0 = right tail"
                    )

            else:
                st.info("Need at least 30 days of data to show returns distribution.")

            st.markdown("---")

            # Performance Insights
            st.markdown("#### Performance Insights")

            insights = []

            # Sharpe ratio insight
            if sharpe > 2:
                insights.append(("success", "Excellent Sharpe Ratio", f"Your Sharpe ratio of {sharpe:.2f} indicates excellent risk-adjusted returns."))
            elif sharpe < 0:
                insights.append(("error", "Negative Sharpe Ratio", f"Your Sharpe ratio of {sharpe:.2f} indicates returns below the risk-free rate."))

            # Volatility insight
            if volatility > 25:
                insights.append(("warning", "High Volatility", f"Your portfolio volatility of {volatility:.1f}% is relatively high. Consider diversification."))

            # Drawdown insight
            if max_dd > 20:
                insights.append(("warning", "Significant Drawdown", f"Your portfolio experienced a {max_dd:.1f}% drawdown from {peak_date} to {trough_date}."))

            # Concentration insight
            if concentration['top_1_pct'] > 30:
                insights.append(("warning", "Concentration Risk", f"Your largest holding represents {concentration['top_1_pct']:.1f}% of your portfolio."))

            # Benchmark comparison insight
            try:
                if outperformance > 5:
                    insights.append(("success", "Strong Outperformance", f"You've outperformed the ASX 200 by {outperformance:.1f}%!"))
                elif outperformance < -5:
                    insights.append(("info", "Underperformance", f"Your portfolio has underperformed the ASX 200 by {abs(outperformance):.1f}%."))
            except:
                pass

            # Display insights
            if insights:
                for insight_type, title, message in insights:
                    if insight_type == "success":
                        st.success(f"**{title}**: {message}")
                    elif insight_type == "warning":
                        st.warning(f"**{title}**: {message}")
                    elif insight_type == "error":
                        st.error(f"**{title}**: {message}")
                    else:
                        st.info(f"**{title}**: {message}")
            else:
                st.info("No specific performance insights at this time.")

        except Exception as e:
            st.error(f"Error calculating performance metrics: {str(e)}")
            import traceback
            st.code(traceback.format_exc())


# Run the page
if __name__ == "__main__":
    show()
