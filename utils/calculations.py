"""
Financial calculations module for portfolio analytics.
Includes Time-Weighted Returns, Sharpe Ratio, Volatility, Beta, and other metrics.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple


def calculate_time_weighted_return(portfolio_values: pd.DataFrame) -> float:
    """
    Calculate Time-Weighted Return (TWR) for the portfolio.
    TWR eliminates the impact of cash flows, measuring pure investment performance.

    Args:
        portfolio_values: DataFrame with columns ['date', 'value', 'cash_flow']
                         cash_flow is positive for deposits, negative for withdrawals

    Returns:
        TWR as a percentage
    """
    if portfolio_values.empty or len(portfolio_values) < 2:
        return 0.0

    # Sort by date
    df = portfolio_values.sort_values('date').copy()

    # Calculate holding period returns
    holding_returns = []

    for i in range(1, len(df)):
        prev_value = df.iloc[i-1]['value']
        current_value = df.iloc[i]['value']
        cash_flow = df.iloc[i].get('cash_flow', 0)

        # Adjust for cash flows
        # Return = (Ending Value - Cash Flow) / Beginning Value - 1
        if prev_value > 0:
            hpr = (current_value - cash_flow) / prev_value - 1
            holding_returns.append(1 + hpr)

    if not holding_returns:
        return 0.0

    # Compound the returns
    twr = np.prod(holding_returns) - 1
    return twr * 100  # Return as percentage


def calculate_simple_return(initial_investment: float, current_value: float) -> float:
    """
    Calculate simple return percentage.

    Args:
        initial_investment: Total amount invested
        current_value: Current portfolio value

    Returns:
        Simple return as a percentage
    """
    if initial_investment <= 0:
        return 0.0

    return ((current_value - initial_investment) / initial_investment) * 100


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.043) -> float:
    """
    Calculate Sharpe Ratio - measures risk-adjusted returns.

    Args:
        returns: Series of period returns (daily, monthly, etc.)
        risk_free_rate: Annual risk-free rate (default: 4.3% - Australian 10-year bond yield)

    Returns:
        Annualized Sharpe Ratio
    """
    if returns.empty or len(returns) < 2:
        return 0.0

    # Calculate excess returns
    mean_return = returns.mean()
    std_return = returns.std()

    if std_return == 0:
        return 0.0

    # Assuming daily returns, annualize
    # Annual return = mean * 252 (trading days)
    # Annual std = std * sqrt(252)
    periods_per_year = 252
    annualized_return = mean_return * periods_per_year
    annualized_std = std_return * np.sqrt(periods_per_year)

    sharpe = (annualized_return - risk_free_rate) / annualized_std
    return sharpe


def calculate_volatility(returns: pd.Series, annualize: bool = True) -> float:
    """
    Calculate portfolio volatility (standard deviation of returns).

    Args:
        returns: Series of period returns
        annualize: If True, annualize the volatility

    Returns:
        Volatility as a percentage
    """
    if returns.empty or len(returns) < 2:
        return 0.0

    volatility = returns.std()

    if annualize:
        # Assume daily returns, annualize using sqrt(252)
        volatility *= np.sqrt(252)

    return volatility * 100  # Return as percentage


def calculate_beta(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """
    Calculate Beta - measures portfolio sensitivity to market movements.
    Beta > 1: More volatile than market
    Beta = 1: Moves with market
    Beta < 1: Less volatile than market

    Args:
        portfolio_returns: Series of portfolio returns
        benchmark_returns: Series of benchmark (ASX200) returns

    Returns:
        Beta coefficient
    """
    if portfolio_returns.empty or benchmark_returns.empty:
        return 0.0

    # Align the series
    df = pd.DataFrame({
        'portfolio': portfolio_returns,
        'benchmark': benchmark_returns
    }).dropna()

    if len(df) < 2:
        return 0.0

    # Calculate covariance and variance
    covariance = df['portfolio'].cov(df['benchmark'])
    benchmark_variance = df['benchmark'].var()

    if benchmark_variance == 0:
        return 0.0

    beta = covariance / benchmark_variance
    return beta


def calculate_maximum_drawdown(portfolio_values: pd.Series) -> Tuple[float, str, str]:
    """
    Calculate Maximum Drawdown - largest peak-to-trough decline.

    Args:
        portfolio_values: Series of portfolio values over time (indexed by date)

    Returns:
        Tuple of (max_drawdown_pct, peak_date, trough_date)
    """
    if portfolio_values.empty or len(portfolio_values) < 2:
        return 0.0, None, None

    # Calculate cumulative maximum (running peak)
    cumulative_max = portfolio_values.cummax()

    # Calculate drawdown at each point
    drawdown = (portfolio_values - cumulative_max) / cumulative_max

    # Find maximum drawdown
    max_drawdown = drawdown.min()

    if pd.isna(max_drawdown) or max_drawdown == 0:
        return 0.0, None, None

    # Find the trough date (date of maximum drawdown)
    trough_date = drawdown.idxmin()

    # Find the peak date (last peak before the trough)
    peak_date = portfolio_values[:trough_date].idxmax()

    return abs(max_drawdown) * 100, str(peak_date)[:10], str(trough_date)[:10]


def calculate_portfolio_concentration(holdings_df: pd.DataFrame, value_column: str = 'current_value') -> Dict:
    """
    Calculate portfolio concentration metrics.

    Args:
        holdings_df: DataFrame with holdings and their values
        value_column: Name of the column containing values

    Returns:
        Dictionary with concentration metrics
    """
    if holdings_df.empty:
        return {
            'top_1_pct': 0.0,
            'top_3_pct': 0.0,
            'top_5_pct': 0.0,
            'herfindahl_index': 0.0
        }

    # Sort by value descending
    sorted_holdings = holdings_df.sort_values(value_column, ascending=False)
    total_value = sorted_holdings[value_column].sum()

    if total_value == 0:
        return {
            'top_1_pct': 0.0,
            'top_3_pct': 0.0,
            'top_5_pct': 0.0,
            'herfindahl_index': 0.0
        }

    # Calculate percentages
    top_1 = sorted_holdings[value_column].iloc[0] / total_value * 100 if len(sorted_holdings) >= 1 else 0
    top_3 = sorted_holdings[value_column].iloc[:3].sum() / total_value * 100 if len(sorted_holdings) >= 3 else sorted_holdings[value_column].sum() / total_value * 100
    top_5 = sorted_holdings[value_column].iloc[:5].sum() / total_value * 100 if len(sorted_holdings) >= 5 else sorted_holdings[value_column].sum() / total_value * 100

    # Herfindahl-Hirschman Index (HHI) - measures concentration
    # HHI = sum of squared market shares (0-10000, higher = more concentrated)
    market_shares = (sorted_holdings[value_column] / total_value * 100) ** 2
    hhi = market_shares.sum()

    return {
        'top_1_pct': top_1,
        'top_3_pct': top_3,
        'top_5_pct': top_5,
        'herfindahl_index': hhi
    }


def calculate_ytd_return(portfolio_history: pd.DataFrame, value_column: str = 'value') -> float:
    """
    Calculate Year-to-Date return.

    Args:
        portfolio_history: DataFrame with date index and value column
        value_column: Name of the value column

    Returns:
        YTD return as a percentage
    """
    if portfolio_history.empty:
        return 0.0

    df = portfolio_history.sort_index()
    current_date = datetime.now()
    current_year = current_date.year

    # Find first value of current year
    year_start_date = datetime(current_year, 1, 1)

    # Get values at year start and current
    year_start_value = None
    current_value = df[value_column].iloc[-1]

    # Find the closest date to year start
    for date, row in df.iterrows():
        if date >= year_start_date:
            year_start_value = row[value_column]
            break

    if year_start_value is None or year_start_value == 0:
        return 0.0

    ytd_return = ((current_value - year_start_value) / year_start_value) * 100
    return ytd_return


def calculate_daily_returns(prices: pd.Series) -> pd.Series:
    """
    Calculate daily returns from price series.

    Args:
        prices: Series of prices indexed by date

    Returns:
        Series of daily returns (percentage)
    """
    if prices.empty or len(prices) < 2:
        return pd.Series()

    returns = prices.pct_change().dropna()
    return returns


def calculate_cagr(initial_value: float, final_value: float, years: float) -> float:
    """
    Calculate Compound Annual Growth Rate (CAGR).

    Args:
        initial_value: Starting portfolio value
        final_value: Ending portfolio value
        years: Time period in years (can be fractional)

    Returns:
        CAGR as a percentage
    """
    if initial_value <= 0 or years <= 0:
        return 0.0

    cagr = ((final_value / initial_value) ** (1 / years) - 1) * 100
    return cagr
