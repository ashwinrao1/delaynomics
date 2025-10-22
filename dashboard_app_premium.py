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
    'MQ': 'Envoy Air',
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
                html.Span("$74/minute (FAA estimate)"),
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
        You are a flight delay data analyst. Answer this question based ONLY on the data provided below.

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

    # Add scatter points
    fig_scatter.add_trace(go.Scatter(
        x=filtered_df['delay_rate'],
        y=filtered_df['avg_cost_per_mile'],
        mode='markers+text',
        marker=dict(
            size=filtered_df['num_flights'] / 100,
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
