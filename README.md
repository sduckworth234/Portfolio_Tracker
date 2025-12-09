# Portfolio Tracker

A personal finance portfolio tracker built with Streamlit for tracking and visualizing your investment portfolio.

## Features

- **Multi-Asset Support**: Track stocks, crypto, cash, bonds, real estate, and other assets
- **Transaction Management**: Record buy and sell transactions with dates and prices
- **Portfolio Analytics**: View total portfolio value, number of assets, and asset allocation
- **Interactive Visualizations**:
  - Pie charts for portfolio allocation by asset and type
  - Bar charts for holdings value
  - Timeline scatter plot for transaction history
- **Data Persistence**: All data saved locally in JSON format
- **Clean Interface**: Intuitive Streamlit UI with organized tabs

## Installation

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/Portfolio_Tracker.git
cd Portfolio_Tracker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:
```bash
streamlit run portfolio_tracker.py
```

The app will open in your browser at `http://localhost:8501`

### Adding Transactions

1. Use the sidebar to add buy or sell transactions
2. Enter asset name, type, quantity, price, and date
3. Click "Add Transaction" to save

### Viewing Your Portfolio

- **Portfolio Overview**: See total value and allocation charts
- **Holdings**: View current positions and their values
- **Transaction History**: Review all past transactions with timeline visualization

## Deployment

### Deploy to Streamlit Cloud

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repository and branch
5. Click "Deploy"

Your app will be live at a public URL!

## Tech Stack

- **Streamlit**: Web framework
- **Pandas**: Data manipulation
- **Plotly**: Interactive visualizations
- **Python 3.7+**

## Data Storage

Portfolio data is stored locally in `portfolio_data.json`. This file is excluded from git via `.gitignore` to protect your financial data.

## License

MIT License - feel free to use and modify as needed.
