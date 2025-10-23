"""
Delaynomics Enhanced Dashboard - Modern Design
Aviation-themed interactive dashboard (duplicate of premium with two extra containers)
"""

import dash
from dash import dcc, html, Input, Output, callback, State, ALL, ctx, MATCH
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# DATA LOADING
# ============================================================================

def load_data():
    """Load pre-computed summary data from outputs folder"""
    try:
        airline_summary = pd.read_csv('outputs/airline_summary.csv')
        airport_summary = pd.read_csv('outputs/airport_summary.csv')

        full_data_path = Path('outputs/full_dataset_for_tableau.csv')
        if full_data_path.exists():
            full_data = pd.read_csv(full_data_path)
            # Compute day of week
            full_data['date'] = pd.to_datetime(full_data[['Year', 'Month', 'DayofMonth']].rename(
                columns={'DayofMonth': 'day'}))
            full_data['day_of_week'] = full_data['date'].dt.dayofweek
            full_data['day_name'] = full_data['date'].dt.day_name()
        else:
            full_data = None

        return airline_summary, airport_summary, full_data

    except FileNotFoundError as e:
        print("❌ Error: CSV files not found in outputs/ directory")
        print("   Run notebooks/analysis.ipynb first to generate the data")
        raise e

# Load data
airline_df, airport_df, flights_df = load_data()

# Compute day-of-week statistics
if flights_df is not None:
    dow_stats = flights_df.groupby('day_name').agg({
        'ArrDelay': 'mean',
        'delay_cost': 'mean',
        'is_delayed': 'mean'
    }).reset_index()
    # Order by day of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_stats['day_of_week'] = dow_stats['day_name'].apply(lambda x: day_order.index(x))
    dow_stats = dow_stats.sort_values('day_of_week')
else:
    dow_stats = None

# ============================================================================
# GEMINI AI CONFIGURATION
# ============================================================================

# Configure Gemini API (optional - will degrade gracefully if not available)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
gemini_model = None

if GEMINI_API_KEY:
    
        
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Use correct model names
        model_names = [
            'gemini-2.0-flash-exp',  # Latest
            'gemini-1.5-flash',      # Stable
            'gemini-1.5-pro'         # Fallback
        ]
        
        for model_name in model_names:
            try:
                gemini_model = genai.GenerativeModel(model_name)
                print(f"✓ Gemini AI enabled (using {model_name})")
                break
            except Exception as e:
                continue
                
        if not gemini_model:
            raise Exception("No compatible model found")
    except Exception as e:
        print(f"WARNING: Gemini AI unavailable: {e}")
        gemini_model = None
else:
    print("WARNING: GEMINI_API_KEY not set - AI features disabled")

def generate_ai_insights(airline_summary):
    """Generate AI-powered insights from airline data"""
    if not gemini_model:
        return "**AI Insights Unavailable**\n\nSet the `GEMINI_API_KEY` in your `.env` file to enable AI-powered insights.\n\n**How to enable:**\n1. Get API key from: https://makersuite.google.com/app/apikey\n2. Add to `.env` file: `GEMINI_API_KEY=your-key-here`\n3. Restart the dashboard"

    try:
        #gemini_model = 'gemini-2.0-flash'
        # Prepare data summary - format numbers nicely to avoid recitation issues
        top_5_df = airline_summary.nsmallest(5, 'avg_cost_per_mile')[['Carrier', 'avg_cost_per_mile', 'avg_delay_min', 'delay_rate']].copy()
        top_5_df['avg_cost_per_mile'] = top_5_df['avg_cost_per_mile'].round(2)
        top_5_df['avg_delay_min'] = top_5_df['avg_delay_min'].round(1)
        top_5_df['delay_rate'] = (top_5_df['delay_rate'] * 100).round(1)

        worst_3_df = airline_summary.nlargest(3, 'avg_cost_per_mile')[['Carrier', 'avg_cost_per_mile', 'avg_delay_min', 'delay_rate']].copy()
        worst_3_df['avg_cost_per_mile'] = worst_3_df['avg_cost_per_mile'].round(2)
        worst_3_df['avg_delay_min'] = worst_3_df['avg_delay_min'].round(1)
        worst_3_df['delay_rate'] = (worst_3_df['delay_rate'] * 100).round(1)

        prompt = f"""Analyze this airline data and provide exactly 3 brief insights:

Best performers: {top_5_df.to_string(index=False)}
Worst performers: {worst_3_df.to_string(index=False)}

Write exactly 3 points (1 sentence each):
1. Best airline and why
2. Worst airline and why
3. One key travel tip

Be brief and use specific numbers from the data."""

        # Configure safety settings to be more permissive for business data
        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        response = gemini_model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.5,
                'top_p': 0.9,
                'top_k': 20,
                'max_output_tokens': 512,
            },
            safety_settings=safety_settings
        )

        # Check if response was blocked or has no text
        if not response.candidates or not response.candidates[0].content.parts:
            raise Exception("Response was blocked or empty")

        # Extract all text from all parts
        full_text = ""
        candidate = response.candidates[0]

        for part in candidate.content.parts:
            if hasattr(part, 'text'):
                full_text += part.text

        # Log finish reason and response length for debugging
        print(f"DEBUG: AI response finish_reason: {candidate.finish_reason}, length: {len(full_text)}")
        print(f"DEBUG: Response text: {full_text[:200]}...")

        # Check if response is incomplete (finish_reason != 1 means not normal STOP)
        if candidate.finish_reason and candidate.finish_reason != 1:
            print(f"WARNING: AI response incomplete (finish_reason: {candidate.finish_reason})")

        if not full_text:
            raise Exception("No text content in response")

        return full_text

    except Exception as e:
        # Provide fallback insights when AI fails
        best = airline_summary.nsmallest(1, 'avg_cost_per_mile').iloc[0]
        worst = airline_summary.nlargest(1, 'avg_cost_per_mile').iloc[0]

        fallback = f"""
**AI temporarily unavailable** - showing basic analysis instead:

1. **Best Performer**: {best['Carrier']} with ${best['avg_cost_per_mile']:.2f} per mile ({best['delay_rate']*100:.1f}% delay rate)

2. **Worst Performer**: {worst['Carrier']} with ${worst['avg_cost_per_mile']:.2f} per mile ({worst['delay_rate']*100:.1f}% delay rate)

3. **Tip**: Check the charts below for detailed comparisons across all carriers.

*Error details: {str(e)}*
"""
        return fallback

# ============================================================================
# CONSTANTS & STYLING
# ============================================================================

# Brand colors - Aviation Premium theme
COLORS = {
    'primary': '#0A1F44',      # Deep navy blue
    'accent': '#00D9FF',       # Vibrant cyan
    'success': '#10B981',      # Emerald green
    'warning': '#F59E0B',      # Amber
    'danger': '#FF6B6B',       # Coral red
    'background': '#F8FAFC',   # Soft off-white
    'card': '#FFFFFF',         # Pure white
    'text_primary': '#1E293B', # Slate 800
    'text_secondary': '#64748B' # Slate 500
}

# Chart colors for airlines
AIRLINE_COLORS = ['#00D9FF', '#10B981', '#F59E0B', '#FF6B6B', '#9333EA']

# Airline name mapping (2-letter code to full name)
AIRLINE_NAMES = {
    'AA': 'American Airlines',
    'AS': 'Alaska Airlines',
    'B6': 'JetBlue Airways',
    'DL': 'Delta Air Lines',
    'F9': 'Frontier Airlines',
    'G4': 'Allegiant Air',
    'HA': 'Hawaiian Airlines',
    'NK': 'Spirit Airlines',
    'UA': 'United Airlines',
    'WN': 'Southwest Airlines',
    'OO': 'SkyWest Airlines',
    'YX': 'Republic Airways',
    '9E': 'Endeavor Air',
    'YV': 'Mesa Airlines'
}

# ============================================================================
# DASH APP SETUP
# ============================================================================

app = dash.Dash(
    __name__,
    title="Delaynomics Premium",
    update_title="Loading...",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Small fallback airport lat/lon mapping for common US airports (IATA -> (lat, lon)).
# This is used when `airport_df` lacks coordinate columns.
FALLBACK_AIRPORT_COORDS = {
    'ATL': (33.6407, -84.4277),
    'LAX': (33.9416, -118.4085),
    'ORD': (41.9742, -87.9073),
    'DFW': (32.8998, -97.0403),
    'DEN': (39.8561, -104.6737),
    'JFK': (40.6413, -73.7781),
    'SFO': (37.6213, -122.3790),
    'SEA': (47.4502, -122.3088),
    'LAS': (36.0840, -115.1537),
    'MCO': (28.4312, -81.3081),
    'CLT': (35.2144, -80.9473),
    'PHX': (33.4342, -112.0116),
    'IAH': (29.9902, -95.3368),
    'MIA': (25.7959, -80.2870),
    'BOS': (42.3656, -71.0096),
    'MSP': (44.8848, -93.2223),
    'DTW': (42.2162, -83.3554),
    'PHL': (39.8744, -75.2424),
    'BWI': (39.1754, -76.6684),
    'SLC': (40.7884, -111.9778)
}

def create_kpi_card(icon, title, value, subtitle, trend=None, color='accent'):
    """Create a premium KPI card with optional trend"""

    trend_indicator = html.Div()
    if trend:
        trend_color = COLORS['success'] if trend > 0 else COLORS['danger']
        trend_symbol = '↑' if trend > 0 else '↓'
        trend_indicator = html.Div([
            html.Span(f"{trend_symbol} {abs(trend)}%",
                     style={'color': trend_color, 'fontSize': '14px', 'fontWeight': '600'})
        ], style={'marginTop': '8px'})

    return html.Div([
        html.Div([
            html.Div(icon, className=f'kpi-icon kpi-{color}'),
            html.Div(title, className='kpi-title'),
            html.Div(value, className='kpi-value'),
            html.Div(subtitle, className='kpi-subtitle'),
            trend_indicator
        ])
    ], className='kpi-card-premium')

# ============================================================================
# LAYOUT
# ============================================================================

app.layout = html.Div([
    # Header with gradient background
    html.Div([
        html.Div([
            html.H1("Delaynomics", className="header-title-premium"),
            html.P(
                "Which airlines deliver the best value for money?",
                className="header-subtitle-premium"
            ),
        ], className="header-content-premium"),
    ], className="header-premium"),

    # Main container
    html.Div([
        # KPI Cards Row
        html.Div([
            create_kpi_card(
                "",
                "BEST CARRIER",
                airline_df.iloc[0]['Carrier'],
                f"${airline_df.iloc[0]['avg_cost_per_mile']:.2f} per mile",
                trend=-42,
                color='success'
            ),
            create_kpi_card(
                "",
                "WORST CARRIER",
                airline_df.iloc[-1]['Carrier'],
                f"${airline_df.iloc[-1]['avg_cost_per_mile']:.2f} per mile",
                trend=+69,
                color='danger'
            ),
            create_kpi_card(
                "",
                "AVG DELAY COST",
                f"${airline_df['avg_delay_cost'].mean():.0f}",
                "per delayed flight",
                color='warning'
            ),
            create_kpi_card(
                "",
                "TOTAL FLIGHTS",
                f"{airline_df['num_flights'].sum():,}",
                "flights analyzed",
                color='primary'
            ),
        ], className="kpi-row-premium"),

        # AI Insights Card
        html.Div([
            html.Div([
                html.H3("AI-Powered Insights", className="chart-title-premium"),
                html.P("Generated using Gemini AI", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            html.Div(id='ai-insights-content', className="ai-insights-text"),
            dcc.Loading(
                id="loading-insights",
                type="circle",
                children=html.Div(id="insights-loading-output")
            ),
        ], className="ai-insights-card-premium"),

        # Interactive Airline Filter (replaces dropdown)
        html.Div([
            html.H4("Select Airlines to Compare (click to filter)", className="key-title-premium"),
            html.Div([
                html.Div([
                    html.Span(f"{code}", className="airline-code-premium"),
                    html.Span(f"{AIRLINE_NAMES.get(code, code)}", className="airline-name-premium"),
                    html.Span(f"{airline_df[airline_df['Carrier']==code]['num_flights'].values[0]:,} flights",
                             className="airline-flights-premium")
                ], id={'type': 'airline-filter-item', 'index': code},
                   className="airline-key-item-premium airline-key-clickable active",
                   n_clicks=0)
                for code in sorted(airline_df['Carrier'].unique())
            ], className="airline-key-grid-premium"),
            # Hidden div to store selected carriers
            html.Div(id='selected-carriers-store', style={'display': 'none'}),
        ], className="airline-key-section-premium"),

        # Chart 1 - Full Width
        html.Div([
            html.Div([
                html.H3("Cost Efficiency Ranking", className="chart-title-premium"),
                html.P("Lower cost per mile = better value", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            dcc.Graph(
                id='airline-efficiency-chart',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large"),

        # Chart 2 - Full Width
        html.Div([
            html.Div([
                html.H3("Airport Performance", className="chart-title-premium"),
                html.P("Delay costs by origin airport", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            dcc.Graph(
                id='airport-performance-chart',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large"),

        # Chart 3 - Full Width
        html.Div([
            html.Div([
                html.H3("Efficiency Matrix", className="chart-title-premium"),
                html.P("Delay rate vs. cost efficiency", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            dcc.Graph(
                id='delay-rate-scatter',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large"),

        # Chart 4 - Full Width
        html.Div([
            html.Div([
                html.H3("Carrier Comparison", className="chart-title-premium"),
                html.P("Average delay cost by carrier", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            dcc.Graph(
                id='cost-comparison-chart',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large"),

        # === NEW: Network Analysis Container (only added container, no callbacks changed) ===
        html.Div([
            html.Div([
                html.H3("US Flight Network Map", className="chart-title-premium"),
                html.P("Geographic visualization of routes with highest delay costs", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            html.Div([
                html.Div([
                    html.Label('Carrier filter', style={'fontWeight':'600','marginRight':'12px'}),
                    dcc.Dropdown(
                        id='route-carrier-filter',
                        options=[{'label': k, 'value': k} for k in sorted(airline_df['Carrier'].unique())],
                        value=[],
                        multi=True,
                        placeholder='Filter by carrier (optional)'
                    ),
                ], style={'display':'inline-block', 'width':'48%', 'verticalAlign':'middle'}),
                html.Div([
                    html.Label('Routes to display', style={'fontWeight':'600','marginRight':'12px'}),
                    dcc.Slider(id='top-n-routes', min=50, max=800, step=50, value=300,
                               marks={50:'50',150:'150',300:'300',500:'500',800:'800'})
                ], style={'display':'inline-block', 'width':'48%', 'paddingLeft':'16px', 'verticalAlign':'middle'})
            ], style={'marginBottom': '12px'}),
            dcc.Graph(
                id='network-performance-chart',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large"),

        # === Route Performance Matrix ===
        html.Div([
            html.Div([
                html.H3("Route Performance Matrix", className="chart-title-premium"),
                html.P("Route efficiency by distance category and flight frequency", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            dcc.Graph(
                id='route-performance-matrix',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large"),

        # === Hub Connectivity Network ===
        html.Div([
            html.Div([
                html.H3("Hub Connectivity Network", className="chart-title-premium"),
                html.P("Airport network size vs operational efficiency", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            dcc.Graph(
                id='hub-connectivity-chart',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large"),

        # === Seasonal Delay Patterns ===
        html.Div([
            html.Div([
                html.H3("Seasonal Delay Patterns", className="chart-title-premium"),
                html.P("Route delay trends across months of the year", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            dcc.Graph(
                id='seasonal-patterns-chart',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large"),

        # Chart 5 - Day of Week Analysis (NEW)
        html.Div([
            html.Div([
                html.H3("Day of Week Performance", className="chart-title-premium"),
                html.P("When should you fly to minimize delays?", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            dcc.Graph(
                id='day-of-week-chart',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large") if dow_stats is not None else html.Div(),

        # Interactive Chatbot Section (NEW)
        html.Div([
            html.Div([
                html.H3("Ask the AI Analyst", className="chart-title-premium"),
                html.P("Ask questions about the data", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            html.Div([
                dcc.Textarea(
                    id='chat-input',
                    placeholder='Ask a question like: "Which airline is best for cross-country flights?" or "Why does JetBlue have higher delays?"',
                    className="chat-input-premium",
                    style={'width': '100%', 'height': '100px', 'marginBottom': '12px'}
                ),
                html.Button('Ask AI', id='chat-submit-btn', n_clicks=0, className="chat-submit-btn-premium"),
            ]),
            dcc.Loading(
                id="loading-chat",
                type="circle",
                children=html.Div(id='chat-response', className="chat-response-premium")
            ),
        ], className="chat-card-premium"),

        # Footer
        html.Div([
            html.Div([
                html.Span("Data Source: ", style={'fontWeight': '600'}),
                html.Span("Bureau of Transportation Statistics"),
                html.Span(" | ", style={'margin': '0 10px'}),
                html.Span("Cost Model: ", style={'fontWeight': '600'}),
                html.A("$47.10/hour (FAA VOT)", href="https://www.faa.gov/sites/faa.gov/files/regulations_policies/policy_guidance/benefit_cost/econ-value-section-1-tx-time.pdf", target="_blank", style={'color': COLORS['accent'], 'textDecoration': 'none', 'fontWeight': '600'}),
                html.Span(" | ", style={'margin': '0 10px'}),
                html.Span("Analysis: ", style={'fontWeight': '600'}),
                html.Span(f"{airline_df['num_flights'].sum():,} flights"),
            ], className="footer-text-premium")
        ], className="footer-premium"),

    ], className="main-container-premium"),

], className="dashboard-container-premium")

# ============================================================================
# CALLBACKS
# ============================================================================

# Store to track selected carriers
selected_carriers_set = set(airline_df['Carrier'].unique())

@callback(
    [Output({'type': 'airline-filter-item', 'index': ALL}, 'className'),
     Output('selected-carriers-store', 'children')],
    Input({'type': 'airline-filter-item', 'index': ALL}, 'n_clicks'),
    State({'type': 'airline-filter-item', 'index': ALL}, 'id'),
    prevent_initial_call=False
)
def toggle_airline_selection(n_clicks_list, ids):
    """Toggle airline selection on click"""
    global selected_carriers_set

    # Initialize on first load
    if not ctx.triggered_id:
        # All carriers active by default
        classnames = ["airline-key-item-premium airline-key-clickable active" for _ in ids]
        return classnames, json.dumps(list(selected_carriers_set))

    # Handle click
    clicked_id = ctx.triggered_id
    clicked_carrier = clicked_id['index']

    # Toggle carrier in set
    if clicked_carrier in selected_carriers_set:
        selected_carriers_set.remove(clicked_carrier)
    else:
        selected_carriers_set.add(clicked_carrier)

    # Update class names
    classnames = []
    for id_dict in ids:
        carrier = id_dict['index']
        if carrier in selected_carriers_set:
            classnames.append("airline-key-item-premium airline-key-clickable active")
        else:
            classnames.append("airline-key-item-premium airline-key-clickable")

    return classnames, json.dumps(list(selected_carriers_set))

@callback(
    Output('ai-insights-content', 'children'),
    Input('selected-carriers-store', 'children')
)
def update_ai_insights(trigger):
    """Generate AI insights on page load"""
    insights_text = generate_ai_insights(airline_df)
    return dcc.Markdown(insights_text, className="insights-markdown")

@callback(
    Output('chat-response', 'children'),
    Input('chat-submit-btn', 'n_clicks'),
    State('chat-input', 'value'),
    prevent_initial_call=True
)
def handle_chat_question(n_clicks, question):
    """Handle user questions with AI chatbot"""
    if not question or question.strip() == '':
        return dcc.Markdown("*Please enter a question above and click 'Ask AI'*")

    if not gemini_model:
        return dcc.Markdown("**Gemini API not configured**\n\nSet the `GEMINI_API_KEY` environment variable to use the chatbot.")

    try:
        # Prepare data context for the AI
        airline_context = airline_df[['Carrier', 'avg_cost_per_mile', 'avg_delay_min', 'delay_rate', 'num_flights']].to_string(index=False)
        airport_context = airport_df.nlargest(10, 'avg_delay_cost')[['Airport', 'avg_delay_cost', 'avg_delay_min']].to_string(index=False)

        dow_context = ""
        if dow_stats is not None:
            dow_context = f"\n\nDAY OF WEEK STATISTICS:\n{dow_stats[['day_name', 'ArrDelay', 'delay_cost', 'is_delayed']].to_string(index=False)}"

        prompt = f"""
        You are a flight delay data analyst. Answer this question based mostly on the data provided below, and any similar context.

        USER QUESTION: {question}

        AIRLINE PERFORMANCE DATA:
        {airline_context}

        TOP 10 WORST AIRPORTS (by delay cost):
        {airport_context}
        {dow_context}

        INSTRUCTIONS:
        - Provide a clear, data-driven answer with specific numbers from the data above
        - Use carrier codes (AA, DL, etc.) and reference actual metrics
        - If the question asks about something not in the data, answer only if it is related to the data provided. Use your insights, but mention if your answer is not entirely based on the provided data.
        - Be concise but thorough (2-4 sentences)
        - Format your response in markdown

        Answer:
        """

        # Configure safety settings
        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        response = gemini_model.generate_content(prompt, safety_settings=safety_settings)

        # Check if response was blocked or has no text
        if not response.candidates or not response.candidates[0].content.parts:
            raise Exception("Response was blocked or empty")

        # Extract all text from all parts to ensure we get the complete response
        full_text = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                full_text += part.text

        if not full_text:
            raise Exception("No text content in response")

        return dcc.Markdown(f"**Answer:**\n\n{full_text}")

    except Exception as e:
        return dcc.Markdown(f"**Error**: {str(e)}")

@callback(
    [Output('airline-efficiency-chart', 'figure'),
     Output('delay-rate-scatter', 'figure'),
     Output('cost-comparison-chart', 'figure')],
    Input('selected-carriers-store', 'children')
)
def update_airline_charts(selected_carriers_json):
    """Update airline charts with premium styling"""

    # Parse selected carriers
    if selected_carriers_json:
        try:
            selected_carriers = json.loads(selected_carriers_json)
        except:
            selected_carriers = None
    else:
        selected_carriers = None

    # Filter data
    if selected_carriers and len(selected_carriers) > 0:
        filtered_df = airline_df[airline_df['Carrier'].isin(selected_carriers)]
    else:
        filtered_df = airline_df

    # Chart 1: Airline Efficiency - Horizontal bar with gradient
    sorted_df = filtered_df.sort_values('avg_cost_per_mile')

    fig_efficiency = go.Figure()

    colors = [COLORS['success'] if x < filtered_df['avg_cost_per_mile'].median()
              else COLORS['danger'] for x in sorted_df['avg_cost_per_mile']]

    fig_efficiency.add_trace(go.Bar(
        y=sorted_df['Carrier'],
        x=sorted_df['avg_cost_per_mile'],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(width=0),
        ),
        text=[f"${x:.2f}" for x in sorted_df['avg_cost_per_mile']],
        textposition='inside',
        textfont=dict(size=12, family='Inter, sans-serif', color='white'),
        hovertemplate='<b>%{y}</b><br>Cost per mile: $%{x:.2f}<extra></extra>',
    ))

    fig_efficiency.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=COLORS['text_secondary'], size=11),
        xaxis=dict(
            title='Cost per Mile ($)',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            zeroline=False,
            automargin=True,
            fixedrange=True,
        ),
        yaxis=dict(
            title='',
            showgrid=False,
            automargin=True,
            fixedrange=True,
        ),
        margin=dict(l=50, r=50, t=30, b=60),
        autosize=True,
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Inter, sans-serif"
        )
    )

    # Chart 2: Efficiency Matrix - Scatter with quadrants
    fig_scatter = go.Figure()

    # Add quadrant lines
    median_rate = filtered_df['delay_rate'].median()
    median_cost = filtered_df['avg_cost_per_mile'].median()

    fig_scatter.add_hline(y=median_cost, line_dash="dot", line_color="rgba(0,0,0,0.2)",
                           annotation_text="", annotation_position="right")
    fig_scatter.add_vline(x=median_rate, line_dash="dot", line_color="rgba(0,0,0,0.2)",
                           annotation_text="", annotation_position="top")

    # Add regression line
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        filtered_df['delay_rate'],
        filtered_df['avg_cost_per_mile']
    )
    line_x = np.array([filtered_df['delay_rate'].min(), filtered_df['delay_rate'].max()])
    line_y = slope * line_x + intercept
    
    # Add regression line as a trace
    fig_scatter.add_trace(go.Scatter(
        x=line_x,
        y=line_y,
        mode='lines',
        name=f'Regression (R² = {r_value**2:.2f})',
        line=dict(color='rgba(100,100,100,0.5)', dash='dot'),
    
        
        hovertemplate='R² = {r_value**2:.2f}<extra></extra>'
    ))

    # Add scatter points
    fig_scatter.add_trace(go.Scatter(
        x=filtered_df['delay_rate'],
        y=filtered_df['avg_cost_per_mile'],
        mode='markers+text',
        marker=dict(
            # Scale down the size more aggressively and add limits
            size=filtered_df['num_flights'] / 1000,  # Reduced from /100 to /1000
            sizemin=10,  # Minimum size
            sizemode='area',  # Use area for more intuitive scaling
            sizeref=2. * filtered_df['num_flights'].max() / (1000**2),  # Normalize the size range
            color=filtered_df['avg_delay_min'],
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title="Avg Delay<br>(min)"),
            line=dict(width=2, color='white'),
        ),
        text=filtered_df['Carrier'],
        textposition='middle center',
        textfont=dict(size=12, color='white', family='Roboto Mono, monospace'),
        hovertemplate='<b>%{text}</b><br>Delay Rate: %{x:.1%}<br>Cost/Mile: $%{y:.2f}<extra></extra>',
    ))

    fig_scatter.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            x=-0.02,  # Position at 2% from left
            y=-0.02,  # Position at 2% from bottom
            xanchor='left',
            yanchor='bottom',
            bgcolor='rgba(255,255,255,0.8)'  # Semi-transparent white background
        ),
        font=dict(family='Inter, sans-serif', color=COLORS['text_secondary'], size=11),
        xaxis=dict(
            title='Delay Rate',
            tickformat='.0%',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            automargin=True,
            fixedrange=True,
        ),
        yaxis=dict(
            title='Cost per Mile ($)',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            automargin=True,
            fixedrange=True,
        ),
        margin=dict(l=50, r=50, t=30, b=60),
        autosize=True,
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Inter, sans-serif"
        )
    )

    # Chart 3: Cost Comparison - Grouped bars
    fig_cost = go.Figure()

    sorted_cost_df = filtered_df.sort_values('avg_delay_cost', ascending=False)

    colors_cost = [COLORS['danger'] if i < len(sorted_cost_df)//2
                   else COLORS['warning'] for i in range(len(sorted_cost_df))]

    fig_cost.add_trace(go.Bar(
        x=sorted_cost_df['Carrier'],
        y=sorted_cost_df['avg_delay_cost'],
        marker=dict(
            color=colors_cost,
            line=dict(width=0),
        ),
        text=[f"${x:.0f}" for x in sorted_cost_df['avg_delay_cost']],
        textposition='inside',
        textfont=dict(size=12, family='Inter, sans-serif', color='white'),
        hovertemplate='<b>%{x}</b><br>Avg Delay Cost: $%{y:.0f}<extra></extra>',
    ))

    fig_cost.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=COLORS['text_secondary'], size=11),
        xaxis=dict(
            title='Carrier',
            showgrid=False,
            automargin=True,
            fixedrange=True,
        ),
        yaxis=dict(
            title='Average Delay Cost ($)',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            automargin=True,
            fixedrange=True,
        ),
        margin=dict(l=50, r=50, t=30, b=60),
        autosize=True,
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Inter, sans-serif"
        )
    )

    return fig_efficiency, fig_scatter, fig_cost


@callback(
    Output('airport-performance-chart', 'figure'),
    Input('selected-carriers-store', 'children')
)
def update_airport_chart(selected_carriers_json):
    """Update airport chart with premium styling"""

    sorted_airports = airport_df.sort_values('avg_delay_cost', ascending=False).head(10)

    fig = go.Figure()

    # Gradient colors from red to orange
    colors_gradient = [f'rgb({255}, {int(107 + (i * 14))}, {int(107 + (i * 14))})'
                       for i in range(len(sorted_airports))]

    fig.add_trace(go.Bar(
        y=sorted_airports['Airport'],
        x=sorted_airports['avg_delay_cost'],
        orientation='h',
        marker=dict(
            color=colors_gradient,
            line=dict(width=0),
        ),
        text=[f"${x:.0f}" for x in sorted_airports['avg_delay_cost']],
        textposition='inside',
        textfont=dict(size=12, family='Inter, sans-serif', color='white'),
        hovertemplate='<b>%{y}</b><br>Avg Delay Cost: $%{x:.0f}<extra></extra>',
    ))

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=COLORS['text_secondary'], size=11),
        xaxis=dict(
            title='Average Delay Cost ($)',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            automargin=True,
            fixedrange=True,
        ),
        yaxis=dict(
            title='',
            showgrid=False,
            automargin=True,
            fixedrange=True,
        ),
        margin=dict(l=50, r=50, t=30, b=60),
        autosize=True,
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Inter, sans-serif"
        )
    )

    return fig


@callback(
    Output('day-of-week-chart', 'figure'),
    Input('selected-carriers-store', 'children')
)
def update_day_of_week_chart(trigger):
    """Update day of week analysis chart"""
    if dow_stats is None:
        return go.Figure()

    fig = go.Figure()

    # Create dual-axis chart: bars for delay rate, line for avg delay
    fig.add_trace(go.Bar(
        x=dow_stats['day_name'],
        y=dow_stats['is_delayed'] * 100,
        name='Delay Rate',
        marker=dict(
            color=dow_stats['is_delayed'] * 100,
            colorscale='RdYlGn_r',
            showscale=False,
            line=dict(width=0),
        ),
        text=[f"{x:.1f}%" for x in dow_stats['is_delayed'] * 100],
        textposition='inside',
        textfont=dict(size=12, family='Inter, sans-serif', color='white'),
        hovertemplate='<b>%{x}</b><br>Delay Rate: %{y:.1f}%<extra></extra>',
        yaxis='y'
    ))

    fig.add_trace(go.Scatter(
        x=dow_stats['day_name'],
        y=dow_stats['ArrDelay'],
        name='Avg Delay (min)',
        mode='lines+markers',
        line=dict(color=COLORS['accent'], width=3),
        marker=dict(size=10, color=COLORS['accent'], line=dict(width=2, color='white')),
        hovertemplate='<b>%{x}</b><br>Avg Delay: %{y:.1f} min<extra></extra>',
        yaxis='y2'
    ))

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=COLORS['text_secondary'], size=11),
        xaxis=dict(
            title='Day of Week',
            showgrid=False,
            automargin=True,
            fixedrange=True,
        ),
        yaxis=dict(
            title='Delay Rate (%)',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            automargin=True,
            fixedrange=True,
        ),
        yaxis2=dict(
            title='Average Delay (minutes)',
            overlaying='y',
            side='right',
            showgrid=False,
            automargin=True,
            fixedrange=True,
        ),
        margin=dict(l=50, r=50, t=30, b=60),
        autosize=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Inter, sans-serif"
        )
    )

    return fig


# Helper: placeholder empty figure with a message
def _empty_figure(message: str = "No data available") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, xref='paper', yref='paper', showarrow=False,
                       font=dict(size=14, color=COLORS['text_secondary']))
    fig.update_layout(
        xaxis={'visible': False},
        yaxis={'visible': False},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig


@callback(
    Output('network-performance-chart', 'figure'),
    [Input('top-n-routes', 'value'),
     Input('route-carrier-filter', 'value'),
     Input('selected-carriers-store', 'children')]
)
def update_network_performance(top_n, carrier_filter, selected_carriers_json):
    """Render US Geographic Network Map showing flight routes with delay costs"""
    route_path = Path('outputs/route_summary.csv')
    if not route_path.exists():
        return _empty_figure("Route summary CSV not found (outputs/route_summary.csv)")

    try:
        route_df = pd.read_csv(route_path)
        if route_df.empty:
            return _empty_figure("Route summary CSV is empty")

        # Apply carrier filters
        try:
            selected = json.loads(selected_carriers_json) if selected_carriers_json else None
        except Exception:
            selected = None

        carriers_to_filter = carrier_filter if carrier_filter else selected
        if carriers_to_filter and 'primary_carrier' in route_df.columns:
            route_df = route_df[route_df['primary_carrier'].isin(carriers_to_filter)]

        # Get top N routes by total delay cost
        value_col = 'total_delay_cost' if 'total_delay_cost' in route_df.columns else 'avg_delay_cost'
        top_n = int(top_n) if top_n is not None else 20
        top_routes = route_df.nlargest(top_n, value_col).copy()

        # Load airport coordinates
        coords_df = None
        coords_path = Path('data/airport_coords.csv')
        if coords_path.exists():
            coords_df = pd.read_csv(coords_path)
        
        # Parse route origins and destinations
        def parse_route_codes(route_str):
            if pd.isna(route_str):
                return None, None
            parts = str(route_str).split('-')
            if len(parts) >= 2:
                return parts[0].strip().upper(), parts[1].strip().upper()
            return None, None

        # Extract origin/dest from route column
        route_parsed = top_routes['route'].apply(lambda x: pd.Series(parse_route_codes(x), index=['origin', 'dest']))
        top_routes = pd.concat([top_routes.reset_index(drop=True), route_parsed], axis=1)

        # Get coordinates for each airport
        def get_coordinates(airport_code):
            if not airport_code:
                return None, None
            
            # Try coordinates CSV first
            if coords_df is not None:
                match = coords_df[coords_df['iata'] == airport_code]
                if not match.empty:
                    return float(match.iloc[0]['lat']), float(match.iloc[0]['lon'])
            
            # Fallback to hardcoded coordinates
            if airport_code in FALLBACK_AIRPORT_COORDS:
                return FALLBACK_AIRPORT_COORDS[airport_code]
            
            return None, None

        # Add coordinates to routes
        coords_data = []
        for _, row in top_routes.iterrows():
            origin_lat, origin_lon = get_coordinates(row['origin'])
            dest_lat, dest_lon = get_coordinates(row['dest'])
            
            if all(coord is not None for coord in [origin_lat, origin_lon, dest_lat, dest_lon]):
                coords_data.append({
                    'route': row['route'],
                    'origin': row['origin'],
                    'dest': row['dest'],
                    'origin_lat': origin_lat,
                    'origin_lon': origin_lon,
                    'dest_lat': dest_lat,
                    'dest_lon': dest_lon,
                    'delay_cost': row[value_col],
                    'num_flights': row.get('num_flights', 0),
                    'avg_delay_min': row.get('avg_delay_min', 0),
                    'delay_rate': row.get('delay_rate', 0),
                    'carrier': row.get('primary_carrier', 'Unknown')
                })

        if not coords_data:
            return _empty_figure("No coordinate data available for routes")

        coords_df_final = pd.DataFrame(coords_data)
        
        # Create the map figure
        fig = go.Figure()

        # Normalize values for visual scaling
        max_cost = coords_df_final['delay_cost'].max()
        min_cost = coords_df_final['delay_cost'].min()
        max_flights = coords_df_final['num_flights'].max() if coords_df_final['num_flights'].max() > 0 else 1

        # Add flight routes as lines
        for _, route in coords_df_final.iterrows():
            # Calculate line properties
            cost_ratio = (route['delay_cost'] - min_cost) / (max_cost - min_cost) if max_cost > min_cost else 0
            line_width = 2 + (cost_ratio * 8)  # 2-10px width range
            
            # Color based on delay severity
            if cost_ratio < 0.33:
                line_color = COLORS['success']  # Green for low delay cost
            elif cost_ratio < 0.66:
                line_color = COLORS['warning']  # Orange for medium delay cost
            else:
                line_color = COLORS['danger']   # Red for high delay cost

            # Create curved flight path (great circle approximation)
            lons = [route['origin_lon'], route['dest_lon']]
            lats = [route['origin_lat'], route['dest_lat']]
            
            # Add some curvature for visual appeal
            mid_lon = (route['origin_lon'] + route['dest_lon']) / 2
            mid_lat = (route['origin_lat'] + route['dest_lat']) / 2 + 2  # Slight northward curve
            
            # Create curved path with 3 points
            curve_lons = [route['origin_lon'], mid_lon, route['dest_lon']]
            curve_lats = [route['origin_lat'], mid_lat, route['dest_lat']]

            fig.add_trace(go.Scattergeo(
                lon=curve_lons,
                lat=curve_lats,
                mode='lines',
                line=dict(
                    width=line_width,
                    color=line_color,
                ),
                opacity=0.7,
                hoverinfo='text',
                hovertext=f"""<b>{route['route']}</b><br>
                Carrier: {route['carrier']}<br>
                Total Delay Cost: ${route['delay_cost']:,.0f}<br>
                Flights: {route['num_flights']:,}<br>
                Avg Delay: {route['avg_delay_min']:.1f} min<br>
                Delay Rate: {route['delay_rate']*100:.1f}%""",
                showlegend=False,
                name=''
            ))

        # Add airport nodes
        airports = {}
        for _, route in coords_df_final.iterrows():
            # Collect origin airports
            if route['origin'] not in airports:
                airports[route['origin']] = {
                    'lat': route['origin_lat'],
                    'lon': route['origin_lon'],
                    'total_cost': 0,
                    'total_flights': 0,
                    'routes': 0
                }
            airports[route['origin']]['total_cost'] += route['delay_cost']
            airports[route['origin']]['total_flights'] += route['num_flights']
            airports[route['origin']]['routes'] += 1
            
            # Collect destination airports
            if route['dest'] not in airports:
                airports[route['dest']] = {
                    'lat': route['dest_lat'],
                    'lon': route['dest_lon'],
                    'total_cost': 0,
                    'total_flights': 0,
                    'routes': 0
                }
            airports[route['dest']]['total_cost'] += route['delay_cost']
            airports[route['dest']]['total_flights'] += route['num_flights']
            airports[route['dest']]['routes'] += 1

        # Add airport markers
        airport_lons = []
        airport_lats = []
        airport_sizes = []
        airport_colors = []
        airport_texts = []
        airport_hovers = []

        max_airport_cost = max(data['total_cost'] for data in airports.values()) if airports else 1

        for code, data in airports.items():
            airport_lons.append(data['lon'])
            airport_lats.append(data['lat'])
            
            # Size based on total cost impact
            size_ratio = data['total_cost'] / max_airport_cost if max_airport_cost > 0 else 0
            size = 8 + (size_ratio * 20)  # 8-28px range
            airport_sizes.append(size)
            
            # Color based on hub size (number of routes)
            if data['routes'] >= 5:
                airport_colors.append(COLORS['primary'])  # Major hub
            elif data['routes'] >= 3:
                airport_colors.append(COLORS['accent'])   # Medium hub
            else:
                airport_colors.append(COLORS['text_secondary'])  # Small airport
            
            airport_texts.append(code)
            airport_hovers.append(f"""<b>{code}</b><br>
            Routes: {data['routes']}<br>
            Total Delay Cost: ${data['total_cost']:,.0f}<br>
            Total Flights: {data['total_flights']:,}""")

        fig.add_trace(go.Scattergeo(
            lon=airport_lons,
            lat=airport_lats,
            mode='markers+text',
            marker=dict(
                size=airport_sizes,
                color=airport_colors,
                line=dict(width=1, color='white'),
                sizemode='diameter'
            ),
            text=airport_texts,
            textposition='middle center',
            textfont=dict(size=10, color='white', family='Inter, sans-serif'),
            hoverinfo='text',
            hovertext=airport_hovers,
            showlegend=False,
            name=''
        ))

        # Update layout for US map
        fig.update_layout(
            title=dict(
                text=f'US Flight Network - Top {len(coords_df_final)} Routes by Delay Cost',
                font=dict(size=16, family='Inter, sans-serif', color=COLORS['text_primary'])
            ),
            geo=dict(
                scope='usa',
                projection_type='albers usa',
                showland=True,
                landcolor='rgb(243, 243, 243)',
                coastlinecolor='rgb(204, 204, 204)',
                showlakes=True,
                lakecolor='rgb(255, 255, 255)',
                showsubunits=True,
                subunitcolor='rgb(217, 217, 217)',
                countrycolor='rgb(217, 217, 217)',
                showframe=False,
                bgcolor='rgba(0,0,0,0)'
            ),
            showlegend=False,
            margin=dict(l=0, r=0, t=50, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, sans-serif', color=COLORS['text_secondary']),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Inter, sans-serif",
                bordercolor=COLORS['text_secondary']
            )
        )

        return fig

    except Exception as e:
        return _empty_figure(f"Error creating network map: {str(e)}")
            


@callback(
    Output('route-performance-matrix', 'figure'),
    [Input('selected-carriers-store', 'children'),
     Input('route-carrier-filter', 'value')]
)
def update_route_performance_matrix(selected_carriers_json, carrier_filter):
    """Route Performance Matrix"""
    return create_route_performance_matrix(selected_carriers_json, carrier_filter)

@callback(
    Output('hub-connectivity-chart', 'figure'),
    [Input('selected-carriers-store', 'children'),
     Input('route-carrier-filter', 'value')]
)
def update_hub_connectivity(selected_carriers_json, carrier_filter):
    """Hub Connectivity Network"""
    return create_hub_connectivity_network(selected_carriers_json, carrier_filter)

@callback(
    Output('seasonal-patterns-chart', 'figure'),
    [Input('selected-carriers-store', 'children'),
     Input('route-carrier-filter', 'value')]
)
def update_seasonal_patterns(selected_carriers_json, carrier_filter):
    """Seasonal Delay Patterns"""
    return create_seasonal_analysis(selected_carriers_json, carrier_filter)

def create_route_performance_matrix(selected_carriers_json, carrier_filter):
    """Create a route performance matrix showing distance vs frequency vs delay cost"""
    route_path = Path('outputs/route_summary.csv')
    if not route_path.exists():
        return _empty_figure("Route summary CSV not found")
    
    try:
        route_df = pd.read_csv(route_path)
        
        # Apply carrier filters
        try:
            selected = json.loads(selected_carriers_json) if selected_carriers_json else None
        except Exception:
            selected = None

        carriers_to_filter = carrier_filter if carrier_filter else selected
        if carriers_to_filter and 'primary_carrier' in route_df.columns:
            route_df = route_df[route_df['primary_carrier'].isin(carriers_to_filter)]
        
        # Calculate metrics
        route_df['flights_per_day'] = route_df['num_flights'] / 365  # Approximate daily flights
        route_df['cost_per_mile'] = route_df['total_delay_cost'] / route_df['distance']
        route_df['cost_per_flight'] = route_df['total_delay_cost'] / route_df['num_flights']
        
        # Categorize routes by distance
        route_df['distance_category'] = pd.cut(route_df['distance'], 
                                             bins=[0, 500, 1500, 5000], 
                                             labels=['Short (<500mi)', 'Medium (500-1500mi)', 'Long (>1500mi)'])
        
        # Create scatter plot
        fig = go.Figure()
        
        colors = {'Short (<500mi)': COLORS['success'], 
                 'Medium (500-1500mi)': COLORS['warning'], 
                 'Long (>1500mi)': COLORS['danger']}
        
        for category in route_df['distance_category'].unique():
            if pd.notna(category):
                cat_data = route_df[route_df['distance_category'] == category]
                
                fig.add_trace(go.Scatter(
                    x=cat_data['flights_per_day'],
                    y=cat_data['cost_per_flight'],
                    mode='markers',
                    marker=dict(
                        size=cat_data['distance'] / 50,  # Size by distance
                        color=colors.get(category, COLORS['primary']),
                        opacity=0.7,
                        line=dict(width=1, color='white')
                    ),
                    name=category,
                    text=cat_data['route'],
                    hovertemplate='<b>%{text}</b><br>' +
                                'Flights/day: %{x:.1f}<br>' +
                                'Cost/flight: $%{y:.0f}<br>' +
                                'Distance: %{marker.size:.0f} mi<extra></extra>'
                ))
        
        fig.update_layout(
            title='Route Performance Matrix: Frequency vs Cost Efficiency',
            xaxis_title='Average Flights per Day',
            yaxis_title='Delay Cost per Flight ($)',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, sans-serif', color=COLORS['text_secondary']),
            legend=dict(title='Route Distance'),
            hovermode='closest'
        )
        
        return fig
        
    except Exception as e:
        return _empty_figure(f"Error creating performance matrix: {str(e)}")

def create_hub_connectivity_network(selected_carriers_json, carrier_filter):
    """Create a network diagram showing hub connectivity and efficiency"""
    route_path = Path('outputs/route_summary.csv')
    if not route_path.exists():
        return _empty_figure("Route summary CSV not found")
    
    try:
        route_df = pd.read_csv(route_path)
        
        # Apply carrier filters
        try:
            selected = json.loads(selected_carriers_json) if selected_carriers_json else None
        except Exception:
            selected = None

        carriers_to_filter = carrier_filter if carrier_filter else selected
        if carriers_to_filter and 'primary_carrier' in route_df.columns:
            route_df = route_df[route_df['primary_carrier'].isin(carriers_to_filter)]
        
        # Parse routes to get airports
        airports = {}
        for _, row in route_df.iterrows():
            parts = row['route'].split('-')
            if len(parts) >= 2:
                origin, dest = parts[0], parts[1]
                
                # Track airport metrics
                for airport in [origin, dest]:
                    if airport not in airports:
                        airports[airport] = {
                            'routes': 0,
                            'total_flights': 0,
                            'total_delay_cost': 0,
                            'connections': set()
                        }
                    
                    airports[airport]['routes'] += 1
                    airports[airport]['total_flights'] += row['num_flights']
                    airports[airport]['total_delay_cost'] += row['total_delay_cost']
                    
                    # Track connections
                    other_airport = dest if airport == origin else origin
                    airports[airport]['connections'].add(other_airport)
        
        # Convert to DataFrame for easier plotting
        airport_data = []
        for code, data in airports.items():
            airport_data.append({
                'airport': code,
                'routes': data['routes'],
                'total_flights': data['total_flights'],
                'total_delay_cost': data['total_delay_cost'],
                'connections': len(data['connections']),
                'avg_cost_per_flight': data['total_delay_cost'] / data['total_flights'] if data['total_flights'] > 0 else 0
            })
        
        airport_df = pd.DataFrame(airport_data)
        
        # Create bubble chart with simplified color approach
        fig = go.Figure()
        
        # Clean and validate data
        airport_df['avg_cost_per_flight'] = airport_df['avg_cost_per_flight'].fillna(0)
        airport_df['total_flights'] = airport_df['total_flights'].fillna(0)
        
        # Create discrete color categories instead of continuous scale
        # Categorize airports by efficiency
        cost_values = airport_df['avg_cost_per_flight']
        cost_percentiles = cost_values.quantile([0.33, 0.67])
        
        def get_efficiency_category(cost):
            if cost <= cost_percentiles.iloc[0]:
                return 'High Efficiency'
            elif cost <= cost_percentiles.iloc[1]:
                return 'Medium Efficiency'
            else:
                return 'Low Efficiency'
        
        airport_df['efficiency_category'] = airport_df['avg_cost_per_flight'].apply(get_efficiency_category)
        
        # Color mapping
        color_map = {
            'High Efficiency': COLORS['success'],
            'Medium Efficiency': COLORS['warning'], 
            'Low Efficiency': COLORS['danger']
        }
        
        # Create size array with validation
        flight_sizes = (airport_df['total_flights'] / 1000).clip(lower=1, upper=50)
        
        # Add traces by category for better legend
        for category in ['High Efficiency', 'Medium Efficiency', 'Low Efficiency']:
            cat_data = airport_df[airport_df['efficiency_category'] == category]
            if not cat_data.empty:
                # Calculate sizes properly to avoid the color error
                sizes = (cat_data['total_flights'] / 1000).clip(lower=1, upper=40).tolist()
                
                fig.add_trace(go.Scatter(
                    x=cat_data['connections'],
                    y=cat_data['routes'],
                    mode='markers+text',
                    marker=dict(
                        size=sizes,
                        color=color_map[category],
                        line=dict(width=1, color='white'),
                        sizemin=8,
                        sizemode='diameter',
                        opacity=0.8
                    ),
                    text=cat_data['airport'],
                    textposition='middle center',
                    textfont=dict(size=9, color='white', family='Inter, sans-serif'),
                    name=category,
                    hovertemplate='<b>%{text}</b><br>' +
                                'Connections: %{x}<br>' +
                                'Routes: %{y}<br>' +
                                'Total Flights: %{customdata[0]:,.0f}<br>' +
                                'Avg Cost/Flight: $%{customdata[1]:.0f}<br>' +
                                'Efficiency: %{customdata[2]}<extra></extra>',
                    customdata=list(zip(cat_data['total_flights'].tolist(), 
                                       cat_data['avg_cost_per_flight'].tolist(),
                                       cat_data['efficiency_category'].tolist()))
                ))
        
        fig.update_layout(
            title='Hub Connectivity Analysis: Network Size vs Efficiency',
            xaxis_title='Number of Connected Airports',
            yaxis_title='Number of Routes',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, sans-serif', color=COLORS['text_secondary']),
            hovermode='closest'
        )
        
        return fig
        
    except Exception as e:
        return _empty_figure(f"Error creating hub network: {str(e)}")

def create_seasonal_analysis(selected_carriers_json, carrier_filter):
    """Create seasonal delay pattern analysis"""
    full_path = Path('outputs/full_dataset_for_tableau.csv')
    if not full_path.exists():
        return _empty_figure("Full dataset CSV not found")
    
    try:
        # Better sampling strategy to ensure all 12 months are represented
        # Read smaller chunks more frequently to get better month distribution
        chunk_size = 300000
        max_chunks = 20  # Read more chunks to ensure we get all months
        
        chunks = []
        months_found = set()
        chunk_count = 0
        
        for chunk in pd.read_csv(full_path, chunksize=chunk_size):
            chunk_count += 1
            chunk_months = set(chunk['Month'].unique())
            months_found.update(chunk_months)
            
            # Sample from each chunk
            chunk_sample = chunk.sample(n=min(25000, len(chunk)), random_state=42)
            chunks.append(chunk_sample)
            
            # Continue until we have all 12 months or hit max chunks
            if len(months_found) == 12 or chunk_count >= max_chunks:
                break
        
        df = pd.concat(chunks, ignore_index=True)
        
        # Log what months we found for debugging
        final_months = sorted(df['Month'].unique())
        print(f"Seasonal analysis found months: {final_months}")
        
        # Apply carrier filters
        try:
            selected = json.loads(selected_carriers_json) if selected_carriers_json else None
        except Exception:
            selected = None

        carriers_to_filter = carrier_filter if carrier_filter else selected
        if carriers_to_filter and 'Carrier' in df.columns:
            df = df[df['Carrier'].isin(carriers_to_filter)]
        
        # Create route column and date
        if 'route' not in df.columns:
            df['route'] = df['Origin'] + '-' + df['Dest']
        
        # Use existing month column if available, otherwise create from date
        if 'Month' in df.columns:
            df['month'] = df['Month']
        else:
            df['date'] = pd.to_datetime(df[['Year', 'Month', 'DayofMonth']].rename(columns={'DayofMonth': 'day'}))
            df['month'] = df['date'].dt.month
        
        # Get top routes by volume
        top_routes = df['route'].value_counts().head(15).index
        df_filtered = df[df['route'].isin(top_routes)]
        
        if df_filtered.empty:
            return _empty_figure("No route data available after filtering")
        
        # Aggregate by route and month
        monthly_delays = df_filtered.groupby(['route', 'month'])['delay_cost'].mean().reset_index()
        
        if monthly_delays.empty:
            return _empty_figure("No monthly delay data available")
        
        # Pivot for heatmap
        heatmap_data = monthly_delays.pivot(index='route', columns='month', values='delay_cost')
        
        # Fill missing months with 0 and ensure we have proper month labels
        month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                      7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
        
        # Reindex to include all months that exist in the dataset (fill missing with NaN)
        available_months = sorted(df['month'].unique())
        all_months = list(range(1, 13))  # Still show all 12 months for context
        heatmap_data = heatmap_data.reindex(columns=all_months)
        
        # Create month labels
        month_labels = [month_names.get(i, f'Month {i}') for i in heatmap_data.columns]
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=month_labels,
            y=heatmap_data.index,
            colorscale='RdYlGn_r',
            showscale=True,
            colorbar=dict(title='Avg Delay<br>Cost ($)'),
            hovertemplate='Route: %{y}<br>Month: %{x}<br>Avg Delay Cost: $%{z:.0f}<extra></extra>',
            zmin=0  # Set minimum to 0 for better color scaling
        ))
        
        fig.update_layout(
            title='Seasonal Delay Patterns by Route',
            xaxis_title='Month',
            yaxis_title='Route',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, sans-serif', color=COLORS['text_secondary'])
        )
        
        return fig
        
    except Exception as e:
        return _empty_figure(f"Error creating seasonal analysis: {str(e)}")






# ============================================================================
# PREMIUM CSS STYLING
# ============================================================================

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@600;700;800&family=Roboto+Mono:wght@500;600&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #0A1F44 0%, #1e3a5f 50%, #F8FAFC 100%);
                min-height: 100vh;
                color: #1E293B;
            }

            .dashboard-container-premium {
                min-height: 100vh;
            }

            /* Header Styling */
            .header-premium {
                background: linear-gradient(135deg, #0A1F44 0%, #1e3a5f 100%);
                padding: 24px 20px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                position: relative;
                overflow: hidden;
            }

            .header-premium::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="1" fill="rgba(255,255,255,0.1)"/></svg>');
                opacity: 0.3;
            }

            .header-content-premium {
                max-width: 1400px;
                margin: 0 auto;
                position: relative;
                z-index: 1;
            }

            .header-title-premium {
                color: white;
                font-family: 'Montserrat', sans-serif;
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            }

            .header-subtitle-premium {
                color: rgba(255, 255, 255, 0.9);
                font-size: 15px;
                font-weight: 400;
                letter-spacing: 0.5px;
                text-align: center;
            }

            /* Main Container */
            .main-container-premium {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }

            /* KPI Cards */
            .kpi-row-premium {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 16px;
                margin-bottom: 20px;
            }

            .kpi-card-premium {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            }

            .kpi-card-premium:hover {
                transform: translateY(-8px);
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
            }

            .kpi-card-premium::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #00D9FF 0%, #10B981 100%);
                opacity: 0;
                transition: opacity 0.3s;
            }

            .kpi-card-premium:hover::before {
                opacity: 1;
            }

            .kpi-icon {
                font-size: 32px;
                margin-bottom: 12px;
                display: inline-block;
            }

            .kpi-title {
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1.2px;
                color: #64748B;
                margin-bottom: 12px;
            }

            .kpi-value {
                font-family: 'Roboto Mono', monospace;
                font-size: 36px;
                font-weight: 600;
                color: #0A1F44;
                margin-bottom: 6px;
                line-height: 1;
            }

            .kpi-subtitle {
                font-size: 14px;
                color: #64748B;
                font-weight: 500;
            }

            /* Filter Section */
            .filter-section-premium {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 16px 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }

            .filter-label-premium {
                font-weight: 600;
                font-size: 14px;
                color: #1E293B;
                margin-bottom: 12px;
                display: block;
            }

            .dropdown-premium .Select-control {
                border-radius: 10px !important;
                border-color: #E2E8F0 !important;
            }

            /* Airline Key Section */
            .airline-key-section-premium {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }

            .key-title-premium {
                font-family: 'Montserrat', sans-serif;
                font-size: 18px;
                font-weight: 700;
                color: #0A1F44;
                margin-bottom: 16px;
            }

            .airline-key-grid-premium {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 12px;
            }

            .airline-key-item-premium {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 16px;
                background: #F8FAFC;
                border-radius: 8px;
                border: 2px solid transparent;
                transition: all 0.2s ease;
            }

            .airline-key-clickable {
                cursor: pointer;
                user-select: none;
            }

            .airline-key-clickable:hover {
                background: #E2E8F0;
                transform: translateY(-2px);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }

            .airline-key-item-premium.active {
                background: #D1FAE5 !important;
                border-color: #10B981 !important;
            }

            .airline-key-item-premium.active .airline-code-premium {
                background: #10B981 !important;
                color: white !important;
            }

            .airline-code-premium {
                font-family: 'Roboto Mono', monospace;
                font-size: 14px;
                font-weight: 600;
                color: #0A1F44;
                background: white;
                padding: 6px 10px;
                border-radius: 4px;
                min-width: 40px;
                text-align: center;
                transition: all 0.2s ease;
            }

            .airline-name-premium {
                font-size: 14px;
                color: #64748B;
                flex: 1;
                font-weight: 500;
            }

            .airline-flights-premium {
                font-size: 12px;
                color: #94A3B8;
                font-weight: 400;
            }

            /* AI Insights Card */
            .ai-insights-card-premium {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 16px;
                padding: 32px;
                margin-bottom: 24px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            }

            .ai-insights-card-premium::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #00D9FF 0%, #10B981 50%, #00D9FF 100%);
                background-size: 200% 100%;
                animation: shimmer 3s linear infinite;
            }

            @keyframes shimmer {
                0% { background-position: 200% 0; }
                100% { background-position: -200% 0; }
            }

            .ai-insights-card-premium:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 32px rgba(0, 217, 255, 0.15);
            }

            .ai-insights-text {
                font-size: 15px;
                line-height: 1.9;
                color: #1E293B;
                margin-top: 12px;
                word-wrap: break-word;
                overflow-wrap: break-word;
                white-space: pre-wrap;
            }

            .ai-insights-text p {
                margin: 16px 0;
            }

            .ai-insights-text ol, .ai-insights-text ul {
                margin: 12px 0;
                padding-left: 24px;
            }

            .ai-insights-text li {
                margin: 12px 0;
                padding-left: 8px;
            }

            .ai-insights-text strong {
                color: #00D9FF;
                font-weight: 700;
            }

            .insights-markdown {
                padding: 16px 0;
                word-wrap: break-word;
                overflow-wrap: break-word;
                white-space: normal;
                max-width: 100%;
            }

            .insights-markdown p {
                margin: 14px 0;
                line-height: 1.8;
                white-space: normal;
                word-wrap: break-word;
            }

            .insights-markdown ol, .insights-markdown ul {
                margin: 12px 0;
                padding-left: 28px;
            }

            .insights-markdown li {
                margin: 14px 0;
                padding-left: 8px;
                line-height: 1.8;
                white-space: normal;
                word-wrap: break-word;
            }

            .insights-markdown strong {
                color: #00D9FF;
                font-weight: 700;
            }

            .insights-markdown code {
                background: rgba(0, 217, 255, 0.1);
                padding: 3px 8px;
                border-radius: 6px;
                font-family: 'Roboto Mono', monospace;
                font-size: 13px;
                color: #0A1F44;
                border: 1px solid rgba(0, 217, 255, 0.2);
            }

            /* Chatbot Card */
            .chat-card-premium {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 16px;
                padding: 32px;
                margin-bottom: 24px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            }

            .chat-card-premium::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #9333EA 0%, #3B82F6 50%, #9333EA 100%);
                background-size: 200% 100%;
                animation: shimmer 3s linear infinite;
            }

            .chat-card-premium:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 32px rgba(147, 51, 234, 0.15);
            }

            .chat-input-premium {
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                padding: 16px;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                resize: vertical;
                transition: all 0.3s;
                background: white;
            }

            .chat-input-premium:focus {
                outline: none;
                border-color: #9333EA;
                box-shadow: 0 0 0 4px rgba(147, 51, 234, 0.1);
                background: #FEFEFF;
            }

            .chat-submit-btn-premium {
                background: linear-gradient(135deg, #9333EA 0%, #3B82F6 100%);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 14px 36px;
                font-family: 'Inter', sans-serif;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                box-shadow: 0 6px 20px rgba(147, 51, 234, 0.3);
            }

            .chat-submit-btn-premium:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 28px rgba(147, 51, 234, 0.4);
            }

            .chat-submit-btn-premium:active {
                transform: translateY(0);
            }

            .chat-response-premium {
                margin-top: 24px;
                padding: 20px;
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(249, 250, 251, 0.9) 100%);
                border-radius: 12px;
                border-left: 4px solid #9333EA;
                min-height: 80px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
                word-wrap: break-word;
                overflow-wrap: break-word;
            }

            .chat-response-premium .markdown {
                font-size: 15px;
                line-height: 1.8;
                color: #1E293B;
            }

            .chat-response-premium p {
                margin: 12px 0;
                white-space: pre-wrap;
            }

            .chat-response-premium strong {
                color: #9333EA;
                font-weight: 700;
            }

            /* Large Chart Cards (Full Width) */
            .chart-card-premium-large {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                min-height: 600px;
                height: 700px;
                display: flex;
                flex-direction: column;
                margin-bottom: 20px;
            }

            .chart-card-premium-large:hover {
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
            }

            /* Fix chart container to prevent overflow */
            .chart-card-premium-large .js-plotly-plot {
                width: 100% !important;
                flex: 1;
                min-height: 500px;
            }

            .chart-card-premium-large .plotly {
                width: 100% !important;
                height: 100% !important;
            }

            .chart-card-premium-large .svg-container {
                width: 100% !important;
                height: 100% !important;
            }

            .chart-header-premium {
                margin-bottom: 12px;
                flex-shrink: 0;
            }

            .chart-title-premium {
                font-family: 'Montserrat', sans-serif;
                font-size: 16px;
                font-weight: 700;
                color: #0A1F44;
                margin-bottom: 4px;
            }

            .chart-subtitle-premium {
                font-size: 12px;
                color: #64748B;
                font-weight: 500;
            }

            /* Footer */
            .footer-premium {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 16px;
                margin-top: 16px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }

            .footer-text-premium {
                text-align: center;
                color: #64748B;
                font-size: 14px;
                line-height: 1.6;
            }

            /* Responsive Design */
            @media (max-width: 1200px) {
                .chart-row-premium {
                    grid-template-columns: 1fr;
                }
            }

            @media (max-width: 768px) {
                .header-title-premium {
                    font-size: 32px;
                }

                .kpi-row-premium {
                    grid-template-columns: 1fr;
                }

                .kpi-value {
                    font-size: 36px;
                }
            }

            /* Loading Animation - fade only, no transform to prevent layout shift */
            @keyframes fadeIn {
                from {
                    opacity: 0;
                }
                to {
                    opacity: 1;
                }
            }

            .kpi-card-premium,
            .chart-card-premium,
            .filter-section-premium {
                animation: fadeIn 0.4s ease-out backwards;
            }

            .kpi-card-premium:nth-child(1) { animation-delay: 0.05s; }
            .kpi-card-premium:nth-child(2) { animation-delay: 0.10s; }
            .kpi-card-premium:nth-child(3) { animation-delay: 0.15s; }
            .kpi-card-premium:nth-child(4) { animation-delay: 0.20s; }
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
    print("Starting Delaynomics Enhanced Dashboard")
    print("="*60)
    print(f"\nLoaded {len(airline_df)} airlines")
    print(f"Loaded {len(airport_df)} airports")
    if flights_df is not None:
        print(f"Loaded {len(flights_df):,} flights")
    print(f"\nEnhanced Dashboard: http://localhost:8050")
    print("Press CTRL+C to quit\n")

    app.run(
        debug=True,
        host='0.0.0.0',
        port=8050
    )
"""
Delaynomics Premium Dashboard - Modern Design
Aviation-themed interactive dashboard with glassmorphism UI
"""

import dash
from dash import dcc, html, Input, Output, callback, State, ALL, ctx, MATCH
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# DATA LOADING
# ============================================================================

def load_data():
    """Load pre-computed summary data from outputs folder"""
    try:
        airline_summary = pd.read_csv('outputs/airline_summary.csv')
        airport_summary = pd.read_csv('outputs/airport_summary.csv')

        full_data_path = Path('outputs/full_dataset_for_tableau.csv')
        if full_data_path.exists():
            full_data = pd.read_csv(full_data_path)
            # Compute day of week
            full_data['date'] = pd.to_datetime(full_data[['Year', 'Month', 'DayofMonth']].rename(
                columns={'DayofMonth': 'day'}))
            full_data['day_of_week'] = full_data['date'].dt.dayofweek
            full_data['day_name'] = full_data['date'].dt.day_name()
        else:
            full_data = None

        return airline_summary, airport_summary, full_data

    except FileNotFoundError as e:
        print("❌ Error: CSV files not found in outputs/ directory")
        print("   Run notebooks/analysis.ipynb first to generate the data")
        raise e

# Load data
airline_df, airport_df, flights_df = load_data()

# Compute day-of-week statistics
if flights_df is not None:
    dow_stats = flights_df.groupby('day_name').agg({
        'ArrDelay': 'mean',
        'delay_cost': 'mean',
        'is_delayed': 'mean'
    }).reset_index()
    # Order by day of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_stats['day_of_week'] = dow_stats['day_name'].apply(lambda x: day_order.index(x))
    dow_stats = dow_stats.sort_values('day_of_week')
else:
    dow_stats = None

# ============================================================================
# GEMINI AI CONFIGURATION
# ============================================================================

# Configure Gemini API (optional - will degrade gracefully if not available)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
gemini_model = None

if GEMINI_API_KEY:
    
        
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Use correct model names
        model_names = [
            'gemini-2.0-flash-exp',  # Latest
            'gemini-1.5-flash',      # Stable
            'gemini-1.5-pro'         # Fallback
        ]
        
        for model_name in model_names:
            try:
                gemini_model = genai.GenerativeModel(model_name)
                print(f"✓ Gemini AI enabled (using {model_name})")
                break
            except Exception as e:
                continue
                
        if not gemini_model:
            raise Exception("No compatible model found")
    except Exception as e:
        print(f"WARNING: Gemini AI unavailable: {e}")
        gemini_model = None
else:
    print("WARNING: GEMINI_API_KEY not set - AI features disabled")

def generate_ai_insights(airline_summary):
    """Generate AI-powered insights from airline data"""
    if not gemini_model:
        return "**AI Insights Unavailable**\n\nSet the `GEMINI_API_KEY` in your `.env` file to enable AI-powered insights.\n\n**How to enable:**\n1. Get API key from: https://makersuite.google.com/app/apikey\n2. Add to `.env` file: `GEMINI_API_KEY=your-key-here`\n3. Restart the dashboard"

    try:
        #gemini_model = 'gemini-2.0-flash'
        # Prepare data summary - format numbers nicely to avoid recitation issues
        top_5_df = airline_summary.nsmallest(5, 'avg_cost_per_mile')[['Carrier', 'avg_cost_per_mile', 'avg_delay_min', 'delay_rate']].copy()
        top_5_df['avg_cost_per_mile'] = top_5_df['avg_cost_per_mile'].round(2)
        top_5_df['avg_delay_min'] = top_5_df['avg_delay_min'].round(1)
        top_5_df['delay_rate'] = (top_5_df['delay_rate'] * 100).round(1)

        worst_3_df = airline_summary.nlargest(3, 'avg_cost_per_mile')[['Carrier', 'avg_cost_per_mile', 'avg_delay_min', 'delay_rate']].copy()
        worst_3_df['avg_cost_per_mile'] = worst_3_df['avg_cost_per_mile'].round(2)
        worst_3_df['avg_delay_min'] = worst_3_df['avg_delay_min'].round(1)
        worst_3_df['delay_rate'] = (worst_3_df['delay_rate'] * 100).round(1)

        prompt = f"""Analyze this airline data and provide exactly 3 brief insights:

Best performers: {top_5_df.to_string(index=False)}
Worst performers: {worst_3_df.to_string(index=False)}

Write exactly 3 points (1 sentence each):
1. Best airline and why
2. Worst airline and why
3. One key travel tip

Be brief and use specific numbers from the data."""

        # Configure safety settings to be more permissive for business data
        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        response = gemini_model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.5,
                'top_p': 0.9,
                'top_k': 20,
                'max_output_tokens': 512,
            },
            safety_settings=safety_settings
        )

        # Check if response was blocked or has no text
        if not response.candidates or not response.candidates[0].content.parts:
            raise Exception("Response was blocked or empty")

        # Extract all text from all parts
        full_text = ""
        candidate = response.candidates[0]

        for part in candidate.content.parts:
            if hasattr(part, 'text'):
                full_text += part.text

        # Log finish reason and response length for debugging
        print(f"DEBUG: AI response finish_reason: {candidate.finish_reason}, length: {len(full_text)}")
        print(f"DEBUG: Response text: {full_text[:200]}...")

        # Check if response is incomplete (finish_reason != 1 means not normal STOP)
        if candidate.finish_reason and candidate.finish_reason != 1:
            print(f"WARNING: AI response incomplete (finish_reason: {candidate.finish_reason})")

        if not full_text:
            raise Exception("No text content in response")

        return full_text

    except Exception as e:
        # Provide fallback insights when AI fails
        best = airline_summary.nsmallest(1, 'avg_cost_per_mile').iloc[0]
        worst = airline_summary.nlargest(1, 'avg_cost_per_mile').iloc[0]

        fallback = f"""
**AI temporarily unavailable** - showing basic analysis instead:

1. **Best Performer**: {best['Carrier']} with ${best['avg_cost_per_mile']:.2f} per mile ({best['delay_rate']*100:.1f}% delay rate)

2. **Worst Performer**: {worst['Carrier']} with ${worst['avg_cost_per_mile']:.2f} per mile ({worst['delay_rate']*100:.1f}% delay rate)

3. **Tip**: Check the charts below for detailed comparisons across all carriers.

*Error details: {str(e)}*
"""
        return fallback

# ============================================================================
# CONSTANTS & STYLING
# ============================================================================

# Brand colors - Aviation Premium theme
COLORS = {
    'primary': '#0A1F44',      # Deep navy blue
    'accent': '#00D9FF',       # Vibrant cyan
    'success': '#10B981',      # Emerald green
    'warning': '#F59E0B',      # Amber
    'danger': '#FF6B6B',       # Coral red
    'background': '#F8FAFC',   # Soft off-white
    'card': '#FFFFFF',         # Pure white
    'text_primary': '#1E293B', # Slate 800
    'text_secondary': '#64748B' # Slate 500
}

# Chart colors for airlines
AIRLINE_COLORS = ['#00D9FF', '#10B981', '#F59E0B', '#FF6B6B', '#9333EA']

# Airline name mapping (2-letter code to full name)
AIRLINE_NAMES = {
    'AA': 'American Airlines',
    'AS': 'Alaska Airlines',
    'B6': 'JetBlue Airways',
    'DL': 'Delta Air Lines',
    'F9': 'Frontier Airlines',
    'G4': 'Allegiant Air',
    'HA': 'Hawaiian Airlines',
    'NK': 'Spirit Airlines',
    'UA': 'United Airlines',
    'WN': 'Southwest Airlines',
    'OO': 'SkyWest Airlines',
    'YX': 'Republic Airways',
    '9E': 'Endeavor Air',
    'YV': 'Mesa Airlines'
}

# ============================================================================
# DASH APP SETUP
# ============================================================================

app = dash.Dash(
    __name__,
    title="Delaynomics Premium",
    update_title="Loading...",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_kpi_card(icon, title, value, subtitle, trend=None, color='accent'):
    """Create a premium KPI card with optional trend"""

    trend_indicator = html.Div()
    if trend:
        trend_color = COLORS['success'] if trend > 0 else COLORS['danger']
        trend_symbol = '↑' if trend > 0 else '↓'
        trend_indicator = html.Div([
            html.Span(f"{trend_symbol} {abs(trend)}%",
                     style={'color': trend_color, 'fontSize': '14px', 'fontWeight': '600'})
        ], style={'marginTop': '8px'})

    return html.Div([
        html.Div([
            html.Div(icon, className=f'kpi-icon kpi-{color}'),
            html.Div(title, className='kpi-title'),
            html.Div(value, className='kpi-value'),
            html.Div(subtitle, className='kpi-subtitle'),
            trend_indicator
        ])
    ], className='kpi-card-premium')

# ============================================================================
# LAYOUT
# ============================================================================

app.layout = html.Div([
    # Header with gradient background
    html.Div([
        html.Div([
            html.H1("Delaynomics", className="header-title-premium"),
            html.P(
                "Which airlines deliver the best value for money?",
                className="header-subtitle-premium"
            ),
        ], className="header-content-premium"),
    ], className="header-premium"),

    # Main container
    html.Div([
        # KPI Cards Row
        html.Div([
            create_kpi_card(
                "",
                "BEST CARRIER",
                airline_df.iloc[0]['Carrier'],
                f"${airline_df.iloc[0]['avg_cost_per_mile']:.2f} per mile",
                trend=-42,
                color='success'
            ),
            create_kpi_card(
                "",
                "WORST CARRIER",
                airline_df.iloc[-1]['Carrier'],
                f"${airline_df.iloc[-1]['avg_cost_per_mile']:.2f} per mile",
                trend=+69,
                color='danger'
            ),
            create_kpi_card(
                "",
                "AVG DELAY COST",
                f"${airline_df['avg_delay_cost'].mean():.0f}",
                "per delayed flight",
                color='warning'
            ),
            create_kpi_card(
                "",
                "TOTAL FLIGHTS",
                f"{airline_df['num_flights'].sum():,}",
                "flights analyzed",
                color='primary'
            ),
        ], className="kpi-row-premium"),

        # AI Insights Card
        html.Div([
            html.Div([
                html.H3("AI-Powered Insights", className="chart-title-premium"),
                html.P("Generated using Gemini AI", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            html.Div(id='ai-insights-content', className="ai-insights-text"),
            dcc.Loading(
                id="loading-insights",
                type="circle",
                children=html.Div(id="insights-loading-output")
            ),
        ], className="ai-insights-card-premium"),

        # Interactive Airline Filter (replaces dropdown)
        html.Div([
            html.H4("Select Airlines to Compare (click to filter)", className="key-title-premium"),
            html.Div([
                html.Div([
                    html.Span(f"{code}", className="airline-code-premium"),
                    html.Span(f"{AIRLINE_NAMES.get(code, code)}", className="airline-name-premium"),
                    html.Span(f"{airline_df[airline_df['Carrier']==code]['num_flights'].values[0]:,} flights",
                             className="airline-flights-premium")
                ], id={'type': 'airline-filter-item', 'index': code},
                   className="airline-key-item-premium airline-key-clickable active",
                   n_clicks=0)
                for code in sorted(airline_df['Carrier'].unique())
            ], className="airline-key-grid-premium"),
            # Hidden div to store selected carriers
            html.Div(id='selected-carriers-store', style={'display': 'none'}),
        ], className="airline-key-section-premium"),

        # Chart 1 - Full Width
        html.Div([
            html.Div([
                html.H3("Cost Efficiency Ranking", className="chart-title-premium"),
                html.P("Lower cost per mile = better value", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            dcc.Graph(
                id='airline-efficiency-chart',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large"),

        # Chart 2 - Full Width
        html.Div([
            html.Div([
                html.H3("Airport Performance", className="chart-title-premium"),
                html.P("Delay costs by origin airport", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            dcc.Graph(
                id='airport-performance-chart',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large"),

        # Chart 3 - Full Width
        html.Div([
            html.Div([
                html.H3("Efficiency Matrix", className="chart-title-premium"),
                html.P("Delay rate vs. cost efficiency", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            dcc.Graph(
                id='delay-rate-scatter',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large"),

        # Chart 4 - Full Width
        html.Div([
            html.Div([
                html.H3("Carrier Comparison", className="chart-title-premium"),
                html.P("Average delay cost by carrier", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            dcc.Graph(
                id='cost-comparison-chart',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large"),

        # Chart 5 - Day of Week Analysis (NEW)
        html.Div([
            html.Div([
                html.H3("Day of Week Performance", className="chart-title-premium"),
                html.P("When should you fly to minimize delays?", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            dcc.Graph(
                id='day-of-week-chart',
                config={'displayModeBar': False, 'responsive': True},
                style={'height': '100%', 'width': '100%'}
            ),
        ], className="chart-card-premium-large") if dow_stats is not None else html.Div(),

        # Interactive Chatbot Section (NEW)
        html.Div([
            html.Div([
                html.H3("Ask the AI Analyst", className="chart-title-premium"),
                html.P("Ask questions about the data", className="chart-subtitle-premium"),
            ], className="chart-header-premium"),
            html.Div([
                dcc.Textarea(
                    id='chat-input',
                    placeholder='Ask a question like: "Which airline is best for cross-country flights?" or "Why does JetBlue have higher delays?"',
                    className="chat-input-premium",
                    style={'width': '100%', 'height': '100px', 'marginBottom': '12px'}
                ),
                html.Button('Ask AI', id='chat-submit-btn', n_clicks=0, className="chat-submit-btn-premium"),
            ]),
            dcc.Loading(
                id="loading-chat",
                type="circle",
                children=html.Div(id='chat-response', className="chat-response-premium")
            ),
        ], className="chat-card-premium"),

        # Footer
        html.Div([
            html.Div([
                html.Span("Data Source: ", style={'fontWeight': '600'}),
                html.Span("Bureau of Transportation Statistics"),
                html.Span(" | ", style={'margin': '0 10px'}),
                html.Span("Cost Model: ", style={'fontWeight': '600'}),
                html.A("$47.10/hour (FAA VOT)", href="https://www.faa.gov/sites/faa.gov/files/regulations_policies/policy_guidance/benefit_cost/econ-value-section-1-tx-time.pdf", target="_blank", style={'color': COLORS['accent'], 'textDecoration': 'none', 'fontWeight': '600'}),
                html.Span(" | ", style={'margin': '0 10px'}),
                html.Span("Analysis: ", style={'fontWeight': '600'}),
                html.Span(f"{airline_df['num_flights'].sum():,} flights"),
            ], className="footer-text-premium")
        ], className="footer-premium"),

    ], className="main-container-premium"),

], className="dashboard-container-premium")

# ============================================================================
# CALLBACKS
# ============================================================================

# Store to track selected carriers
selected_carriers_set = set(airline_df['Carrier'].unique())

@callback(
    [Output({'type': 'airline-filter-item', 'index': ALL}, 'className'),
     Output('selected-carriers-store', 'children')],
    Input({'type': 'airline-filter-item', 'index': ALL}, 'n_clicks'),
    State({'type': 'airline-filter-item', 'index': ALL}, 'id'),
    prevent_initial_call=False
)
def toggle_airline_selection(n_clicks_list, ids):
    """Toggle airline selection on click"""
    global selected_carriers_set

    # Initialize on first load
    if not ctx.triggered_id:
        # All carriers active by default
        classnames = ["airline-key-item-premium airline-key-clickable active" for _ in ids]
        return classnames, json.dumps(list(selected_carriers_set))

    # Handle click
    clicked_id = ctx.triggered_id
    clicked_carrier = clicked_id['index']

    # Toggle carrier in set
    if clicked_carrier in selected_carriers_set:
        selected_carriers_set.remove(clicked_carrier)
    else:
        selected_carriers_set.add(clicked_carrier)

    # Update class names
    classnames = []
    for id_dict in ids:
        carrier = id_dict['index']
        if carrier in selected_carriers_set:
            classnames.append("airline-key-item-premium airline-key-clickable active")
        else:
            classnames.append("airline-key-item-premium airline-key-clickable")

    return classnames, json.dumps(list(selected_carriers_set))

@callback(
    Output('ai-insights-content', 'children'),
    Input('selected-carriers-store', 'children')
)
def update_ai_insights(trigger):
    """Generate AI insights on page load"""
    insights_text = generate_ai_insights(airline_df)
    return dcc.Markdown(insights_text, className="insights-markdown")

@callback(
    Output('chat-response', 'children'),
    Input('chat-submit-btn', 'n_clicks'),
    State('chat-input', 'value'),
    prevent_initial_call=True
)
def handle_chat_question(n_clicks, question):
    """Handle user questions with AI chatbot"""
    if not question or question.strip() == '':
        return dcc.Markdown("*Please enter a question above and click 'Ask AI'*")

    if not gemini_model:
        return dcc.Markdown("**Gemini API not configured**\n\nSet the `GEMINI_API_KEY` environment variable to use the chatbot.")

    try:
        # Prepare data context for the AI
        airline_context = airline_df[['Carrier', 'avg_cost_per_mile', 'avg_delay_min', 'delay_rate', 'num_flights']].to_string(index=False)
        airport_context = airport_df.nlargest(10, 'avg_delay_cost')[['Airport', 'avg_delay_cost', 'avg_delay_min']].to_string(index=False)

        dow_context = ""
        if dow_stats is not None:
            dow_context = f"\n\nDAY OF WEEK STATISTICS:\n{dow_stats[['day_name', 'ArrDelay', 'delay_cost', 'is_delayed']].to_string(index=False)}"

        prompt = f"""
        You are a flight delay data analyst. Answer this question based mostly on the data provided below, and any similar context.

        USER QUESTION: {question}

        AIRLINE PERFORMANCE DATA:
        {airline_context}

        TOP 10 WORST AIRPORTS (by delay cost):
        {airport_context}
        {dow_context}

        INSTRUCTIONS:
        - Provide a clear, data-driven answer with specific numbers from the data above
        - Use carrier codes (AA, DL, etc.) and reference actual metrics
        - If the question asks about something not in the data, answer only if it is related to the data provided. Use your insights, but mention if your answer is not entirely based on the provided data.
        - Be concise but thorough (2-4 sentences)
        - Format your response in markdown

        Answer:
        """

        # Configure safety settings
        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        response = gemini_model.generate_content(prompt, safety_settings=safety_settings)

        # Check if response was blocked or has no text
        if not response.candidates or not response.candidates[0].content.parts:
            raise Exception("Response was blocked or empty")

        # Extract all text from all parts to ensure we get the complete response
        full_text = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                full_text += part.text

        if not full_text:
            raise Exception("No text content in response")

        return dcc.Markdown(f"**Answer:**\n\n{full_text}")

    except Exception as e:
        return dcc.Markdown(f"**Error**: {str(e)}")

@callback(
    [Output('airline-efficiency-chart', 'figure'),
     Output('delay-rate-scatter', 'figure'),
     Output('cost-comparison-chart', 'figure')],
    Input('selected-carriers-store', 'children')
)
def update_airline_charts(selected_carriers_json):
    """Update airline charts with premium styling"""

    # Parse selected carriers
    if selected_carriers_json:
        try:
            selected_carriers = json.loads(selected_carriers_json)
        except:
            selected_carriers = None
    else:
        selected_carriers = None

    # Filter data
    if selected_carriers and len(selected_carriers) > 0:
        filtered_df = airline_df[airline_df['Carrier'].isin(selected_carriers)]
    else:
        filtered_df = airline_df

    # Chart 1: Airline Efficiency - Horizontal bar with gradient
    sorted_df = filtered_df.sort_values('avg_cost_per_mile')

    fig_efficiency = go.Figure()

    colors = [COLORS['success'] if x < filtered_df['avg_cost_per_mile'].median()
              else COLORS['danger'] for x in sorted_df['avg_cost_per_mile']]

    fig_efficiency.add_trace(go.Bar(
        y=sorted_df['Carrier'],
        x=sorted_df['avg_cost_per_mile'],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(width=0),
        ),
        text=[f"${x:.2f}" for x in sorted_df['avg_cost_per_mile']],
        textposition='inside',
        textfont=dict(size=12, family='Inter, sans-serif', color='white'),
        hovertemplate='<b>%{y}</b><br>Cost per mile: $%{x:.2f}<extra></extra>',
    ))

    fig_efficiency.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=COLORS['text_secondary'], size=11),
        xaxis=dict(
            title='Cost per Mile ($)',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            zeroline=False,
            automargin=True,
            fixedrange=True,
        ),
        yaxis=dict(
            title='',
            showgrid=False,
            automargin=True,
            fixedrange=True,
        ),
        margin=dict(l=50, r=50, t=30, b=60),
        autosize=True,
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Inter, sans-serif"
        )
    )

    # Chart 2: Efficiency Matrix - Scatter with quadrants
    fig_scatter = go.Figure()

    # Add quadrant lines
    median_rate = filtered_df['delay_rate'].median()
    median_cost = filtered_df['avg_cost_per_mile'].median()

    fig_scatter.add_hline(y=median_cost, line_dash="dot", line_color="rgba(0,0,0,0.2)",
                           annotation_text="", annotation_position="right")
    fig_scatter.add_vline(x=median_rate, line_dash="dot", line_color="rgba(0,0,0,0.2)",
                           annotation_text="", annotation_position="top")

    # Add regression line
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        filtered_df['delay_rate'],
        filtered_df['avg_cost_per_mile']
    )
    line_x = np.array([filtered_df['delay_rate'].min(), filtered_df['delay_rate'].max()])
    line_y = slope * line_x + intercept
    
    # Add regression line as a trace
    fig_scatter.add_trace(go.Scatter(
        x=line_x,
        y=line_y,
        mode='lines',
        name=f'Regression (R² = {r_value**2:.2f})',
        line=dict(color='rgba(100,100,100,0.5)', dash='dot'),
    
        
        hovertemplate='R² = {r_value**2:.2f}<extra></extra>'
    ))

    # Add scatter points
    fig_scatter.add_trace(go.Scatter(
        x=filtered_df['delay_rate'],
        y=filtered_df['avg_cost_per_mile'],
        mode='markers+text',
        marker=dict(
            # Scale down the size more aggressively and add limits
            size=filtered_df['num_flights'] / 1000,  # Reduced from /100 to /1000
            sizemin=10,  # Minimum size
            sizemode='area',  # Use area for more intuitive scaling
            sizeref=2. * filtered_df['num_flights'].max() / (1000**2),  # Normalize the size range
            color=filtered_df['avg_delay_min'],
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title="Avg Delay<br>(min)"),
            line=dict(width=2, color='white'),
        ),
        text=filtered_df['Carrier'],
        textposition='middle center',
        textfont=dict(size=12, color='white', family='Roboto Mono, monospace'),
        hovertemplate='<b>%{text}</b><br>Delay Rate: %{x:.1%}<br>Cost/Mile: $%{y:.2f}<extra></extra>',
    ))

    fig_scatter.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            x=-0.02,  # Position at 2% from left
            y=-0.02,  # Position at 2% from bottom
            xanchor='left',
            yanchor='bottom',
            bgcolor='rgba(255,255,255,0.8)'  # Semi-transparent white background
        ),
        font=dict(family='Inter, sans-serif', color=COLORS['text_secondary'], size=11),
        xaxis=dict(
            title='Delay Rate',
            tickformat='.0%',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            automargin=True,
            fixedrange=True,
        ),
        yaxis=dict(
            title='Cost per Mile ($)',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            automargin=True,
            fixedrange=True,
        ),
        margin=dict(l=50, r=50, t=30, b=60),
        autosize=True,
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Inter, sans-serif"
        )
    )

    # Chart 3: Cost Comparison - Grouped bars
    fig_cost = go.Figure()

    sorted_cost_df = filtered_df.sort_values('avg_delay_cost', ascending=False)

    colors_cost = [COLORS['danger'] if i < len(sorted_cost_df)//2
                   else COLORS['warning'] for i in range(len(sorted_cost_df))]

    fig_cost.add_trace(go.Bar(
        x=sorted_cost_df['Carrier'],
        y=sorted_cost_df['avg_delay_cost'],
        marker=dict(
            color=colors_cost,
            line=dict(width=0),
        ),
        text=[f"${x:.0f}" for x in sorted_cost_df['avg_delay_cost']],
        textposition='inside',
        textfont=dict(size=12, family='Inter, sans-serif', color='white'),
        hovertemplate='<b>%{x}</b><br>Avg Delay Cost: $%{y:.0f}<extra></extra>',
    ))

    fig_cost.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=COLORS['text_secondary'], size=11),
        xaxis=dict(
            title='Carrier',
            showgrid=False,
            automargin=True,
            fixedrange=True,
        ),
        yaxis=dict(
            title='Average Delay Cost ($)',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            automargin=True,
            fixedrange=True,
        ),
        margin=dict(l=50, r=50, t=30, b=60),
        autosize=True,
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Inter, sans-serif"
        )
    )

    return fig_efficiency, fig_scatter, fig_cost


@callback(
    Output('airport-performance-chart', 'figure'),
    Input('selected-carriers-store', 'children')
)
def update_airport_chart(selected_carriers_json):
    """Update airport chart with premium styling"""

    sorted_airports = airport_df.sort_values('avg_delay_cost', ascending=False).head(10)

    fig = go.Figure()

    # Gradient colors from red to orange
    colors_gradient = [f'rgb({255}, {int(107 + (i * 14))}, {int(107 + (i * 14))})'
                       for i in range(len(sorted_airports))]

    fig.add_trace(go.Bar(
        y=sorted_airports['Airport'],
        x=sorted_airports['avg_delay_cost'],
        orientation='h',
        marker=dict(
            color=colors_gradient,
            line=dict(width=0),
        ),
        text=[f"${x:.0f}" for x in sorted_airports['avg_delay_cost']],
        textposition='inside',
        textfont=dict(size=12, family='Inter, sans-serif', color='white'),
        hovertemplate='<b>%{y}</b><br>Avg Delay Cost: $%{x:.0f}<extra></extra>',
    ))

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=COLORS['text_secondary'], size=11),
        xaxis=dict(
            title='Average Delay Cost ($)',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            automargin=True,
            fixedrange=True,
        ),
        yaxis=dict(
            title='',
            showgrid=False,
            automargin=True,
            fixedrange=True,
        ),
        margin=dict(l=50, r=50, t=30, b=60),
        autosize=True,
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Inter, sans-serif"
        )
    )

    return fig


@callback(
    Output('day-of-week-chart', 'figure'),
    Input('selected-carriers-store', 'children')
)
def update_day_of_week_chart(trigger):
    """Update day of week analysis chart"""
    if dow_stats is None:
        return go.Figure()

    fig = go.Figure()

    # Create dual-axis chart: bars for delay rate, line for avg delay
    fig.add_trace(go.Bar(
        x=dow_stats['day_name'],
        y=dow_stats['is_delayed'] * 100,
        name='Delay Rate',
        marker=dict(
            color=dow_stats['is_delayed'] * 100,
            colorscale='RdYlGn_r',
            showscale=False,
            line=dict(width=0),
        ),
        text=[f"{x:.1f}%" for x in dow_stats['is_delayed'] * 100],
        textposition='inside',
        textfont=dict(size=12, family='Inter, sans-serif', color='white'),
        hovertemplate='<b>%{x}</b><br>Delay Rate: %{y:.1f}%<extra></extra>',
        yaxis='y'
    ))

    fig.add_trace(go.Scatter(
        x=dow_stats['day_name'],
        y=dow_stats['ArrDelay'],
        name='Avg Delay (min)',
        mode='lines+markers',
        line=dict(color=COLORS['accent'], width=3),
        marker=dict(size=10, color=COLORS['accent'], line=dict(width=2, color='white')),
        hovertemplate='<b>%{x}</b><br>Avg Delay: %{y:.1f} min<extra></extra>',
        yaxis='y2'
    ))

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=COLORS['text_secondary'], size=11),
        xaxis=dict(
            title='Day of Week',
            showgrid=False,
            automargin=True,
            fixedrange=True,
        ),
        yaxis=dict(
            title='Delay Rate (%)',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            automargin=True,
            fixedrange=True,
        ),
        yaxis2=dict(
            title='Average Delay (minutes)',
            overlaying='y',
            side='right',
            showgrid=False,
            automargin=True,
            fixedrange=True,
        ),
        margin=dict(l=50, r=50, t=30, b=60),
        autosize=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Inter, sans-serif"
        )
    )

    return fig


# ============================================================================
# PREMIUM CSS STYLING
# ============================================================================

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@600;700;800&family=Roboto+Mono:wght@500;600&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #0A1F44 0%, #1e3a5f 50%, #F8FAFC 100%);
                min-height: 100vh;
                color: #1E293B;
            }

            .dashboard-container-premium {
                min-height: 100vh;
            }

            /* Header Styling */
            .header-premium {
                background: linear-gradient(135deg, #0A1F44 0%, #1e3a5f 100%);
                padding: 24px 20px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                position: relative;
                overflow: hidden;
            }

            .header-premium::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="1" fill="rgba(255,255,255,0.1)"/></svg>');
                opacity: 0.3;
            }

            .header-content-premium {
                max-width: 1400px;
                margin: 0 auto;
                position: relative;
                z-index: 1;
            }

            .header-title-premium {
                color: white;
                font-family: 'Montserrat', sans-serif;
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            }

            .header-subtitle-premium {
                color: rgba(255, 255, 255, 0.9);
                font-size: 15px;
                font-weight: 400;
                letter-spacing: 0.5px;
                text-align: center;
            }

            /* Main Container */
            .main-container-premium {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }

            /* KPI Cards */
            .kpi-row-premium {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 16px;
                margin-bottom: 20px;
            }

            .kpi-card-premium {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            }

            .kpi-card-premium:hover {
                transform: translateY(-8px);
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
            }

            .kpi-card-premium::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #00D9FF 0%, #10B981 100%);
                opacity: 0;
                transition: opacity 0.3s;
            }

            .kpi-card-premium:hover::before {
                opacity: 1;
            }

            .kpi-icon {
                font-size: 32px;
                margin-bottom: 12px;
                display: inline-block;
            }

            .kpi-title {
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1.2px;
                color: #64748B;
                margin-bottom: 12px;
            }

            .kpi-value {
                font-family: 'Roboto Mono', monospace;
                font-size: 36px;
                font-weight: 600;
                color: #0A1F44;
                margin-bottom: 6px;
                line-height: 1;
            }

            .kpi-subtitle {
                font-size: 14px;
                color: #64748B;
                font-weight: 500;
            }

            /* Filter Section */
            .filter-section-premium {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 16px 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }

            .filter-label-premium {
                font-weight: 600;
                font-size: 14px;
                color: #1E293B;
                margin-bottom: 12px;
                display: block;
            }

            .dropdown-premium .Select-control {
                border-radius: 10px !important;
                border-color: #E2E8F0 !important;
            }

            /* Airline Key Section */
            .airline-key-section-premium {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }

            .key-title-premium {
                font-family: 'Montserrat', sans-serif;
                font-size: 18px;
                font-weight: 700;
                color: #0A1F44;
                margin-bottom: 16px;
            }

            .airline-key-grid-premium {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 12px;
            }

            .airline-key-item-premium {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 16px;
                background: #F8FAFC;
                border-radius: 8px;
                border: 2px solid transparent;
                transition: all 0.2s ease;
            }

            .airline-key-clickable {
                cursor: pointer;
                user-select: none;
            }

            .airline-key-clickable:hover {
                background: #E2E8F0;
                transform: translateY(-2px);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }

            .airline-key-item-premium.active {
                background: #D1FAE5 !important;
                border-color: #10B981 !important;
            }

            .airline-key-item-premium.active .airline-code-premium {
                background: #10B981 !important;
                color: white !important;
            }

            .airline-code-premium {
                font-family: 'Roboto Mono', monospace;
                font-size: 14px;
                font-weight: 600;
                color: #0A1F44;
                background: white;
                padding: 6px 10px;
                border-radius: 4px;
                min-width: 40px;
                text-align: center;
                transition: all 0.2s ease;
            }

            .airline-name-premium {
                font-size: 14px;
                color: #64748B;
                flex: 1;
                font-weight: 500;
            }

            .airline-flights-premium {
                font-size: 12px;
                color: #94A3B8;
                font-weight: 400;
            }

            /* AI Insights Card */
            .ai-insights-card-premium {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 16px;
                padding: 32px;
                margin-bottom: 24px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            }

            .ai-insights-card-premium::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #00D9FF 0%, #10B981 50%, #00D9FF 100%);
                background-size: 200% 100%;
                animation: shimmer 3s linear infinite;
            }

            @keyframes shimmer {
                0% { background-position: 200% 0; }
                100% { background-position: -200% 0; }
            }

            .ai-insights-card-premium:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 32px rgba(0, 217, 255, 0.15);
            }

            .ai-insights-text {
                font-size: 15px;
                line-height: 1.9;
                color: #1E293B;
                margin-top: 12px;
                word-wrap: break-word;
                overflow-wrap: break-word;
                white-space: pre-wrap;
            }

            .ai-insights-text p {
                margin: 16px 0;
            }

            .ai-insights-text ol, .ai-insights-text ul {
                margin: 12px 0;
                padding-left: 24px;
            }

            .ai-insights-text li {
                margin: 12px 0;
                padding-left: 8px;
            }

            .ai-insights-text strong {
                color: #00D9FF;
                font-weight: 700;
            }

            .insights-markdown {
                padding: 16px 0;
                word-wrap: break-word;
                overflow-wrap: break-word;
                white-space: normal;
                max-width: 100%;
            }

            .insights-markdown p {
                margin: 14px 0;
                line-height: 1.8;
                white-space: normal;
                word-wrap: break-word;
            }

            .insights-markdown ol, .insights-markdown ul {
                margin: 12px 0;
                padding-left: 28px;
            }

            .insights-markdown li {
                margin: 14px 0;
                padding-left: 8px;
                line-height: 1.8;
                white-space: normal;
                word-wrap: break-word;
            }

            .insights-markdown strong {
                color: #00D9FF;
                font-weight: 700;
            }

            .insights-markdown code {
                background: rgba(0, 217, 255, 0.1);
                padding: 3px 8px;
                border-radius: 6px;
                font-family: 'Roboto Mono', monospace;
                font-size: 13px;
                color: #0A1F44;
                border: 1px solid rgba(0, 217, 255, 0.2);
            }

            /* Chatbot Card */
            .chat-card-premium {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 16px;
                padding: 32px;
                margin-bottom: 24px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            }

            .chat-card-premium::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #9333EA 0%, #3B82F6 50%, #9333EA 100%);
                background-size: 200% 100%;
                animation: shimmer 3s linear infinite;
            }

            .chat-card-premium:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 32px rgba(147, 51, 234, 0.15);
            }

            .chat-input-premium {
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                padding: 16px;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                resize: vertical;
                transition: all 0.3s;
                background: white;
            }

            .chat-input-premium:focus {
                outline: none;
                border-color: #9333EA;
                box-shadow: 0 0 0 4px rgba(147, 51, 234, 0.1);
                background: #FEFEFF;
            }

            .chat-submit-btn-premium {
                background: linear-gradient(135deg, #9333EA 0%, #3B82F6 100%);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 14px 36px;
                font-family: 'Inter', sans-serif;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                box-shadow: 0 6px 20px rgba(147, 51, 234, 0.3);
            }

            .chat-submit-btn-premium:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 28px rgba(147, 51, 234, 0.4);
            }

            .chat-submit-btn-premium:active {
                transform: translateY(0);
            }

            .chat-response-premium {
                margin-top: 24px;
                padding: 20px;
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(249, 250, 251, 0.9) 100%);
                border-radius: 12px;
                border-left: 4px solid #9333EA;
                min-height: 80px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
                word-wrap: break-word;
                overflow-wrap: break-word;
            }

            .chat-response-premium .markdown {
                font-size: 15px;
                line-height: 1.8;
                color: #1E293B;
            }

            .chat-response-premium p {
                margin: 12px 0;
                white-space: pre-wrap;
            }

            .chat-response-premium strong {
                color: #9333EA;
                font-weight: 700;
            }

            /* Large Chart Cards (Full Width) */
            .chart-card-premium-large {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                min-height: 600px;
                height: 700px;
                display: flex;
                flex-direction: column;
                margin-bottom: 20px;
            }

            .chart-card-premium-large:hover {
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
            }

            /* Fix chart container to prevent overflow */
            .chart-card-premium-large .js-plotly-plot {
                width: 100% !important;
                flex: 1;
                min-height: 500px;
            }

            .chart-card-premium-large .plotly {
                width: 100% !important;
                height: 100% !important;
            }

            .chart-card-premium-large .svg-container {
                width: 100% !important;
                height: 100% !important;
            }

            .chart-header-premium {
                margin-bottom: 12px;
                flex-shrink: 0;
            }

            .chart-title-premium {
                font-family: 'Montserrat', sans-serif;
                font-size: 16px;
                font-weight: 700;
                color: #0A1F44;
                margin-bottom: 4px;
            }

            .chart-subtitle-premium {
                font-size: 12px;
                color: #64748B;
                font-weight: 500;
            }

            /* Footer */
            .footer-premium {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 16px;
                margin-top: 16px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }

            .footer-text-premium {
                text-align: center;
                color: #64748B;
                font-size: 14px;
                line-height: 1.6;
            }

            /* Responsive Design */
            @media (max-width: 1200px) {
                .chart-row-premium {
                    grid-template-columns: 1fr;
                }
            }

            @media (max-width: 768px) {
                .header-title-premium {
                    font-size: 32px;
                }

                .kpi-row-premium {
                    grid-template-columns: 1fr;
                }

                .kpi-value {
                    font-size: 36px;
                }
            }

            /* Loading Animation - fade only, no transform to prevent layout shift */
            @keyframes fadeIn {
                from {
                    opacity: 0;
                }
                to {
                    opacity: 1;
                }
            }

            .kpi-card-premium,
            .chart-card-premium,
            .filter-section-premium {
                animation: fadeIn 0.4s ease-out backwards;
            }

            .kpi-card-premium:nth-child(1) { animation-delay: 0.05s; }
            .kpi-card-premium:nth-child(2) { animation-delay: 0.10s; }
            .kpi-card-premium:nth-child(3) { animation-delay: 0.15s; }
            .kpi-card-premium:nth-child(4) { animation-delay: 0.20s; }
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
    print("Starting Delaynomics Premium Dashboard")
    print("="*60)
    print(f"\nLoaded {len(airline_df)} airlines")
    print(f"Loaded {len(airport_df)} airports")
    if flights_df is not None:
        print(f"Loaded {len(flights_df):,} flights")
    print(f"\nPremium Dashboard: http://localhost:8050")
    print("Press CTRL+C to quit\n")

    app.run(
        debug=True,
        host='0.0.0.0',
        port=8050
    )
