"""
Data fetching utilities with caching for portfolio tracker.
Handles stock data, historical prices, forex rates, and benchmark data.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_live_price(ticker: str) -> Optional[float]:
    """
    Fetch current live price for a ticker symbol.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'CBA.AX', 'BTC-USD')

    Returns:
        Current price or None if fetch fails
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period='1d')
        if not data.empty:
            return data['Close'].iloc[-1]
        return None
    except Exception as e:
        st.warning(f"Failed to fetch price for {ticker}: {str(e)}")
        return None


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_historical_price(ticker: str, date) -> Optional[float]:
    """
    Fetch historical price for a ticker on a specific date.

    Args:
        ticker: Stock ticker symbol
        date: Date to fetch price for (datetime.date or datetime.datetime)

    Returns:
        Historical price or None if not available
    """
    try:
        # Convert date to datetime if needed
        if isinstance(date, datetime):
            date_obj = date.date()
        else:
            date_obj = date

        # Convert to datetime for arithmetic
        dt = datetime.combine(date_obj, datetime.min.time())

        # Add buffer days to ensure we get data
        start_date = (dt - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = (dt + timedelta(days=1)).strftime('%Y-%m-%d')

        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date)

        if not data.empty:
            # Get the closest date
            closest_date = min(data.index, key=lambda x: abs(x.date() - date_obj))
            return data.loc[closest_date, 'Close']
        return None
    except Exception as e:
        # Only show error once per ticker to avoid spam
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_forex_rate(from_currency: str = 'USD', to_currency: str = 'AUD') -> float:
    """
    Get forex conversion rate.

    Args:
        from_currency: Source currency code
        to_currency: Target currency code

    Returns:
        Conversion rate (defaults to 1.52 if fetch fails)
    """
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


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_stock_historical_data(ticker: str, start_date: str, end_date: str = None) -> pd.DataFrame:
    """
    Fetch historical OHLCV data for a ticker.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (defaults to today)

    Returns:
        DataFrame with historical data (Date, Open, High, Low, Close, Volume)
    """
    try:
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date)

        return data
    except Exception as e:
        st.warning(f"Failed to fetch historical data for {ticker}: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_asx200_data(start_date: str, end_date: str = None) -> pd.DataFrame:
    """
    Fetch ASX200 benchmark data using STW.AX (SPDR S&P/ASX 200 ETF).

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (defaults to today)

    Returns:
        DataFrame with ASX200 data
    """
    return get_stock_historical_data('STW.AX', start_date, end_date)


@st.cache_data(ttl=86400)  # Cache for 24 hours (stock info changes slowly)
def get_stock_info(ticker: str) -> dict:
    """
    Fetch detailed stock information.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary with stock info (sector, industry, market cap, etc.)
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', None),
            'dividend_yield': info.get('dividendYield', None),
            'beta': info.get('beta', None),
            '52w_high': info.get('fiftyTwoWeekHigh', None),
            '52w_low': info.get('fiftyTwoWeekLow', None)
        }
    except Exception as e:
        # Return default values instead of warning to avoid spam
        # Rate limiting is common with stock.info calls
        return {
            'sector': 'Unknown',
            'industry': 'Unknown',
            'market_cap': 0,
            'pe_ratio': None,
            'dividend_yield': None,
            'beta': None,
            '52w_high': None,
            '52w_low': None
        }


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_multiple_stocks_data(tickers: list, start_date: str, end_date: str = None) -> dict:
    """
    Fetch historical data for multiple tickers efficiently.

    Args:
        tickers: List of ticker symbols
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (defaults to today)

    Returns:
        Dictionary mapping ticker to DataFrame
    """
    result = {}

    for ticker in tickers:
        data = get_stock_historical_data(ticker, start_date, end_date)
        if not data.empty:
            result[ticker] = data

    return result


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_market_indicators() -> dict:
    """
    Fetch various market indicators for dashboard display.

    Returns:
        Dictionary with market indicators
    """
    indicators = {}

    try:
        # ASX200 current data
        asx200 = yf.Ticker('STW.AX')
        asx_data = asx200.history(period='5d')
        if len(asx_data) >= 2:
            current = asx_data['Close'].iloc[-1]
            previous = asx_data['Close'].iloc[-2]
            indicators['asx200_price'] = current
            indicators['asx200_change'] = current - previous
            indicators['asx200_change_pct'] = (current - previous) / previous * 100

        # VIX (market volatility index)
        vix = yf.Ticker('^VIX')
        vix_data = vix.history(period='1d')
        if not vix_data.empty:
            indicators['vix'] = vix_data['Close'].iloc[-1]

        # USD/AUD
        indicators['usd_aud'] = get_forex_rate('USD', 'AUD')

    except Exception as e:
        st.warning(f"Failed to fetch some market indicators: {str(e)}")

    return indicators


def calculate_portfolio_history(transactions: list, end_date: datetime = None) -> pd.DataFrame:
    """
    Calculate daily portfolio value history from transaction data.

    Args:
        transactions: List of transaction dictionaries
        end_date: End date for history (defaults to today)

    Returns:
        DataFrame with columns: date, value, cash_flow, daily_return
    """
    if not transactions:
        return pd.DataFrame()

    if end_date is None:
        end_date = datetime.now()

    # Convert transactions to DataFrame
    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])

    # Get earliest transaction date
    start_date = df['date'].min()

    # Create date range
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    # Initialize portfolio history
    history = []

    for date in date_range:
        # Get transactions up to this date
        past_transactions = df[df['date'] <= date]

        if past_transactions.empty:
            continue

        # Calculate holdings at this date
        holdings = {}
        for _, txn in past_transactions.iterrows():
            ticker = txn.get('ticker', txn['asset_name'])
            quantity_change = txn['quantity'] if txn['transaction_type'] == 'Buy' else -txn['quantity']

            if ticker not in holdings:
                holdings[ticker] = {
                    'quantity': 0,
                    'asset_type': txn['asset_type']
                }

            holdings[ticker]['quantity'] += quantity_change

        # Get prices for this date and calculate value
        total_value = 0
        for ticker, holding in holdings.items():
            if holding['quantity'] > 0:
                # For stocks/crypto, fetch historical price
                if holding['asset_type'] in ['Stocks', 'Crypto']:
                    price = get_historical_price(ticker, date.to_pydatetime())
                    if price:
                        total_value += holding['quantity'] * price
                else:
                    # For other assets, use last transaction price
                    last_txn = past_transactions[past_transactions.get('ticker', past_transactions['asset_name']) == ticker].iloc[-1]
                    total_value += holding['quantity'] * last_txn['price']

        # Detect cash flows on this date
        cash_flow = 0
        same_day_txns = past_transactions[past_transactions['date'] == date]
        for _, txn in same_day_txns.iterrows():
            if txn['transaction_type'] == 'Buy':
                cash_flow += txn['total_value']  # Cash in
            else:
                cash_flow -= txn['total_value']  # Cash out

        history.append({
            'date': date,
            'value': total_value,
            'cash_flow': cash_flow
        })

    history_df = pd.DataFrame(history)

    # Calculate daily returns
    if not history_df.empty:
        history_df['daily_return'] = history_df['value'].pct_change()

    return history_df


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_benchmark_data(benchmark_name: str, start_date: str, end_date: str = None) -> pd.DataFrame:
    """
    Fetch benchmark data for comparison.

    Args:
        benchmark_name: Name of benchmark ('S&P 500', 'NASDAQ', 'ASX 200', or custom ticker)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (defaults to today)

    Returns:
        DataFrame with benchmark historical data
    """
    # Map common benchmark names to tickers
    benchmark_tickers = {
        'S&P 500': '^GSPC',
        'NASDAQ': '^IXIC',
        'ASX 200': '^AXJO',
        'ASX 200 ETF': 'STW.AX',
        'VTS': 'VTS.AX',
        'VGS': 'VGS.AX'
    }

    ticker = benchmark_tickers.get(benchmark_name, benchmark_name)
    return get_stock_historical_data(ticker, start_date, end_date)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_correlation_matrix(tickers: list, start_date: str, end_date: str = None) -> pd.DataFrame:
    """
    Calculate correlation matrix for multiple stocks.

    Args:
        tickers: List of ticker symbols
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Correlation matrix DataFrame
    """
    try:
        data_dict = get_multiple_stocks_data(tickers, start_date, end_date)

        # Create DataFrame with closing prices
        prices = pd.DataFrame()
        for ticker, data in data_dict.items():
            if not data.empty:
                prices[ticker] = data['Close']

        if prices.empty:
            return pd.DataFrame()

        # Calculate daily returns
        returns = prices.pct_change().dropna()

        # Calculate correlation
        correlation = returns.corr()

        return correlation

    except Exception as e:
        st.warning(f"Failed to calculate correlation matrix: {str(e)}")
        return pd.DataFrame()
