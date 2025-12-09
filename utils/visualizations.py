"""
Plotly visualization functions for portfolio dashboard.
All charts are interactive with zoom, pan, and hover tooltips.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime


def create_portfolio_value_chart(history_df: pd.DataFrame, transactions: list = None) -> go.Figure:
    """
    Create interactive portfolio value timeline with transaction markers.

    Args:
        history_df: DataFrame with columns ['date', 'value']
        transactions: Optional list of transactions to mark on chart

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Main portfolio value line
    fig.add_trace(go.Scatter(
        x=history_df['date'],
        y=history_df['value'],
        mode='lines',
        name='Portfolio Value',
        line=dict(color='#2E86AB', width=2.5),
        hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br>' +
                      '<b>Value:</b> A$%{y:,.2f}<br>' +
                      '<extra></extra>'
    ))

    # Add transaction markers if provided
    if transactions:
        df_trans = pd.DataFrame(transactions)
        df_trans['date'] = pd.to_datetime(df_trans['date'])

        # Buy transactions (green triangles up)
        buys = df_trans[df_trans['transaction_type'] == 'Buy']
        if not buys.empty:
            # Merge with history to get values at transaction dates
            buy_values = []
            for _, txn in buys.iterrows():
                matching_date = history_df[history_df['date'] == txn['date']]
                if not matching_date.empty:
                    buy_values.append(matching_date['value'].iloc[0])
                else:
                    # Find closest date
                    closest_idx = (history_df['date'] - txn['date']).abs().idxmin()
                    buy_values.append(history_df.loc[closest_idx, 'value'])

            fig.add_trace(go.Scatter(
                x=buys['date'],
                y=buy_values,
                mode='markers',
                name='Buy',
                marker=dict(
                    symbol='triangle-up',
                    size=12,
                    color='#06D6A0',
                    line=dict(color='white', width=1)
                ),
                hovertemplate='<b>BUY</b><br>' +
                              '<b>Date:</b> %{x|%Y-%m-%d}<br>' +
                              '<b>Asset:</b> ' + buys['asset_name'] + '<br>' +
                              '<b>Amount:</b> A$%{customdata:,.2f}<br>' +
                              '<extra></extra>',
                customdata=buys['total_value']
            ))

        # Sell transactions (red triangles down)
        sells = df_trans[df_trans['transaction_type'] == 'Sell']
        if not sells.empty:
            sell_values = []
            for _, txn in sells.iterrows():
                matching_date = history_df[history_df['date'] == txn['date']]
                if not matching_date.empty:
                    sell_values.append(matching_date['value'].iloc[0])
                else:
                    closest_idx = (history_df['date'] - txn['date']).abs().idxmin()
                    sell_values.append(history_df.loc[closest_idx, 'value'])

            fig.add_trace(go.Scatter(
                x=sells['date'],
                y=sell_values,
                mode='markers',
                name='Sell',
                marker=dict(
                    symbol='triangle-down',
                    size=12,
                    color='#EF476F',
                    line=dict(color='white', width=1)
                ),
                hovertemplate='<b>SELL</b><br>' +
                              '<b>Date:</b> %{x|%Y-%m-%d}<br>' +
                              '<b>Asset:</b> ' + sells['asset_name'] + '<br>' +
                              '<b>Amount:</b> A$%{customdata:,.2f}<br>' +
                              '<extra></extra>',
                customdata=sells['total_value']
            ))

    # Layout with range selector
    fig.update_layout(
        title='Portfolio Value Over Time',
        xaxis_title='Date',
        yaxis_title='Value (AUD)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="ALL")
                ]),
                bgcolor='#E8E8E8',
                activecolor='#2E86AB'
            ),
            rangeslider=dict(visible=False),
            type='date'
        ),
        yaxis=dict(
            tickprefix='A$',
            tickformat=',.0f'
        )
    )

    return fig


def create_treemap(holdings_df: pd.DataFrame) -> go.Figure:
    """
    Create interactive treemap showing holdings sized by value, colored by gain/loss.

    Args:
        holdings_df: DataFrame with holdings data

    Returns:
        Plotly Figure object
    """
    if holdings_df.empty:
        return go.Figure()

    # Prepare data
    df = holdings_df.copy()
    df['label'] = df['asset_name'] + '<br>' + df['gain_loss_pct'].apply(lambda x: f'{x:+.1f}%')

    # Create color scale based on gain/loss percentage
    max_abs = max(abs(df['gain_loss_pct'].min()), abs(df['gain_loss_pct'].max()))
    colorscale = [
        [0, '#EF476F'],      # Red (loss)
        [0.5, '#FFD166'],    # Yellow (neutral)
        [1, '#06D6A0']       # Green (gain)
    ]

    fig = go.Figure(go.Treemap(
        labels=df['asset_name'],
        parents=['Portfolio'] * len(df),
        values=df['current_value'],
        text=df['label'],
        textposition='middle center',
        marker=dict(
            colors=df['gain_loss_pct'],
            colorscale=colorscale,
            cmid=0,
            colorbar=dict(
                title='Gain/Loss %',
                ticksuffix='%'
            ),
            line=dict(color='white', width=2)
        ),
        hovertemplate='<b>%{label}</b><br>' +
                      'Value: A$%{value:,.2f}<br>' +
                      '<extra></extra>'
    ))

    fig.update_layout(
        title='Holdings Treemap (Size = Value, Color = Gain/Loss %)',
        height=500
    )

    return fig


def create_sunburst_chart(holdings_df: pd.DataFrame) -> go.Figure:
    """
    Create sunburst chart showing hierarchical allocation.
    Structure: Portfolio > Asset Type > Individual Holdings

    Args:
        holdings_df: DataFrame with holdings data

    Returns:
        Plotly Figure object
    """
    if holdings_df.empty:
        return go.Figure()

    # Prepare hierarchical data
    data = []

    # Level 1: Portfolio (root)
    total_value = holdings_df['current_value'].sum()

    # Level 2: Asset Types
    for asset_type in holdings_df['asset_type'].unique():
        type_holdings = holdings_df[holdings_df['asset_type'] == asset_type]
        type_value = type_holdings['current_value'].sum()

        # Level 3: Individual Holdings
        for _, holding in type_holdings.iterrows():
            data.append({
                'labels': holding['asset_name'],
                'parents': asset_type,
                'values': holding['current_value'],
                'gain_loss_pct': holding['gain_loss_pct']
            })

        # Add asset type node
        data.append({
            'labels': asset_type,
            'parents': 'Portfolio',
            'values': type_value,
            'gain_loss_pct': (type_holdings['gain_loss'].sum() / type_holdings['total_invested'].sum() * 100)
        })

    # Add root node
    data.append({
        'labels': 'Portfolio',
        'parents': '',
        'values': total_value,
        'gain_loss_pct': 0
    })

    df_sunburst = pd.DataFrame(data)

    fig = go.Figure(go.Sunburst(
        labels=df_sunburst['labels'],
        parents=df_sunburst['parents'],
        values=df_sunburst['values'],
        branchvalues='total',
        marker=dict(
            colors=df_sunburst['gain_loss_pct'],
            colorscale=[
                [0, '#EF476F'],
                [0.5, '#FFD166'],
                [1, '#06D6A0']
            ],
            cmid=0,
            line=dict(color='white', width=2)
        ),
        hovertemplate='<b>%{label}</b><br>' +
                      'Value: A$%{value:,.2f}<br>' +
                      'Gain/Loss: %{color:+.1f}%<br>' +
                      '<extra></extra>'
    ))

    fig.update_layout(
        title='Portfolio Hierarchy (Type > Holdings)',
        height=500
    )

    return fig


def create_correlation_heatmap(correlation_df: pd.DataFrame) -> go.Figure:
    """
    Create correlation heatmap for stock holdings.

    Args:
        correlation_df: Correlation matrix DataFrame

    Returns:
        Plotly Figure object
    """
    if correlation_df.empty:
        return go.Figure()

    fig = go.Figure(data=go.Heatmap(
        z=correlation_df.values,
        x=correlation_df.columns,
        y=correlation_df.index,
        colorscale='RdBu',
        zmid=0,
        zmin=-1,
        zmax=1,
        text=correlation_df.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title='Correlation'),
        hovertemplate='%{x} vs %{y}<br>Correlation: %{z:.3f}<extra></extra>'
    ))

    fig.update_layout(
        title='Stock Correlation Matrix',
        xaxis_title='',
        yaxis_title='',
        height=500,
        width=600
    )

    return fig


def create_benchmark_comparison_chart(portfolio_history: pd.DataFrame,
                                      benchmark_history: pd.DataFrame) -> go.Figure:
    """
    Create normalized comparison chart (both starting at 100).

    Args:
        portfolio_history: DataFrame with date and value columns
        benchmark_history: DataFrame with date and Close columns

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Normalize portfolio (start at 100)
    portfolio_norm = portfolio_history.copy()
    portfolio_norm['normalized'] = (portfolio_norm['value'] / portfolio_norm['value'].iloc[0]) * 100

    # Normalize benchmark (start at 100)
    benchmark_norm = benchmark_history.copy()
    benchmark_norm['normalized'] = (benchmark_norm['Close'] / benchmark_norm['Close'].iloc[0]) * 100

    # Plot portfolio
    fig.add_trace(go.Scatter(
        x=portfolio_norm['date'],
        y=portfolio_norm['normalized'],
        mode='lines',
        name='Your Portfolio',
        line=dict(color='#2E86AB', width=2.5),
        hovertemplate='<b>Portfolio</b><br>' +
                      'Date: %{x|%Y-%m-%d}<br>' +
                      'Value: %{y:.2f}<br>' +
                      '<extra></extra>'
    ))

    # Plot benchmark
    fig.add_trace(go.Scatter(
        x=benchmark_norm.index,
        y=benchmark_norm['normalized'],
        mode='lines',
        name='ASX 200',
        line=dict(color='#F18F01', width=2.5, dash='dash'),
        hovertemplate='<b>ASX 200</b><br>' +
                      'Date: %{x|%Y-%m-%d}<br>' +
                      'Value: %{y:.2f}<br>' +
                      '<extra></extra>'
    ))

    fig.update_layout(
        title='Portfolio vs ASX 200 Performance (Normalized to 100)',
        xaxis_title='Date',
        yaxis_title='Normalized Value',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        xaxis=dict(type='date'),
        yaxis=dict(tickformat='.1f')
    )

    return fig


def create_sector_performance_chart(holdings_df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart showing sector performance.

    Args:
        holdings_df: DataFrame with holdings and sector information

    Returns:
        Plotly Figure object
    """
    if holdings_df.empty or 'sector' not in holdings_df.columns:
        return go.Figure()

    # Group by sector
    sector_data = holdings_df.groupby('sector').agg({
        'current_value': 'sum',
        'gain_loss': 'sum',
        'total_invested': 'sum'
    }).reset_index()

    sector_data['gain_loss_pct'] = (sector_data['gain_loss'] / sector_data['total_invested'] * 100)
    sector_data = sector_data.sort_values('gain_loss_pct', ascending=True)

    # Color based on positive/negative
    colors = ['#06D6A0' if x >= 0 else '#EF476F' for x in sector_data['gain_loss_pct']]

    fig = go.Figure(go.Bar(
        x=sector_data['gain_loss_pct'],
        y=sector_data['sector'],
        orientation='h',
        marker=dict(color=colors),
        text=sector_data['gain_loss_pct'].apply(lambda x: f'{x:+.1f}%'),
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>' +
                      'Return: %{x:+.2f}%<br>' +
                      'Value: A$%{customdata:,.2f}<br>' +
                      '<extra></extra>',
        customdata=sector_data['current_value']
    ))

    fig.update_layout(
        title='Sector Performance',
        xaxis_title='Return (%)',
        yaxis_title='',
        height=400,
        template='plotly_white',
        showlegend=False,
        xaxis=dict(ticksuffix='%')
    )

    return fig


def create_holdings_performance_bars(holdings_df: pd.DataFrame) -> go.Figure:
    """
    Create grouped bar chart comparing invested vs current value.

    Args:
        holdings_df: DataFrame with holdings data

    Returns:
        Plotly Figure object
    """
    if holdings_df.empty:
        return go.Figure()

    df = holdings_df.sort_values('current_value', ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Invested',
        x=df['asset_name'],
        y=df['total_invested'],
        marker_color='#A0C4FF'
    ))

    fig.add_trace(go.Bar(
        name='Current Value',
        x=df['asset_name'],
        y=df['current_value'],
        marker_color='#06D6A0'
    ))

    fig.update_layout(
        title='Investment vs Current Value by Asset',
        xaxis_title='Asset',
        yaxis_title='Value (AUD)',
        barmode='group',
        template='plotly_white',
        height=400,
        yaxis=dict(
            tickprefix='A$',
            tickformat=',.0f'
        )
    )

    return fig


def create_allocation_pie(holdings_df: pd.DataFrame, group_by: str = 'asset_name') -> go.Figure:
    """
    Create interactive pie chart for allocation.

    Args:
        holdings_df: DataFrame with holdings data
        group_by: Column to group by ('asset_name', 'asset_type', 'sector')

    Returns:
        Plotly Figure object
    """
    if holdings_df.empty:
        return go.Figure()

    if group_by == 'asset_name':
        data = holdings_df
        values = data['current_value']
        labels = data['asset_name']
    else:
        data = holdings_df.groupby(group_by)['current_value'].sum().reset_index()
        values = data['current_value']
        labels = data[group_by]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(
            line=dict(color='white', width=2)
        ),
        hovertemplate='<b>%{label}</b><br>' +
                      'Value: A$%{value:,.2f}<br>' +
                      'Percentage: %{percent}<br>' +
                      '<extra></extra>'
    )])

    title_map = {
        'asset_name': 'Portfolio Allocation by Asset',
        'asset_type': 'Portfolio Allocation by Type',
        'sector': 'Portfolio Allocation by Sector'
    }

    fig.update_layout(
        title=title_map.get(group_by, 'Portfolio Allocation'),
        height=400,
        showlegend=True
    )

    return fig


def create_returns_distribution(returns_series: pd.Series) -> go.Figure:
    """
    Create histogram showing distribution of returns.

    Args:
        returns_series: Series of daily returns

    Returns:
        Plotly Figure object
    """
    if returns_series.empty:
        return go.Figure()

    fig = go.Figure(data=[go.Histogram(
        x=returns_series * 100,  # Convert to percentage
        nbinsx=50,
        marker_color='#2E86AB',
        opacity=0.7,
        hovertemplate='Return Range: %{x:.2f}%<br>' +
                      'Frequency: %{y}<br>' +
                      '<extra></extra>'
    )])

    fig.update_layout(
        title='Distribution of Daily Returns',
        xaxis_title='Daily Return (%)',
        yaxis_title='Frequency',
        template='plotly_white',
        height=400,
        showlegend=False
    )

    return fig
