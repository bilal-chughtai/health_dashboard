import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import math
from dashboard.models import (
    OuraData, CronometerData, StravaData, GarminData, GSheetData,
    MetricCategory
)
from dashboard.files import download_and_decrypt_csv
from typing import Optional
from pathlib import Path

# Define all models in one place for consistent usage
ALL_MODELS = [OuraData, CronometerData, StravaData, GarminData, GSheetData]

# Set page config with a light theme
st.set_page_config(
    page_title="Health Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
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
""", unsafe_allow_html=True)

# Cache the last download time
@st.cache_data(ttl=timedelta(hours=4))
def get_last_download_time() -> Optional[datetime]:
    """Get the last time we downloaded data from AWS."""
    try:
        with open("data/last_aws_download.txt", "r") as f:
            return datetime.fromisoformat(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None

def save_last_download_time():
    """Save the current time as the last download time."""
    Path("data").mkdir(exist_ok=True)
    with open("data/last_aws_download.txt", "w") as f:
        f.write(datetime.now().isoformat())

def download_from_aws():
    """Download data from AWS with user feedback."""
    with st.spinner("Downloading data..."):
        try:
            if download_and_decrypt_csv():
                save_last_download_time()
            else:
                st.toast("No data found in AWS, using local data")
        except Exception as e:
            st.error(f"Error downloading from AWS: {e}")
            st.toast("Using local data due to AWS download error")

# Read data
@st.cache_data(ttl=timedelta(hours=4))
def load_data():
    """Load data from CSV."""
    # Load from local CSV
    df = pd.read_csv("data/health_data.csv")
    df['date'] = pd.to_datetime(df['date'])
    return df

# Initialize session state for filters if not already done
if 'selected_type' not in st.session_state:
    st.session_state.selected_type = "All"
if 'selected_source' not in st.session_state:
    st.session_state.selected_source = "All"
if 'time_range' not in st.session_state:
    st.session_state.time_range = "Past Month"
if 'last_download_check' not in st.session_state:
    st.session_state.last_download_check = None

# Check if we need to download fresh data (only once every 4 hours)
current_time = datetime.now()
if (st.session_state.last_download_check is None or 
    current_time - st.session_state.last_download_check > timedelta(hours=4)):
    download_from_aws()
    st.session_state.last_download_check = current_time

# Load data
df = load_data()

# Helper function to get metadata for a column
def get_column_metadata(column: str) -> tuple[str, str, MetricCategory | None, str | None, bool]:
    """Get source, pretty name, category, unit, and sum_weekly flag for a column"""
    # Split into source and base column (e.g., "oura__sleep_score" -> ("oura", "sleep_score"))
    parts = column.split('__', 1)
    if len(parts) == 2:
        source, base_column = parts
        # First try to get metadata for the full column name (including source)
        for model in ALL_MODELS:
            if model.__name__.lower().startswith(source.lower()):
                metadata = model.get_field_metadata(base_column)
                if metadata:
                    return source, metadata.pretty_name, metadata.category, metadata.unit, metadata.sum_weekly
    
    # Fallback to column name if no metadata found
    return column, column.replace('_', ' ').title(), None, None, False

# Get unique sources from column names
available_sources = sorted(set(col.split('__')[0].title() for col in df.columns if '__' in col))

# Define new callback functions for radio buttons (so that on_change is a def, not a lambda)
def on_type_change():
    st.session_state.selected_type = st.session_state.type_radio

def on_source_change():
    st.session_state.selected_source = st.session_state.source_radio

def on_time_range_change():
    st.session_state.time_range = st.session_state.time_radio

# Title and filters in sidebar
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
    source_options = ["All"] + available_sources
    selected_source = st.radio(
        "Source",
        source_options,
        index=source_options.index(st.session_state.selected_source),
        label_visibility="collapsed",
        key="source_radio",
        on_change=on_source_change
    )
    selected_sources = [selected_source.lower()] if selected_source != "All" else [source.lower() for source in available_sources]
    
    # Time range filter
    st.markdown("<h2 style='color: #2c3e50; margin-bottom: 0.5rem;'>Time Range</h2>", unsafe_allow_html=True)
    time_ranges = ["Past Month", "Past 6 Months", "Past Year", "All Time"]
    selected_time_range = st.radio(
        "Time Range",
        time_ranges,
        index=time_ranges.index(st.session_state.time_range),
        label_visibility="collapsed",
        key="time_radio",
        on_change=on_time_range_change
    )

# Calculate date range
end_date = df['date'].max()
if st.session_state.time_range == "Past Month":
    start_date = end_date - timedelta(days=30)
elif st.session_state.time_range == "Past 6 Months":
    start_date = end_date - timedelta(days=180)
elif st.session_state.time_range == "Past Year":
    start_date = end_date - timedelta(days=365)
else:  # All Time - we'll handle this per metric
    start_date = None  # Will be determined per metric

# Filter data for selected time range
if start_date is not None:
    # For fixed time ranges, filter all data at once
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    filtered_df = df.loc[mask].copy()
else:
    # For "All Time", start with all data and filter per metric
    filtered_df = df.copy()

# Apply type and source filters to the dataframe
columns_to_keep = ['date']  # Always keep the date column

# Get list of columns to keep based on filters
for col in filtered_df.columns:
    if col == 'date':
        continue
        
    # Get metadata for the column
    base_column = col.split('__', 1)[1] if '__' in col else col
    metadata = None
    for model in ALL_MODELS:
        metadata = model.get_field_metadata(base_column)
        if metadata:
            break
    
    # Check if column matches type filter
    type_match = not selected_types or (metadata and metadata.category in selected_types)
    
    # Check if column matches source filter
    source_match = not selected_sources or any(col.startswith(source) for source in selected_sources)
    
    # Keep column if it matches both filters
    if type_match and source_match:
        columns_to_keep.append(col)

# Apply filters to dataframe
filtered_df = filtered_df[columns_to_keep]

# Create separate dataframes for summed and averaged metrics
summed_metrics = []
averaged_metrics = []

# Determine which metrics should be summed vs averaged
for column in filtered_df.columns:
    if column == 'date':
        continue
        
    # Get metadata for the column
    base_column = column.split('__', 1)[1] if '__' in column else column
    metadata = None
    for model in ALL_MODELS:
        metadata = model.get_field_metadata(base_column)
        if metadata:
            break
    
    if metadata and metadata.sum_weekly:
        summed_metrics.append(column)
    else:
        averaged_metrics.append(column)

# Process summed metrics (weekly totals)
if summed_metrics:
    summed_df = filtered_df[['date'] + summed_metrics].set_index('date')
    summed_df = summed_df.resample('W-MON').sum().reset_index()
else:
    summed_df = pd.DataFrame(columns=['date'])

# Process averaged metrics (keep as daily data and add rolling average)
if averaged_metrics:
    averaged_df = filtered_df[['date'] + averaged_metrics].copy()
    # Add 7-day centered rolling average for each metric
    for col in averaged_metrics:
        averaged_df[f'{col}_rolling'] = averaged_df[col].rolling(window=7, min_periods=1, center=True).mean()
else:
    averaged_df = pd.DataFrame(columns=['date'])

# Get list of columns to plot (excluding date and empty columns)
columns_to_plot = [col for col in filtered_df.columns 
                  if col != 'date' and not filtered_df[col].isna().all()]

if not columns_to_plot:
    st.info("No metrics available for the selected filters.")
    st.stop()

# Calculate number of rows needed (3 plots per row)
num_rows = math.ceil(len(columns_to_plot) / 3)

# Add color mapping for categories
CATEGORY_COLORS = {
    MetricCategory.RECOVERY: '#3498db',  # Blue
    MetricCategory.ACTIVITY: '#e74c3c',  # Red
    MetricCategory.NUTRITION: '#2ecc71',  # Green
}

# Update plot margins to be smaller
def update_plot_layout(fig, y_axis_label: str, y_min: float | None = None, y_max: float | None = None):
    """Update plot layout with consistent styling and smaller margins"""
    fig.update_layout(
        xaxis_title="",
        yaxis_title=y_axis_label,
        margin=dict(l=10, r=10, t=5, b=10),  # Reduced margins
        height=250,  # Reduced height
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            title_standoff=15,  # Reduced standoff
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

# Create plots in a 3x3 grid
for row in range(num_rows):
    # Create 3 columns for this row
    cols = st.columns(3)
    
    # Plot up to 3 metrics in this row
    for col_idx in range(3):
        metric_idx = row * 3 + col_idx
        if metric_idx < len(columns_to_plot):
            column = columns_to_plot[metric_idx]
            with cols[col_idx]:
                # Get metadata including source
                source, pretty_name, category, unit, sum_weekly = get_column_metadata(column)
                
                # For "All Time", filter this metric's data to its own date range
                if start_date is None:
                    # Find the first non-null value for this metric
                    metric_data = filtered_df[['date', column]].dropna(subset=[column])
                    if not metric_data.empty:
                        metric_start_date = metric_data['date'].min()
                        metric_mask = (filtered_df['date'] >= metric_start_date) & (filtered_df['date'] <= end_date)
                        plot_df = filtered_df.loc[metric_mask].copy()
                    else:
                        # Skip this metric if it has no data
                        continue
                else:
                    plot_df = filtered_df.copy()
                
                # Get color based on category
                category_color = CATEGORY_COLORS.get(category, '#3498db') if category else '#3498db'
                
                # Create y-axis label with only unit
                y_axis_label = unit if unit else ""
                
                # Create a container with grey background for the chart
                with st.container(border=True):
                    # Add title using Streamlit with improved styling
                    st.markdown(
                        f"<h2 style='color: #2c3e50; font-size: 1.1rem; margin-bottom: 0.5rem;'>{pretty_name} <span style='color: #7f8c8d; font-size: 0.9rem;'>({source.title()})</span></h2>",
                        unsafe_allow_html=True
                    )
                    
                    # Choose the appropriate dataframe and plot type
                    if sum_weekly:
                        # Use bar chart with weekly summed data
                        plot_df = plot_df[['date', column]].set_index('date')
                        plot_df = plot_df.resample('W-MON').sum().reset_index()
                        fig = px.bar(
                            plot_df,
                            x='date',
                            y=column,
                            title=None,
                            labels={
                                'date': 'Date',
                                column: ''
                            }
                        )
                        update_plot_layout(fig, y_axis_label)
                        
                        # Update traces for bar appearance with category color
                        fig.update_traces(
                            marker_color=category_color,
                            marker_line_width=0,
                            opacity=0.85,
                            marker_pattern_shape=""
                        )
                    else:
                        # Use line chart with daily data and rolling average
                        # Add 7-day centered rolling average
                        plot_df[f'{column}_rolling'] = plot_df[column].rolling(window=7, min_periods=1, center=True).mean()
                        
                        # Create custom hover text
                        plot_df['hover_text'] = plot_df.apply(
                            lambda row: f"Date: {row['date'].strftime('%Y-%m-%d')}<br>" +
                                      f"Actual: {row[column]:.1f}<br>" +
                                      f"7-day Avg: {row[f'{column}_rolling']:.1f}",
                            axis=1
                        )
                        
                        # Calculate y-axis range based on rolling average
                        rolling_min = plot_df[f'{column}_rolling'].min()
                        rolling_max = plot_df[f'{column}_rolling'].max()
                        rolling_range = rolling_max - rolling_min
                        # Add 10% padding to the range
                        y_min = rolling_min - (rolling_range * 0.1)
                        y_max = rolling_max + (rolling_range * 0.1)

                        fig = px.line(
                            plot_df,
                            x='date',
                            y=[column, f'{column}_rolling'],
                            title=None,
                            labels={
                                'date': 'Date',
                                'value': '',
                                'variable': ''
                            },
                            hover_data={'hover_text': True},
                            range_y=[y_min, y_max]  # Set y-axis range based on rolling average
                        )
                        update_plot_layout(fig, y_axis_label, y_min, y_max)
                        
                        # Update traces for daily data and rolling average with category color
                        fig.update_traces(
                            line_shape='spline',
                            line_smoothing=1.3,
                            mode='lines',
                            selector=dict(name=f'{column}_rolling')
                        ).update_traces(
                            line=dict(
                                color=category_color,
                                width=2.5
                            ),
                            hovertemplate='%{customdata[0]}<extra></extra>',
                            selector=dict(name=f'{column}_rolling')
                        ).update_traces(
                            line=dict(
                                color=category_color,
                                width=1
                            ),
                            opacity=0.3,
                            hoverinfo='none',
                            hovertemplate=None,
                            selector=dict(name=column)
                        )
                    
                    # Display the plot with a subtle border
                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                        config={'displayModeBar': False}
                    )

# Helper function to format dates nicely
def format_date(date):
    """Format a date into a nice readable format like '19th May 2025'"""
    # Get the day suffix (st, nd, rd, th)
    day = date.day
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    
    # Format the date with day with suffix, month name, and year
    return date.strftime(f"%d{suffix} %B %Y")

def get_day_name(date):
    """Get the full day name from a date"""
    return date.strftime("%A")

# Format and display the data table
display_df = filtered_df.copy()

# Sort by date in descending order (most recent first)
display_df = display_df.sort_values('date', ascending=False)

# Split date into day and formatted date columns
display_df['day'] = display_df['date'].apply(get_day_name)
display_df['date'] = display_df['date'].apply(format_date)

# Reorder columns to put day and date first
cols = ['day', 'date'] + [col for col in display_df.columns if col not in ['day', 'date']]
display_df = display_df[cols]

# Format numeric columns to 2 decimal places
numeric_cols = [col for col in display_df.columns if display_df[col].dtype in ['float64', 'int64']]
display_df[numeric_cols] = display_df[numeric_cols].round(2)

# Get pretty names for columns with source prefix
column_names = {}
for col in display_df.columns:
    if col == 'day':
        column_names[col] = 'Day'
    elif col == 'date':
        column_names[col] = 'Date'
    else:
        # Get metadata including source
        source, pretty_name, _, unit, _ = get_column_metadata(col)
        # Create column name with source prefix
        if unit:
            column_names[col] = f"{source.title()} - {pretty_name} ({unit})"
        else:
            column_names[col] = f"{source.title()} - {pretty_name}"

# Rename columns for display
display_df = display_df.rename(columns=column_names)

# Display the table
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
) 