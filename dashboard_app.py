"""
Delaynomics Dashboard - Plotly Dash Implementation
Interactive web dashboard for airline delay economics analysis
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================================
# DATA LOADING
# ============================================================================

def load_data():
    """Load pre-computed summary data from outputs folder"""
    try:
        airline_summary = pd.read_csv('outputs/airline_summary.csv')
        airport_summary = pd.read_csv('outputs/airport_summary.csv')

        # Check if full dataset exists
        full_data_path = Path('outputs/full_dataset_for_tableau.csv')
        if full_data_path.exists():
            full_data = pd.read_csv(full_data_path)
        else:
            full_data = None

        return airline_summary, airport_summary, full_data

    except FileNotFoundError as e:
        print("❌ Error: CSV files not found in outputs/ directory")
        print("   Run notebooks/analysis.ipynb first to generate the data")
        raise e

# Load data
airline_df, airport_df, flights_df = load_data()

# ============================================================================
# DASH APP SETUP
# ============================================================================

app = dash.Dash(
    __name__,
    title="Delaynomics Dashboard",
    update_title="Loading...",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# ============================================================================
# LAYOUT
# ============================================================================

app.layout = html.Div([
    # Header
    html.Div([
        html.H1("✈️ Delaynomics Dashboard", className="header-title"),
        html.P(
            "Which airlines deliver the best value for money?",
            className="header-subtitle"
        ),
    ], className="header"),

    # KPI Cards
    html.Div([
        html.Div([
            html.H4("🏆 Best Carrier"),
            html.H2(airline_df.iloc[0]['Carrier'], id="best-carrier"),
            html.P(f"${airline_df.iloc[0]['avg_cost_per_mile']:.2f} per mile"),
        ], className="kpi-card kpi-green"),

        html.Div([
            html.H4("⚠️ Worst Carrier"),
            html.H2(airline_df.iloc[-1]['Carrier'], id="worst-carrier"),
            html.P(f"${airline_df.iloc[-1]['avg_cost_per_mile']:.2f} per mile"),
        ], className="kpi-card kpi-red"),

        html.Div([
            html.H4("💰 Avg Delay Cost"),
            html.H2(f"${airline_df['avg_delay_cost'].mean():.0f}", id="avg-cost"),
            html.P("per delayed flight"),
        ], className="kpi-card kpi-blue"),

        html.Div([
            html.H4("📊 Total Flights"),
            html.H2(f"{airline_df['num_flights'].sum():,}", id="total-flights"),
            html.P("flights analyzed"),
        ], className="kpi-card kpi-purple"),
    ], className="kpi-row"),

    # Filters
    html.Div([
        html.Div([
            html.Label("Filter by Carrier:"),
            dcc.Dropdown(
                id='carrier-filter',
                options=[{'label': f"{c} - {airline_df[airline_df['Carrier']==c]['num_flights'].values[0]:,} flights",
                         'value': c}
                        for c in airline_df['Carrier']],
                value=None,
                multi=True,
                placeholder="Select carriers to compare..."
            ),
        ], className="filter-item"),
    ], className="filter-row"),

    # Main Charts Row 1
    html.Div([
        html.Div([
            dcc.Graph(id='airline-efficiency-chart'),
        ], className="chart-container chart-half"),

        html.Div([
            dcc.Graph(id='airport-performance-chart'),
        ], className="chart-container chart-half"),
    ], className="chart-row"),

    # Main Charts Row 2
    html.Div([
        html.Div([
            dcc.Graph(id='delay-rate-scatter'),
        ], className="chart-container chart-half"),

        html.Div([
            dcc.Graph(id='cost-comparison-chart'),
        ], className="chart-container chart-half"),
    ], className="chart-row"),

    # Footer
    html.Div([
        html.P([
            "Data Source: Bureau of Transportation Statistics | ",
            "Cost Model: $74/minute (FAA estimate) | ",
            f"Analysis: {airline_df['num_flights'].sum():,} flights"
        ], className="footer-text")
    ], className="footer"),

], className="dashboard-container")

# ============================================================================
# CALLBACKS FOR INTERACTIVITY
# ============================================================================

@callback(
    [Output('airline-efficiency-chart', 'figure'),
     Output('delay-rate-scatter', 'figure'),
     Output('cost-comparison-chart', 'figure')],
    Input('carrier-filter', 'value')
)
def update_airline_charts(selected_carriers):
    """Update airline charts based on carrier filter"""

    # Filter data if carriers selected
    if selected_carriers:
        filtered_df = airline_df[airline_df['Carrier'].isin(selected_carriers)]
    else:
        filtered_df = airline_df

    # Chart 1: Airline Efficiency Bar Chart
    fig_efficiency = px.bar(
        filtered_df.sort_values('avg_cost_per_mile'),
        x='avg_cost_per_mile',
        y='Carrier',
        orientation='h',
        title='💰 Airline Efficiency: Cost per Mile',
        color='avg_cost_per_mile',
        color_continuous_scale='RdYlGn_r',
        hover_data={
            'avg_delay_min': ':.1f',
            'delay_rate': ':.1%',
            'num_flights': ':,',
            'avg_cost_per_mile': ':.2f'
        },
        labels={
            'avg_cost_per_mile': 'Avg Cost per Mile ($)',
            'Carrier': 'Airline',
            'avg_delay_min': 'Avg Delay (min)',
            'delay_rate': 'Delay Rate',
            'num_flights': 'Flights'
        }
    )
    fig_efficiency.update_layout(
        xaxis_title="Average Cost per Mile ($)",
        yaxis_title="Carrier",
        showlegend=False,
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    # Chart 2: Delay Rate vs Cost Scatter
    fig_scatter = px.scatter(
        filtered_df,
        x='delay_rate',
        y='avg_cost_per_mile',
        size='num_flights',
        color='avg_delay_min',
        hover_name='Carrier',
        title='📊 Delay Rate vs Cost Efficiency',
        color_continuous_scale='Reds',
        labels={
            'delay_rate': 'Delay Rate (% of flights delayed >15 min)',
            'avg_cost_per_mile': 'Avg Cost per Mile ($)',
            'num_flights': 'Number of Flights',
            'avg_delay_min': 'Avg Delay (min)'
        }
    )
    fig_scatter.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    fig_scatter.update_layout(
        xaxis_title="Delay Rate (%)",
        yaxis_title="Cost per Mile ($)",
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    # Format x-axis as percentage
    fig_scatter.update_xaxes(tickformat='.0%')

    # Chart 3: Cost Comparison
    fig_cost = go.Figure()

    # Add bars for average delay cost
    fig_cost.add_trace(go.Bar(
        name='Avg Delay Cost',
        x=filtered_df['Carrier'],
        y=filtered_df['avg_delay_cost'],
        marker_color='indianred',
        text=filtered_df['avg_delay_cost'].apply(lambda x: f'${x:.0f}'),
        textposition='outside',
    ))

    fig_cost.update_layout(
        title='💵 Average Delay Cost by Carrier',
        xaxis_title="Carrier",
        yaxis_title="Average Delay Cost ($)",
        showlegend=False,
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    return fig_efficiency, fig_scatter, fig_cost


@callback(
    Output('airport-performance-chart', 'figure'),
    Input('carrier-filter', 'value')
)
def update_airport_chart(selected_carriers):
    """Update airport chart (doesn't filter, just updates)"""

    # Sort by delay cost
    sorted_airports = airport_df.sort_values('avg_delay_cost', ascending=False).head(10)

    fig = px.bar(
        sorted_airports,
        x='avg_delay_cost',
        y='Airport',
        orientation='h',
        title='🏢 Top 10 Airports by Delay Cost',
        color='avg_delay_cost',
        color_continuous_scale='Oranges',
        hover_data={
            'avg_delay_min': ':.1f',
            'delay_rate': ':.1%',
            'num_flights': ':,',
            'avg_delay_cost': ':.0f'
        },
        labels={
            'avg_delay_cost': 'Avg Delay Cost ($)',
            'Airport': 'Airport Code',
            'avg_delay_min': 'Avg Delay (min)',
            'delay_rate': 'Delay Rate',
            'num_flights': 'Flights'
        }
    )

    fig.update_layout(
        xaxis_title="Average Delay Cost ($)",
        yaxis_title="Airport",
        showlegend=False,
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    return fig


# ============================================================================
# CUSTOM CSS
# ============================================================================

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }

            .dashboard-container {
                max-width: 1400px;
                margin: 0 auto;
            }

            .header {
                background: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-align: center;
            }

            .header-title {
                color: #2d3748;
                font-size: 2.5rem;
                margin-bottom: 10px;
            }

            .header-subtitle {
                color: #718096;
                font-size: 1.2rem;
            }

            .kpi-row {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }

            .kpi-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-align: center;
                transition: transform 0.2s;
            }

            .kpi-card:hover {
                transform: translateY(-5px);
            }

            .kpi-card h4 {
                color: #718096;
                margin-bottom: 10px;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            .kpi-card h2 {
                font-size: 2rem;
                margin-bottom: 5px;
            }

            .kpi-card p {
                color: #718096;
                font-size: 0.9rem;
            }

            .kpi-green h2 { color: #48bb78; }
            .kpi-red h2 { color: #f56565; }
            .kpi-blue h2 { color: #4299e1; }
            .kpi-purple h2 { color: #9f7aea; }

            .filter-row {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }

            .filter-item label {
                display: block;
                margin-bottom: 10px;
                color: #2d3748;
                font-weight: 600;
            }

            .chart-row {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }

            .chart-container {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }

            .footer {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-align: center;
            }

            .footer-text {
                color: #718096;
                font-size: 0.9rem;
            }

            @media (max-width: 768px) {
                .header-title {
                    font-size: 1.8rem;
                }

                .kpi-row {
                    grid-template-columns: 1fr;
                }

                .chart-row {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting Delaynomics Dashboard")
    print("="*60)
    print(f"\n✓ Loaded {len(airline_df)} airlines")
    print(f"✓ Loaded {len(airport_df)} airports")
    if flights_df is not None:
        print(f"✓ Loaded {len(flights_df):,} flights")
    print(f"\n🌐 Dashboard running at: http://localhost:8050")
    print("   Press CTRL+C to quit\n")

    app.run(
        debug=True,
        host='0.0.0.0',
        port=8050
    )
