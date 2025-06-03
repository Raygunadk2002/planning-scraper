"""
Streamlit Cloud Compatible - London Planning Application Monitor
Simplified version for cloud deployment with sample data
Version: 2.0 - Cloud Ready (2025-06-03)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Sample data for demonstration
SAMPLE_APPLICATIONS = [
    {
        'project_id': '25/03344/LBC',
        'borough': 'Westminster',
        'title': 'Structural monitoring survey to inform the Restoration and Renewal Programme for the Palace of Westminster',
        'address': 'Palace Of Westminster St Margaret Street London SW1P 3JX',
        'detected_keywords': 'monitoring',
        'submission_date': '2025-05-16',
        'application_url': 'https://idoxpa.westminster.gov.uk/online-applications/applicationDetails.do?keyVal=SWCO2GRPGV500'
    },
    {
        'project_id': '25/03211/ADFULL',
        'borough': 'Westminster',
        'title': 'Details of Biodiversity plan, details of tree protection, Arboricultural method statement',
        'address': 'Flat 1 43 Leamington Road Villas London W11 1HT',
        'detected_keywords': 'monitoring, arboricultural, supervision',
        'submission_date': '2025-05-12',
        'application_url': 'https://idoxpa.westminster.gov.uk/online-applications/applicationDetails.do?keyVal=SW5C85RPFLX00'
    },
    {
        'project_id': '25/02299/ADFULL',
        'borough': 'Westminster',
        'title': 'Details of monitoring strategy pursuant to conditions for Lords Cricket Ground',
        'address': 'Ground Floor Lords Cricket Ground St Johns Wood Road London NW8 8QN',
        'detected_keywords': 'monitoring',
        'submission_date': '2025-04-03',
        'application_url': 'https://idoxpa.westminster.gov.uk/online-applications/applicationDetails.do?keyVal=SU5HXWRPGAL00'
    },
    {
        'project_id': '17/08991/ADFULL',
        'borough': 'Westminster',
        'title': 'Details of noise monitoring regime pursuant to planning permission',
        'address': '46 Berkeley Square London W1J 5AT',
        'detected_keywords': 'monitoring, noise',
        'submission_date': '2017-10-10',
        'application_url': 'https://idoxpa.westminster.gov.uk/online-applications/applicationDetails.do?keyVal=OXLNSYRPIU400'
    },
    {
        'project_id': '22/01564/ADFULL',
        'borough': 'Westminster',
        'title': 'Environmental monitoring instrumentation installation',
        'address': '11 Stanhope Gate London W1K 1AN',
        'detected_keywords': 'monitoring, environmental',
        'submission_date': '2022-03-09',
        'application_url': 'https://idoxpa.westminster.gov.uk/online-applications/applicationDetails.do?keyVal=R8GXWDRPIFM00'
    }
]

# Configure Streamlit page
st.set_page_config(
    page_title="London Planning Monitor",
    page_icon="🏗️",
    layout="wide"
)

def main():
    """Main Streamlit application"""
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Data Explorer", "About"]
    )
    
    # Main title
    st.title("🏗️ London Planning Application Monitor")
    st.markdown("Monitor planning applications with environmental monitoring requirements across London boroughs")
    
    # Route to appropriate page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Data Explorer":
        show_data_explorer()
    elif page == "About":
        show_about()

def show_dashboard():
    """Dashboard page with overview statistics and charts"""
    st.header("📊 Dashboard Overview")
    
    # Convert sample data to DataFrame
    df = pd.DataFrame(SAMPLE_APPLICATIONS)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Applications",
            value=len(df),
            help="Total planning applications with monitoring keywords"
        )
    
    with col2:
        borough_count = df['borough'].nunique()
        st.metric(
            label="Boroughs Covered",
            value=borough_count,
            help="Number of boroughs with applications found"
        )
    
    with col3:
        # Count unique keywords
        all_keywords = []
        for keywords in df['detected_keywords']:
            all_keywords.extend([k.strip() for k in keywords.split(',')])
        unique_keywords = len(set(all_keywords))
        
        st.metric(
            label="Keywords Found",
            value=unique_keywords,
            help="Number of monitoring keywords found in applications"
        )
    
    with col4:
        st.metric(
            label="Recent Applications",
            value=len(df[df['submission_date'] >= '2025-01-01']),
            help="Applications from 2025"
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Applications by borough
        st.subheader("📍 Applications by Borough")
        borough_counts = df['borough'].value_counts()
        borough_df = pd.DataFrame({
            'Borough': borough_counts.index,
            'Applications': borough_counts.values
        })
        
        fig = px.bar(
            borough_df,
            x='Borough',
            y='Applications',
            title="Planning Applications by Borough"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Applications by keyword type
        st.subheader("🔍 Applications by Monitoring Type")
        
        # Count keywords
        keyword_counts = {}
        for keywords in df['detected_keywords']:
            for keyword in keywords.split(','):
                keyword = keyword.strip()
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        keyword_df = pd.DataFrame({
            'Keyword': list(keyword_counts.keys()),
            'Applications': list(keyword_counts.values())
        })
        
        fig = px.pie(
            keyword_df,
            values='Applications',
            names='Keyword',
            title="Applications by Monitoring Type"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent applications
    st.subheader("🎯 Recent Applications")
    
    # Convert submission_date to datetime for sorting
    df['submission_date'] = pd.to_datetime(df['submission_date'])
    recent_df = df.sort_values('submission_date', ascending=False).head(3)
    
    for idx, app in recent_df.iterrows():
        with st.expander(f"📋 {app['project_id']} - {app['address'][:50]}..."):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Description:** {app['title']}")
                st.write(f"**Address:** {app['address']}")
                st.write(f"**Keywords:** {app['detected_keywords']}")
                st.write(f"**Submitted:** {app['submission_date'].strftime('%d %B %Y')}")
            
            with col2:
                st.write(f"**Borough:** {app['borough']}")
                if app['application_url']:
                    st.link_button("View Application", app['application_url'])

def show_data_explorer():
    """Data explorer page with filtering and detailed view"""
    st.header("🔍 Data Explorer")
    
    # Convert sample data to DataFrame
    df = pd.DataFrame(SAMPLE_APPLICATIONS)
    df['submission_date'] = pd.to_datetime(df['submission_date'])
    
    # Filters
    st.subheader("Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        boroughs = ['All'] + sorted(df['borough'].unique().tolist())
        selected_borough = st.selectbox("Borough", boroughs)
    
    with col2:
        # Get all unique keywords
        all_keywords = set()
        for keywords in df['detected_keywords']:
            all_keywords.update([k.strip() for k in keywords.split(',')])
        
        keywords = ['All'] + sorted(list(all_keywords))
        selected_keyword = st.selectbox("Monitoring Type", keywords)
    
    with col3:
        year_range = st.slider(
            "Year Range",
            min_value=2017,
            max_value=2025,
            value=(2020, 2025)
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_borough != 'All':
        filtered_df = filtered_df[filtered_df['borough'] == selected_borough]
    
    if selected_keyword != 'All':
        filtered_df = filtered_df[
            filtered_df['detected_keywords'].str.contains(selected_keyword, case=False)
        ]
    
    # Year filter
    filtered_df = filtered_df[
        (filtered_df['submission_date'].dt.year >= year_range[0]) &
        (filtered_df['submission_date'].dt.year <= year_range[1])
    ]
    
    # Display results
    st.subheader(f"📊 Results: {len(filtered_df)} applications found")
    
    if len(filtered_df) > 0:
        # Display as expandable cards
        for idx, app in filtered_df.iterrows():
            with st.expander(f"📋 {app['project_id']} - {app['borough']} - {app['submission_date'].strftime('%Y-%m-%d')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Address:** {app['address']}")
                    st.write(f"**Description:** {app['title']}")
                    st.write(f"**Keywords:** {app['detected_keywords']}")
                
                with col2:
                    st.write(f"**Submitted:** {app['submission_date'].strftime('%d %b %Y')}")
                    if app['application_url']:
                        st.link_button("View Details", app['application_url'])
    else:
        st.info("No applications found matching the selected filters.")

def show_about():
    """About page with system information"""
    st.header("ℹ️ About This System")
    
    st.markdown("""
    ### 🎯 London Planning Application Monitor
    
    This system monitors planning applications across London boroughs for environmental monitoring keywords such as:
    - **Monitoring** (general environmental monitoring)
    - **Noise monitoring** (acoustic assessments)
    - **Vibration monitoring** (construction impacts)
    - **Environmental monitoring** (air quality, pollution)
    - **Arboricultural monitoring** (tree protection)
    
    ### 🏗️ System Status
    - **✅ Westminster Borough**: Fully operational with anti-bot bypass
    - **⚙️ Other Boroughs**: Ready for implementation
    - **📊 Current Data**: Sample applications demonstrating system capabilities
    
    ### 🔧 Technical Features
    - Real-time scraping with CSRF token handling
    - Interactive dashboard with filtering and charts
    - Export capabilities for data analysis
    - Cloud-ready deployment architecture
    
    ### 📈 Sample Data
    The current dashboard shows **{} sample applications** from Westminster borough, 
    including high-profile locations like:
    - Palace of Westminster
    - Lords Cricket Ground
    - Berkeley Square
    
    ### 🚀 Production Deployment
    In production, this system:
    1. Scrapes multiple London borough planning portals
    2. Automatically detects environmental monitoring keywords
    3. Stores data in structured database
    4. Provides real-time alerts for new applications
    5. Enables data export for regulatory compliance
    """.format(len(SAMPLE_APPLICATIONS)))
    
    # System architecture diagram
    st.subheader("🏗️ System Architecture")
    
    st.markdown("""
    ```
    Planning Portals → Web Scrapers → Database → Dashboard
         ↓                ↓             ↓          ↓
    Westminster      CSRF Bypass    SQLite     Streamlit
    Camden           Form Analysis   29 Apps    Charts
    Tower Hamlets    HTML Parsing   Real-time   Filtering
    H&F              Rate Limiting   Storage     Export
    Southwark        Error Handling  Logging     Alerts
    ```
    """)

if __name__ == "__main__":
    main() 