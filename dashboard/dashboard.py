import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.graph_objs import Figure as PlotlyFigure
from datetime import datetime, timedelta
import math
from typing import Optional, List, Tuple, Dict, Any
import io
from botocore.exceptions import ClientError
from dashboard.models import (
    OuraData, CronometerData, StravaData, GarminData, ManualData,
    MetricCategory
)
from dashboard.files import get_s3_client, decrypt_data, encrypt_data
from dashboard.secret import get_shared_secrets
import json

# Constants and Configuration
ALL_MODELS = [OuraData, GarminData, ManualData, CronometerData, StravaData]

# Define custom source order for display
SOURCE_ORDER = ["Oura", "Garmin", "Manual", "Cronometer", "Strava"]

CATEGORY_COLORS = {
    MetricCategory.RECOVERY: '#3498db',  # Blue
    MetricCategory.ACTIVITY: '#e74c3c',  # Red
    MetricCategory.NUTRITION: '#2ecc71',  # Green
}

TIME_RANGES = {
    "Past Month": 30,
    "Past 6 Months": 180,
    "Past Year": 365,
    "All Time": None
}

# Cache settings
CACHE_TTL = timedelta(minutes=30)  # Cache data for 30 minutes

# Custom CSS and JavaScript
CUSTOM_CSS = """
<style>
/* Streamlit theme customization */
:root {
    --primary-color: #9b59b6;  /* Purple */
    --primary-color-hover: #8e44ad;  /* Darker purple for hover */
    --secondary-background-color: #f8f9fa;
    --text-color: #2c3e50;
}

/* Override Streamlit's default primary color */
.stButton button {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
}
.stButton button:hover {
    background-color: var(--primary-color-hover) !important;
    border-color: var(--primary-color-hover) !important;
}

/* Style other Streamlit elements that use primary color */
.stRadio > div > div > label {
    color: var(--primary-color) !important;
}
.stRadio > div > div[data-baseweb="radio"] > div {
    border-color: var(--primary-color) !important;
}
.stRadio > div > div[data-baseweb="radio"] > div[aria-checked="true"] {
    background-color: var(--primary-color) !important;
}
.stToggle > div > div {
    background-color: var(--primary-color) !important;
}

/* Reduce overall padding */
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}
.stContainer {
    background-color: transparent;
    padding: 0.2rem;
    margin-bottom: 0.2rem;
}
.stMarkdown h1 {
    color: #2c3e50;
    font-size: 2rem;
    margin-bottom: 0.75rem;
}
.stMarkdown h2 {
    color: #34495e;
    font-size: 1.1rem;
    margin-bottom: 0.25rem;
}
div[data-testid="stPlotlyChart"] {
    background-color: white;
    border-radius: 8px;
    padding: 0.25rem;
}
/* Radio button styling */
.stRadio > div {
    padding: 0.1rem 0;
    margin-top: -0.4rem;
}
.stRadio > div > div {
    padding: 0.05rem 0;
}
.stRadio > div > div > label {
    font-size: 0.85rem;
    padding: 0.05rem 0.5rem;
}
/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #f8f9fa;
    min-width: 14rem;
    max-width: 14rem;
}
[data-testid="stSidebar"] .stContainer {
    padding: 0.2rem;
    margin-bottom: 0.2rem;
}
[data-testid="stSidebar"] .stMarkdown h2 {
    font-size: 1.2rem;
    margin-bottom: 0;
    color: #34495e;
    font-weight: 500;
}
</style>
"""

CUSTOM_JS = """
<script>
// Function to check if device is mobile
function isMobile() {
    return window.innerWidth <= 768;
}

// Function to set sidebar state
function setSidebarState() {
    const sidebar = document.querySelector('[data-testid="stSidebar"]');
    if (sidebar) {
        if (isMobile()) {
            sidebar.classList.add('collapsed');
            sidebar.setAttribute('aria-expanded', 'false');
        } else {
            sidebar.classList.remove('collapsed');
            sidebar.setAttribute('aria-expanded', 'true');
        }
    }
}

// Set initial state
window.addEventListener('load', setSidebarState);

// Update on resize
window.addEventListener('resize', setSidebarState);
</script>
"""

# Helper Functions
def initialize_session_state():
    """Initialize all session state variables."""
    defaults = {
        'selected_type': "All",
        'selected_source': "All",
        'time_range': "Past Month",
        'last_download_check': None,
        'show_daily_traces': False,
        'use_single_column': False,
        'refresh_flag': False,
        'refresh_toggle': False,
        'compare_metric_1': None,  # Will be set to first metric when available
        'compare_metric_2': None,  # Will be set to second metric when available
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

@st.cache_data(ttl=CACHE_TTL)
def download_data() -> Optional[pd.DataFrame]:
    """
    Get data directly from AWS S3 with caching.
    Returns None if data is not available.
    """
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Downloading health data from AWS S3...")
        with st.spinner("Downloading data..."):
            s3_client = get_s3_client()
            secrets = get_shared_secrets()
            bucket = secrets.AWS_S3_BUCKET_NAME
            csv_filename = secrets.AWS_CSV_FILENAME
            
            # Get data file
            try:
                response = s3_client.get_object(
                    Bucket=bucket,
                    Key=csv_filename
                )
                encrypted_data = response['Body'].read()
                decrypted_data = decrypt_data(encrypted_data)
                
                # Read CSV directly into DataFrame
                df = pd.read_csv(io.BytesIO(decrypted_data))
                df['date'] = pd.to_datetime(df['date'])
                return df
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    st.error(f"No data found in AWS (looking for {csv_filename})")
                    return None
                raise
        
    except Exception as e:
        st.error(f"Error getting data from AWS: {e}")
        return None


def get_column_metadata(column: str) -> Tuple[str, str, Optional[MetricCategory], Optional[str], bool]:
    """Get source, pretty name, category, unit, and sum_weekly flag for a column."""
    parts = column.split('__', 1)
    if len(parts) == 2:
        source, base_column = parts
        for model in ALL_MODELS:
            if model.__name__.lower().startswith(source.lower()):
                metadata = model.get_field_metadata(base_column)
                if metadata:
                    return source, metadata.pretty_name, metadata.category, metadata.unit, metadata.sum_weekly
    
    return column, column.replace('_', ' ').title(), None, None, False

def format_date(date: datetime) -> str:
    """Format a date into a nice readable format like '6th May 2025'."""
    day = date.day
    suffix = "th" if 4 <= day <= 20 or 24 <= day <= 30 else ["st", "nd", "rd"][day % 10 - 1]
    return date.strftime(f"%-d{suffix} %B %Y")

def get_day_name(date: datetime) -> str:
    """Get the full day name from a date."""
    return date.strftime("%A")

def update_plot_layout(fig, y_axis_label: str, y_min: Optional[float] = None, y_max: Optional[float] = None):
    """Update plot layout with consistent styling and smaller margins."""
    fig.update_layout(
        xaxis_title="",
        yaxis_title=y_axis_label,
        margin=dict(l=10, r=10, t=5, b=10),
        height=250,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            title_standoff=15,
            title_font=dict(size=12, color='#7f8c8d'),
            gridcolor='#ecf0f1',
            zerolinecolor='#ecf0f1',
            tickfont=dict(size=10, color='#7f8c8d'),
            range=[y_min, y_max] if y_min is not None and y_max is not None else None
        ),
        xaxis=dict(
            gridcolor='#ecf0f1',
            zerolinecolor='#ecf0f1',
            tickfont=dict(size=10, color='#7f8c8d')
        ),
        hovermode='x unified'
    )

# Callback functions for radio buttons
def on_type_change():
    st.session_state.selected_type = st.session_state.type_radio
    st.session_state.compare_metric_1 = None
    st.session_state.compare_metric_2 = None

def on_source_change():
    st.session_state.selected_source = st.session_state.source_radio
    # Reset comparison metrics when source changes
    st.session_state.compare_metric_1 = None
    st.session_state.compare_metric_2 = None

def on_time_range_change():
    st.session_state.time_range = st.session_state.time_radio

def on_refresh():
    st.cache_data.clear()
    st.session_state.refresh_flag = True

def on_refresh_toggle():
    """Callback for refresh toggle."""
    if st.session_state.refresh_toggle:
        on_refresh()
        st.session_state.refresh_toggle = False

def setup_page():
    """Set up the Streamlit page configuration and custom styling."""
    st.set_page_config(
        page_title="Health Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    # Apply CSS and JavaScript using components.html to ensure proper rendering
    components.html(f"{CUSTOM_CSS}{CUSTOM_JS}", height=0)

def create_sidebar_filters(df: pd.DataFrame):
    """Create and handle sidebar filters."""
    with st.sidebar:
        # Type filter
        st.markdown("<h2 style='color: #2c3e50; margin-bottom: 0.5rem;'>Type</h2>", unsafe_allow_html=True)
        type_options = ["All"] + [cat.value.title() for cat in MetricCategory]
        selected_type = st.radio(
            "Type",
            type_options,
            index=type_options.index(st.session_state.selected_type),
            label_visibility="collapsed",
            key="type_radio",
            on_change=on_type_change
        )
        selected_types = [cat for cat in MetricCategory if cat.value.title() == selected_type] if selected_type != "All" else list(MetricCategory)
        
        # Source filter
        st.markdown("<h2 style='color: #2c3e50; margin-bottom: 0.5rem;'>Source</h2>", unsafe_allow_html=True)
        available_sources = set(col.split('__')[0].title() for col in df.columns if '__' in col)
        # Use custom order for sources, filtering out any that aren't available
        ordered_sources = [source for source in SOURCE_ORDER if source in available_sources]
        source_options = ["All"] + ordered_sources
        selected_source = st.radio(
            "Source",
            source_options,
            index=source_options.index(st.session_state.selected_source),
            label_visibility="collapsed",
            key="source_radio",
            on_change=on_source_change
        )
        selected_sources = [selected_source.lower()] if selected_source != "All" else [source.lower() for source in ordered_sources]
        
        # Time range filter
        st.markdown("<h2 style='color: #2c3e50; margin-bottom: 0.5rem;'>Time Range</h2>", unsafe_allow_html=True)
        time_ranges = list(TIME_RANGES.keys())
        selected_time_range = st.radio(
            "Time Range",
            time_ranges,
            index=time_ranges.index(st.session_state.time_range),
            label_visibility="collapsed",
            key="time_radio",
            on_change=on_time_range_change
        )

        # Display options
        st.markdown("<h2 style='color: #2c3e50; margin-bottom: 0.5rem;'>Display Options</h2>", unsafe_allow_html=True)
        st.toggle(
            "Show Daily Traces",
            value=st.session_state.show_daily_traces,
            key="show_daily_traces"
        )
        st.toggle(
            "Single Column Layout",
            value=st.session_state.use_single_column,
            key="use_single_column"
        )


        # Create refresh toggle with callback
        st.toggle(
            "Refresh Data",
            value=st.session_state.refresh_toggle,
            key="refresh_toggle",
            on_change=on_refresh_toggle
        )

    return selected_types, selected_sources, selected_time_range

def filter_data_by_date_range(df: pd.DataFrame, time_range: str) -> pd.DataFrame:
    """Filter data based on the selected time range."""
    end_date = df['date'].max()
    if time_range == "All Time":
        return df.copy()
    
    days = TIME_RANGES[time_range]
    start_date = end_date - timedelta(days=days)
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    return df.loc[mask].copy()

def filter_columns_by_type_and_source(df: pd.DataFrame, selected_types: List[MetricCategory], selected_sources: List[str]) -> List[str]:
    """Filter columns based on type and source selections."""
    columns_to_keep = ['date']
    
    for col in df.columns:
        if col == 'date':
            continue
            
        base_column = col.split('__', 1)[1] if '__' in col else col
        metadata = None
        for model in ALL_MODELS:
            metadata = model.get_field_metadata(base_column)
            if metadata:
                break
        
        type_match = not selected_types or (metadata and metadata.category in selected_types)
        source_match = not selected_sources or any(col.startswith(source) for source in selected_sources)
        
        if type_match and source_match:
            columns_to_keep.append(col)
    
    return columns_to_keep


def create_plot(plot_df: pd.DataFrame, column: str, source: str, pretty_name: str, 
                category: Optional[MetricCategory], unit: Optional[str], sum_weekly: bool):
    """Create a single plot for a metric."""
    category_color = get_category_color(category)
    y_axis_label = unit if unit else ""
    
    # Get display delay metadata for this column
    base_column = column.split('__', 1)[1] if '__' in column else column
    display_delay = 1  # Default to 1 if not found
    for model in ALL_MODELS:
        metadata = model.get_field_metadata(base_column)
        if metadata:
            display_delay = metadata.display_delay
            break
    
    # Filter out today's data if display_delay=1
    if display_delay == 1:
        today = pd.Timestamp.now().normalize()
        plot_df = plot_df[plot_df['date'].dt.date < today.date()]
    
    # Find the last non-None entry for this metric
    last_valid_date = plot_df[plot_df[column].notna()]['date'].max()
    if pd.isna(last_valid_date):
        return  # Skip plotting if no valid data
    
    # Filter data up to the last valid entry
    plot_df = plot_df[plot_df['date'] <= last_valid_date].copy()
    
    with st.container(border=True):
        st.markdown(
            f"<h2 style='color: #2c3e50; font-size: 1.1rem; margin-bottom: 0.5rem;'>{pretty_name} "
            f"<span style='color: #7f8c8d; font-size: 0.9rem;'>({source.title()})</span></h2>",
            unsafe_allow_html=True
        )
        
        if sum_weekly:
            fig = create_weekly_line_plot(plot_df, column, category_color)
        else:
            fig = create_daily_line_plot(plot_df, column, category_color)
        
        update_plot_layout(fig, y_axis_label)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def create_weekly_line_plot(df: pd.DataFrame, column: str, color: str) -> Any:
    """Create a weekly line plot for summed metrics."""
    # Create a proper copy of the entire DataFrame first
    plot_df = df.copy()
    # Then select columns using .loc
    plot_df = plot_df.loc[:, ['date', column]].copy()
    
    # Convert boolean values to float if needed
    if plot_df[column].dtype == bool:
        plot_df[column] = plot_df[column].astype(float)
    
    plot_df.set_index('date', inplace=True)
    plot_df = plot_df.resample('W-MON', closed='left').sum().reset_index()
    # Shift dates backward by one week to show the Monday that starts the week
    plot_df.loc[:, 'date'] = plot_df['date'] - pd.Timedelta(days=7)
    # Then sort for display
    plot_df = plot_df.sort_values('date')
    
    # Calculate rolling average (using 4 weeks as the window for weekly data)
    rolling_col = f'{column}_rolling'
    plot_df[rolling_col] = plot_df[column].rolling(window=4, min_periods=1, center=False).mean()
    
    # Ensure both columns are float
    plot_df[column] = plot_df[column].astype(float)
    plot_df[rolling_col] = plot_df[rolling_col].astype(float)
    
    # Add hover text showing both weekly total and rolling average
    plot_df.loc[:, 'hover_text'] = plot_df.apply(
        lambda row: f"Weekly Total: {row[column]:.1f}<br>" +
                   f"4-week Avg: {row[rolling_col]:.1f}" if st.session_state.show_daily_traces else f"4-week Avg: {row[rolling_col]:.1f}",
        axis=1
    )
    
    # Calculate y-axis range
    rolling_min = plot_df[rolling_col].min()
    rolling_max = plot_df[rolling_col].max()
    rolling_range = rolling_max - rolling_min
    y_min = rolling_min - (rolling_range * 0.1)
    y_max = rolling_max + (rolling_range * 0.1)
    
    try:
        # Create a long-form dataframe for plotting
        plot_data = pd.melt(
            plot_df,
            id_vars=['date', 'hover_text'],
            value_vars=[column, rolling_col] if st.session_state.show_daily_traces else [rolling_col],
            var_name='variable',
            value_name='value'
        )
        
        # Force using regular Scatter instead of Scattergl for better compatibility
        fig = px.line(
            plot_data,
        x='date',
            y='value',
            color='variable',
        title=None,
            labels={'date': 'Date', 'value': '', 'variable': ''},
            hover_data={'hover_text': True},
            range_y=[y_min, y_max],
            render_mode='svg'  # This forces using regular Scatter instead of Scattergl
        )
        
        # Update traces with smoothing for all trace types
        fig.update_traces(
            line_shape='spline',
            mode='lines',
            selector=dict(name=rolling_col)
        )
        
        # Add smoothing only for non-Scattergl traces
        for trace in fig.data:
            if trace.name == rolling_col and not isinstance(trace, go.Scattergl):
                trace.line.smoothing = 1.3
        
        fig.update_traces(
            line=dict(color=color, width=2.5),
            hovertemplate='%{customdata[0]}<extra></extra>',
            selector=dict(name=rolling_col)
        )
        
        # Add weekly data points with thinner lines if daily traces are enabled
        if st.session_state.show_daily_traces:
            fig.update_traces(
                        line=dict(color=color, width=1),
                        opacity=0.3,
                        hoverinfo='none',
                        hovertemplate=None,
                        selector=dict(name=column)
            )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating plot: {e}")
        raise

def create_daily_line_plot(df: pd.DataFrame, column: str, color: str) -> Any:
    """Create a daily line plot with rolling average."""
    df = df.copy()
    
    # Determine smoothing window based on time range
    smoothing_window = 30 if st.session_state.time_range in ["Past 6 Months", "Past Year", "All Time"] else 7
    
    df.loc[:, f'{column}_rolling'] = df[column].rolling(window=smoothing_window, min_periods=1, center=False).mean()
    
    df.loc[:, 'hover_text'] = df.apply(
        lambda row: f"Actual: {row[column]:.1f}<br>" +
                   f"{smoothing_window}-day Avg: {row[f'{column}_rolling']:.1f}" if st.session_state.show_daily_traces else f"{smoothing_window}-day Avg: {row[f'{column}_rolling']:.1f}",
        axis=1
    )
    
    rolling_min = df[f'{column}_rolling'].min()
    rolling_max = df[f'{column}_rolling'].max()
    rolling_range = rolling_max - rolling_min
    y_min = rolling_min - (rolling_range * 0.1)
    y_max = rolling_max + (rolling_range * 0.1)
    
    y_columns = [f'{column}_rolling']
    if st.session_state.show_daily_traces:
        y_columns.insert(0, column)
    
    try:
        # Force using regular Scatter instead of Scattergl for better compatibility
        fig = px.line(
            df,
            x='date',
            y=y_columns,
            title=None,
            labels={'date': 'Date', 'value': '', 'variable': ''},
            hover_data={'hover_text': True},
            range_y=[y_min, y_max],
            render_mode='svg'  # This forces using regular Scatter instead of Scattergl
        )
        
        # Update traces with smoothing for all trace types
        fig.update_traces(
            line_shape='spline',
            mode='lines',
            selector=dict(name=f'{column}_rolling')
        )
        
        # Add smoothing only for non-Scattergl traces
        for trace in fig.data:
            if trace.name == f'{column}_rolling' and not isinstance(trace, go.Scattergl):
                trace.line.smoothing = 1.3
        
        fig.update_traces(
            line=dict(color=color, width=2.5),
            hovertemplate='%{customdata[0]}<extra></extra>',
            selector=dict(name=f'{column}_rolling')
        )
        
        if st.session_state.show_daily_traces:
            fig.update_traces(
                line=dict(color=color, width=1, smoothing=1.3, shape='spline'),
                opacity=0.3,
                hoverinfo='none',
                hovertemplate=None,
                line_shape='spline',
                selector=dict(name=column)
            )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating plot: {e}")
        raise

def prepare_display_table(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare the data table for display with formatted columns."""
    # Create a proper copy of the entire DataFrame
    display_df = df.copy()
    # Sort the copy
    display_df = display_df.sort_values('date', ascending=False).copy()
    
    # Ensure 'date' is datetime before formatting
    display_df['date'] = pd.to_datetime(display_df['date'])
    display_df['day'] = display_df['date'].apply(get_day_name)
    display_df['date'] = display_df['date'].apply(format_date)
    
    # Create new DataFrame with reordered columns
    cols = ['day', 'date'] + [col for col in display_df.columns if col not in ['day', 'date']]
    display_df = display_df.loc[:, cols].copy()
    
    # Round numeric columns
    numeric_cols = [col for col in display_df.columns if display_df[col].dtype in ['float64', 'int64']]
    display_df[numeric_cols] = display_df[numeric_cols].round(2)
    
    column_names = {}
    for col in display_df.columns:
        if col == 'day':
            column_names[col] = 'Day'
        elif col == 'date':
            column_names[col] = 'Date'
        else:
            source, pretty_name, _, unit, _ = get_column_metadata(col)
            column_names[col] = f"{source.title()} - {pretty_name} ({unit})" if unit else f"{source.title()} - {pretty_name}"
    
    return display_df.rename(columns=column_names)

def create_manual_data_entry(df: pd.DataFrame):
    """Create a form for manual data entry."""
    # Get the date range for the date picker
    min_date = df['date'].min()
    # Allow dates up to 1 year in the future
    max_date = max(df['date'].max(), datetime.now() + timedelta(days=365))
    
    # Initialize form state if not exists
    if 'manual_form_state' not in st.session_state:
        st.session_state.manual_form_state = {
            'date': datetime.now().date(),
            'bodyweight': None,
            'lift': None
        }
    
    # Create a form for data entry
    with st.form("manual_data_entry"):
        # Create title and button in the same row
        title_col, button_col = st.columns([3, 1])
        with title_col:
            pass
        with button_col:
            submitted = st.form_submit_button("Save Data", use_container_width=True)
        
        # Create three columns for the form inputs
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Date selection
            selected_date = st.date_input(
                "Date",
                value=st.session_state.manual_form_state['date'],
                min_value=min_date.date(),
                max_value=max_date.date(),
                key="manual_date"
            )
        
        with col2:
            # Bodyweight input
            bodyweight = st.number_input(
                "Bodyweight (kg)",
                min_value=0.0,
                max_value=500.0,
                value=st.session_state.manual_form_state['bodyweight'],
                step=0.1,
                format="%.1f",
                key="manual_bodyweight"
            )
        
        with col3:
            # Lift dropdown with True/False
            lift = st.selectbox(
                "Lift",
                options=[None, True, False],
                index=0 if st.session_state.manual_form_state['lift'] is None else 
                      (1 if st.session_state.manual_form_state['lift'] else 2),
                format_func=lambda x: "Select..." if x is None else str(x),
                key="manual_lift"
            )
        
        if submitted:
            # Check if we're using random data
            secrets = get_shared_secrets()
            if 'random' in secrets.AWS_CSV_FILENAME.lower():
                st.warning("Manual data entry is disabled for this deployment.")
                return
            
            # Create a new ManualData entry
            manual_data = ManualData(
                source="manual",
                date=datetime.combine(selected_date, datetime.min.time()),
                bodyweight_kg=bodyweight if bodyweight is not None else None,
                lift=lift
            )
            
            # Convert to DataFrame row
            new_data = {
                'date': manual_data.date,
                'manual__bodyweight_kg': manual_data.bodyweight_kg,
                'manual__lift': manual_data.lift
            }
            
            # Create temp data with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_data = {
                'timestamp': timestamp,
                'data': new_data
            }
            
            try:
                s3_client = get_s3_client()
                secrets = get_shared_secrets()
                bucket = secrets.AWS_S3_BUCKET_NAME
                
                # Save temp file first
                temp_key = f'temp_{timestamp}.json'
                temp_json = json.dumps(temp_data, default=str)
                encrypted_temp = encrypt_data(temp_json.encode('utf-8'))
                s3_client.put_object(
                    Bucket=bucket,
                    Key=temp_key,
                    Body=encrypted_temp
                )
                
                # Then update main data file
                # Check if a row for this date already exists
                date_mask = df['date'].dt.date == selected_date
                if date_mask.any():
                    # Update existing row
                    for col, value in new_data.items():
                        if value is not None:  # Only update non-None values
                            df.loc[date_mask, col] = value
                else:
                    # Create new row
                    new_row = pd.DataFrame([new_data])
                    df = pd.concat([df, new_row], ignore_index=True)
                
                # Convert to CSV and encrypt
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                encrypted_data = encrypt_data(csv_buffer.getvalue().encode('utf-8'))
                
                # Upload to S3
                s3_client.put_object(
                    Bucket=bucket,
                    Key=secrets.AWS_CSV_FILENAME,
                    Body=encrypted_data
                )
                
                st.success(f"Data saved successfully!")
                
                # Reset form state with today's date
                st.session_state.manual_form_state = {
                    'date': datetime.now().date(),
                    'bodyweight': None,
                    'lift': None
                }
                
                # Clear all caches and trigger refresh
                st.cache_data.clear()
                st.session_state.refresh_flag = True
                st.rerun()
                
            except Exception as e:
                st.error(f"Error saving data: {e}")

def get_category_color(category: Optional[MetricCategory], is_dual_axis: bool = False, is_second_metric: bool = False) -> str:
    """Get the color for a metric category, with a default if category is None.
    For dual-axis plots, uses fixed blue/red colors regardless of category."""
    if is_dual_axis:
        return '#e74c3c' if is_second_metric else '#3498db'  # Red for second metric, blue for first
    if category is None:
        return '#3498db'  # Default blue
    return CATEGORY_COLORS.get(category, '#3498db')

def get_smoothing_window(start_date: pd.Timestamp, end_date: pd.Timestamp) -> int:
    """Determine the smoothing window based on the time range."""
    date_range = end_date - start_date
    if date_range.days > 180:  # More than 6 months
        return 30
    elif date_range.days > 90:  # More than 3 months
        return 14
    else:
        return 7

def create_dual_axis_plot(df: pd.DataFrame, metric1: str, metric2: str) -> PlotlyFigure:
    """Create a dual-axis plot comparing two metrics."""
    # Get metadata for both metrics
    source1, pretty_name1, category1, unit1, sum_weekly1 = get_column_metadata(metric1)
    source2, pretty_name2, category2, unit2, sum_weekly2 = get_column_metadata(metric2)
    
    # Create a copy of the dataframe for plotting
    plot_df = df.copy()
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Fixed colors for dual-axis plot
    LEFT_COLOR = '#3498db'  # Blue
    RIGHT_COLOR = '#e74c3c'  # Red
    
    # Helper function to process a metric and add its traces
    def add_metric_traces(metric: str, pretty_name: str, sum_weekly: bool, 
                         is_secondary: bool = False) -> None:
        # Get the appropriate color based on which axis
        color = RIGHT_COLOR if is_secondary else LEFT_COLOR
        
        # Convert boolean values to float if needed
        if plot_df[metric].dtype == bool:
            plot_df[metric] = plot_df[metric].astype(float)
        
        # If metric is weekly summed, create weekly data
        if sum_weekly:
            # Create weekly summed data
            weekly_df = plot_df.copy()
            weekly_df.set_index('date', inplace=True)
            weekly_df = weekly_df.resample('W-MON', closed='left').sum().reset_index()
            # Shift dates backward by one week to show the Monday that starts the week
            weekly_df.loc[:, 'date'] = weekly_df['date'] - pd.Timedelta(days=7)
            weekly_df = weekly_df.sort_values('date')
            
            # Calculate 4-week rolling average
            rolling_col = f'{metric}_rolling'
            weekly_df[rolling_col] = weekly_df[metric].rolling(window=4, min_periods=1, center=False).mean()
            
            # Create hover text for the rolling average
            weekly_df.loc[:, 'hover_text'] = weekly_df.apply(
                lambda row: f"Weekly Total: {row[metric]:.1f}<br>4-week Avg: {row[rolling_col]:.1f}" if st.session_state.show_daily_traces else f"4-week Avg: {row[rolling_col]:.1f}",
                axis=1
            )
            
            # Add weekly sums trace if daily traces are enabled
            if st.session_state.show_daily_traces:
                fig.add_trace(
                    go.Scatter(
                        x=weekly_df['date'],
                        y=weekly_df[metric],
                        name=f"{pretty_name} (Weekly)",
                        line=dict(
                            color=color,
                            width=1
                        ),
                        opacity=0.3,
                        yaxis='y2' if is_secondary else 'y',
                        hoverinfo='none'
                    )
                )
            
            # Add rolling average trace
            fig.add_trace(
                go.Scatter(
                    x=weekly_df['date'],
                    y=weekly_df[rolling_col],
                    name=f"{pretty_name} (4-week Avg)",
                    line=dict(
                        color=color,
                        width=2.5,
                        smoothing=1.3,
                        shape='spline'
                    ),
                    yaxis='y2' if is_secondary else 'y',
                    text=weekly_df['hover_text'],
                    hovertemplate='%{text}<extra></extra>'
                )
            )
        else:
            # For non-weekly metrics, use daily data with smoothing
            smoothing_window = get_smoothing_window(plot_df['date'].min(), plot_df['date'].max())
            rolling_col = f'{metric}_rolling'
            plot_df[rolling_col] = plot_df[metric].rolling(window=smoothing_window, min_periods=1, center=False).mean()
            
            # Create hover text for the rolling average
            plot_df.loc[:, 'hover_text'] = plot_df.apply(
                lambda row: f"Daily: {row[metric]:.1f}<br>{smoothing_window}-day Avg: {row[rolling_col]:.1f}" if st.session_state.show_daily_traces else f"{smoothing_window}-day Avg: {row[rolling_col]:.1f}",
                axis=1
            )
            
            # Add daily traces if enabled
            if st.session_state.show_daily_traces:
                fig.add_trace(
                    go.Scatter(
                        x=plot_df['date'],
                        y=plot_df[metric],
                        name=f"{pretty_name} (Daily)",
                        line=dict(
                            color=color,
                            width=1,
                            smoothing=1.3,
                            shape='spline'
                        ),
                        opacity=0.3,
                        yaxis='y2' if is_secondary else 'y',
                        hoverinfo='none'
                    )
                )
            
            # Add smoothed line
            fig.add_trace(
                go.Scatter(
                    x=plot_df['date'],
                    y=plot_df[rolling_col],
                    name=f"{pretty_name} ({smoothing_window}-day Avg)",
                    line=dict(
                        color=color,
                        width=2.5,
                        smoothing=1.3,
                        shape='spline' 
                    ),
                    yaxis='y2' if is_secondary else 'y',
                    text=plot_df['hover_text'],
                    hovertemplate='%{text}<extra></extra>'
                )
            )
    
    # Add traces for both metrics
    add_metric_traces(metric1, pretty_name1, sum_weekly1)
    add_metric_traces(metric2, pretty_name2, sum_weekly2, is_secondary=True)
    
    # Update layout
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255, 255, 255, 0.8)"
        ),
        hovermode='x unified',
        margin=dict(l=0, r=0, t=30, b=0),
        height=400,
        yaxis=dict(
            title=dict(
                text=pretty_name1,
                font=dict(size=12, color=LEFT_COLOR)
            ),
            side='left',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            tickfont=dict(color=LEFT_COLOR)
        ),
        yaxis2=dict(
            title=dict(
                text=pretty_name2,
                font=dict(size=12, color=RIGHT_COLOR)
            ),
            side='right',
            showgrid=False,
            overlaying='y',
            tickfont=dict(color=RIGHT_COLOR)
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        )
    )
    
    return fig

def create_compare_mode_section(df: pd.DataFrame, available_metrics: List[str]):
    """Create the compare mode section with metric selection and dual-axis plot."""
    st.markdown("---")
    
    # Create a container for the compare mode section
    with st.container():        
        # Create two columns for metric selection
        col1, col2 = st.columns(2)
        
        # Get pretty names for the dropdown options and sort by source
        metric_options = []
        for metric in available_metrics:
            source, pretty_name, _, _, _ = get_column_metadata(metric)
            display_name = f"{pretty_name} ({source.title()})"
            # Get source index for sorting (use len(SOURCE_ORDER) for sources not in the list)
            source_index = next((i for i, s in enumerate(SOURCE_ORDER) if s.lower() == source.lower()), len(SOURCE_ORDER))
            metric_options.append((metric, display_name, source_index))
        
        # Sort options by source order, then by display name
        metric_options.sort(key=lambda x: (x[2], x[1]))
        
        # Set default selections if not already set
        if st.session_state.compare_metric_1 is None and metric_options:
            st.session_state.compare_metric_1 = metric_options[0][0]
        if st.session_state.compare_metric_2 is None and len(metric_options) > 1:
            st.session_state.compare_metric_2 = metric_options[1][0]
        
        with col1:
            metric1 = st.selectbox(
                "Select first metric",
                options=[None] + [opt[0] for opt in metric_options],
                format_func=lambda x: "Select a metric..." if x is None else 
                    next((opt[1] for opt in metric_options if opt[0] == x), x),
                index=0 if st.session_state.compare_metric_1 is None else 
                    [opt[0] for opt in metric_options].index(st.session_state.compare_metric_1) + 1,
                key="compare_metric_1_select",
                label_visibility="collapsed"
            )
            st.session_state.compare_metric_1 = metric1
        
        with col2:
            metric2 = st.selectbox(
                "Select second metric",
                options=[None] + [opt[0] for opt in metric_options],
                format_func=lambda x: "Select a metric..." if x is None else 
                    next((opt[1] for opt in metric_options if opt[0] == x), x),
                index=0 if st.session_state.compare_metric_2 is None else 
                    [opt[0] for opt in metric_options].index(st.session_state.compare_metric_2) + 1,
                key="compare_metric_2_select",
                label_visibility="collapsed"
            )
            st.session_state.compare_metric_2 = metric2
        
        # Create the dual-axis plot if both metrics are selected
        if metric1 and metric2:
            fig = create_dual_axis_plot(df, metric1, metric2)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Add a divider after the compare mode section
        st.markdown("---")

def main():
    """Main dashboard function."""
    setup_page()
    initialize_session_state()
    
    # Check if we're using random data and show disclaimer
    secrets = get_shared_secrets()
    if 'random' in secrets.AWS_CSV_FILENAME.lower():
        st.warning("⚠️ This data is entirely synthetic")
    
    # Check if a refresh was requested (and reset the flag)
    if st.session_state.refresh_flag:
        st.session_state.refresh_flag = False
        # Clear all caches to ensure fresh data
        st.cache_data.clear()
        st.rerun()
        return  # Exit after rerun to prevent duplicate rendering
    
    # Get data from AWS
    df = download_data()
    if df is None:
        st.error("Unable to load data. Please try again later.")
        st.stop()
    
    # Create sidebar filters
    selected_types, selected_sources, selected_time_range = create_sidebar_filters(df)
    
    # Filter data
    filtered_df = filter_data_by_date_range(df, selected_time_range)
    columns_to_keep = filter_columns_by_type_and_source(filtered_df, selected_types, selected_sources)
    filtered_df = filtered_df[columns_to_keep]
    
    # Get columns to plot
    columns_to_plot = [col for col in filtered_df.columns 
                      if col != 'date' and not filtered_df[col].isna().all()]
    
    if not columns_to_plot:
        st.info("No metrics available for the selected filters.")
        return
    
    # Create plots grid
    num_columns = 1 if st.session_state.use_single_column else 3
    num_rows = math.ceil(len(columns_to_plot) / num_columns)
    
    for row in range(num_rows):
        cols = st.columns(num_columns)
        for col_idx in range(num_columns):
            metric_idx = row * num_columns + col_idx
            if metric_idx < len(columns_to_plot):
                column = columns_to_plot[metric_idx]
                with cols[col_idx]:
                    source, pretty_name, category, unit, sum_weekly = get_column_metadata(column)
                    
                    if selected_time_range == "All Time":
                        metric_data = filtered_df[['date', column]].dropna(subset=[column])
                        if not metric_data.empty:
                            metric_start_date = metric_data['date'].min()
                            metric_mask = (filtered_df['date'] >= metric_start_date) & (filtered_df['date'] <= filtered_df['date'].max())
                            plot_df = filtered_df.loc[metric_mask].copy()
                        else:
                            continue
                    else:
                        plot_df = filtered_df.copy()
                    
                    create_plot(plot_df, column, source, pretty_name, category, unit, sum_weekly)
    
    # Display data table
    st.markdown("---")

    display_df = prepare_display_table(filtered_df)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Add compare mode section
    create_compare_mode_section(filtered_df, columns_to_plot)
    
    # Add manual entry form at the bottom
    create_manual_data_entry(df)

if __name__ == "__main__":
    main() 