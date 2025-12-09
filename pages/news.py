"""
News Page - News Feed Integration (Placeholder)
Placeholder for future news feed integration with Alpha Vantage or similar APIs.
"""

import streamlit as st
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def show():
    """Render the News page"""
    st.title("Portfolio News Feed")
    st.markdown("### Stay updated with news about your holdings")

    st.info("News feed integration coming soon!")

    # Get portfolio holdings
    if not st.session_state.portfolio or not hasattr(st.session_state, 'portfolio'):
        st.warning("Add some holdings first to see relevant news.")
        return

    # Calculate holdings
    df = pd.DataFrame(st.session_state.portfolio)

    # Get unique tickers
    holdings = []
    for (asset_name, asset_type, ticker), group in df.groupby(['asset_name', 'asset_type', 'ticker']):
        buys = group[group['transaction_type'] == 'Buy']
        sells = group[group['transaction_type'] == 'Sell']
        quantity = buys['quantity'].sum() - sells['quantity'].sum()

        if quantity > 0 and asset_type == 'Stocks':
            holdings.append({
                'asset_name': asset_name,
                'ticker': ticker
            })

    if not holdings:
        st.warning("You don't have any stock holdings yet. Add some stocks to see relevant news!")
        return

    # Display placeholder content
    st.markdown("---")
    st.markdown("#### Your Stock Holdings")

    st.write("News will be available for the following holdings:")
    for holding in holdings:
        st.write(f"- **{holding['asset_name']}** ({holding['ticker']})")

    st.markdown("---")

    # Future integration instructions
    with st.expander("How to Enable News Feed", expanded=True):
        st.markdown("""
        ### Setting Up News Feed Integration

        To enable the news feed, you'll need to integrate with a news API. Here are recommended options:

        #### Option 1: Alpha Vantage (Recommended)
        1. Sign up for a free API key at [alphavantage.co](https://www.alphavantage.co/support/#api-key)
        2. Add your API key to the application settings
        3. The news feed will automatically fetch relevant news for your holdings

        **Features:**
        - Real-time news for stocks
        - Sentiment analysis
        - Topic classification
        - Free tier: 25 API calls per day

        #### Option 2: NewsAPI
        1. Sign up at [newsapi.org](https://newsapi.org/)
        2. Configure API key in settings
        3. Get news articles filtered by stock tickers

        **Features:**
        - Comprehensive news coverage
        - Multiple sources
        - Free tier: 100 requests per day

        #### Option 3: Yahoo Finance (via yfinance)
        - Already integrated in the application
        - No API key required
        - Limited news functionality
        - Good for basic news headlines

        ### Planned Features

        Once integrated, the news feed will include:

        - Real-time news articles for your holdings
        - Sentiment analysis (Positive/Negative/Neutral)
        - Relevance scoring
        - Filter by ticker or date
        - Price impact indicators
        - Breaking news alerts
        - Market-wide news section

        ### Implementation Status

        Current Status: **Placeholder**

        To implement:
        1. Choose a news API provider
        2. Add API key configuration
        3. Implement news fetching functions
        4. Add sentiment analysis
        5. Create news display components
        6. Add filtering and sorting options
        """)

    st.markdown("---")

    # Mock news interface
    st.markdown("#### News Feed Preview (Sample)")

    st.info("This is a preview of what the news feed will look like:")

    # Sample news items
    sample_news = [
        {
            'title': 'Market Analysis: ASX 200 Reaches New Highs',
            'source': 'Financial Times',
            'date': '2025-12-09',
            'sentiment': 'Positive',
            'summary': 'The ASX 200 index closed at record highs today, driven by strong performance in the banking and mining sectors...'
        },
        {
            'title': 'Tech Sector Outlook for 2025',
            'source': 'Bloomberg',
            'date': '2025-12-08',
            'sentiment': 'Neutral',
            'summary': 'Analysts predict mixed performance for tech stocks in the coming year, with AI and cloud computing showing promise...'
        },
        {
            'title': 'Australian Dollar Strengthens Against USD',
            'source': 'Reuters',
            'date': '2025-12-08',
            'sentiment': 'Positive',
            'summary': 'The AUD gained 0.5% against the USD following positive economic data and rising commodity prices...'
        }
    ]

    for news in sample_news:
        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"### {news['title']}")
                st.caption(f"{news['source']} | {news['date']}")
                st.write(news['summary'])

            with col2:
                sentiment_color = {
                    'Positive': 'green',
                    'Negative': 'red',
                    'Neutral': 'gray'
                }
                color = sentiment_color.get(news['sentiment'], 'gray')
                st.markdown(f"**Sentiment**")
                st.markdown(f":{color}[{news['sentiment']}]")

            st.divider()

    # Settings placeholder
    st.markdown("---")
    st.markdown("#### News Feed Settings")

    with st.expander("Configure News Preferences"):
        st.markdown("**API Configuration**")

        api_provider = st.selectbox(
            "News API Provider",
            ["None Selected", "Alpha Vantage", "NewsAPI", "Yahoo Finance"]
        )

        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="Enter your API key here",
            disabled=True
        )

        st.markdown("**Display Preferences**")

        news_count = st.slider(
            "Number of articles to display",
            min_value=5,
            max_value=50,
            value=10
        )

        sentiment_filter = st.multiselect(
            "Filter by sentiment",
            ["Positive", "Neutral", "Negative"],
            default=["Positive", "Neutral", "Negative"]
        )

        auto_refresh = st.checkbox("Auto-refresh news feed", value=False)

        if auto_refresh:
            refresh_interval = st.slider(
                "Refresh interval (minutes)",
                min_value=5,
                max_value=60,
                value=15
            )

        st.info("Settings will be saved once news integration is implemented.")

    # Market news section
    st.markdown("---")
    st.markdown("#### General Market News")

    st.write("""
    In addition to news about your specific holdings, you'll also see:

    - ASX market updates
    - Economic indicators
    - Sector performance news
    - Global market movements
    - Regulatory changes
    - Dividend announcements
    """)


# Run the page
if __name__ == "__main__":
    show()
