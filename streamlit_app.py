"""
Streamlit Dashboard for London Planning Application Monitor
Provides web interface for viewing, filtering, and exporting scraped planning data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import threading
from typing import List, Dict

from config import STREAMLIT_CONFIG, BOROUGHS_CONFIG, MONITORING_KEYWORDS, EXPORT_CONFIG
from database import PlanningDatabase
from scraper_manager import ScrapingManager, ScheduledScraper

# Configure Streamlit page
st.set_page_config(
    page_title=STREAMLIT_CONFIG['page_title'],
    page_icon=STREAMLIT_CONFIG['page_icon'],
    layout=STREAMLIT_CONFIG['layout']
)

# Initialize session state
if 'scraping_manager' not in st.session_state:
    st.session_state.scraping_manager = ScrapingManager()
if 'database' not in st.session_state:
    st.session_state.database = PlanningDatabase()
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

def main():
    """Main Streamlit application"""
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Data Explorer", "Scraping Control", "Export Data", "Settings"]
    )
    
    # Main title
    st.title("🏗️ London Planning Application Monitor")
    st.markdown("Monitor planning applications with environmental monitoring requirements across London boroughs")
    
    # Route to appropriate page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Data Explorer":
        show_data_explorer()
    elif page == "Scraping Control":
        show_scraping_control()
    elif page == "Export Data":
        show_export_page()
    elif page == "Settings":
        show_settings()

def show_dashboard():
    """Dashboard page with overview statistics and charts"""
    st.header("📊 Dashboard Overview")
    
    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Refresh Data"):
            st.session_state.last_refresh = datetime.now()
            st.rerun()
    
    with col2:
        st.write(f"Last updated: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    # Get statistics
    try:
        stats = st.session_state.database.get_statistics()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Applications",
                value=stats.get('total_applications', 0),
                help="Total planning applications with monitoring keywords"
            )
        
        with col2:
            borough_count = len(stats.get('by_borough', {}))
            st.metric(
                label="Boroughs Covered",
                value=borough_count,
                help="Number of boroughs with applications found"
            )
        
        with col3:
            keyword_with_apps = sum(1 for count in stats.get('by_keyword', {}).values() if count > 0)
            st.metric(
                label="Keywords Found",
                value=keyword_with_apps,
                help="Number of monitoring keywords found in applications"
            )
        
        with col4:
            recent_scrapes = len([v for v in stats.get('last_scrapes', {}).values() if v])
            st.metric(
                label="Recent Scrapes",
                value=recent_scrapes,
                help="Number of boroughs scraped recently"
            )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Applications by borough
            if stats.get('by_borough'):
                st.subheader("📍 Applications by Borough")
                borough_df = pd.DataFrame(
                    list(stats['by_borough'].items()),
                    columns=['Borough', 'Applications']
                )
                fig = px.bar(
                    borough_df,
                    x='Borough',
                    y='Applications',
                    title="Planning Applications by Borough"
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Applications by keyword
            if stats.get('by_keyword'):
                st.subheader("🔍 Applications by Monitoring Type")
                keyword_df = pd.DataFrame(
                    list(stats['by_keyword'].items()),
                    columns=['Keyword', 'Applications']
                )
                keyword_df = keyword_df[keyword_df['Applications'] > 0]
                
                if not keyword_df.empty:
                    fig = px.pie(
                        keyword_df,
                        values='Applications',
                        names='Keyword',
                        title="Applications by Monitoring Type"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No applications found with monitoring keywords yet")
        
        # Recent activity
        st.subheader("⏰ Recent Scraping Activity")
        if stats.get('last_scrapes'):
            scrape_df = pd.DataFrame(
                list(stats['last_scrapes'].items()),
                columns=['Borough', 'Last Scrape']
            )
            scrape_df['Last Scrape'] = pd.to_datetime(scrape_df['Last Scrape'], errors='coerce')
            scrape_df['Status'] = scrape_df['Last Scrape'].apply(
                lambda x: '🟢 Recent' if pd.notna(x) and (datetime.now() - x).days < 1 
                         else '🟡 Outdated' if pd.notna(x)
                         else '🔴 Never'
            )
            st.dataframe(scrape_df, use_container_width=True)
        else:
            st.info("No scraping activity recorded yet")
    
    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")

def show_data_explorer():
    """Data explorer page with filtering and detailed view"""
    st.header("🔍 Data Explorer")
    
    # Filters
    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        selected_borough = st.selectbox(
            "Borough",
            options=["All"] + list(BOROUGHS_CONFIG.keys()),
            index=0
        )
    
    with col2:
        selected_keyword = st.selectbox(
            "Monitoring Type",
            options=["All"] + MONITORING_KEYWORDS,
            index=0
        )
    
    with col3:
        date_from = st.date_input(
            "Date From",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now()
        )
    
    with col4:
        date_to = st.date_input(
            "Date To",
            value=datetime.now(),
            max_value=datetime.now()
        )
    
    # Apply filters
    try:
        df = st.session_state.database.get_applications(
            borough=selected_borough if selected_borough != "All" else None,
            keyword=selected_keyword if selected_keyword != "All" else None,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None
        )
        
        if df.empty:
            st.info("No applications found matching the selected filters.")
            return
        
        # Display results
        st.subheader(f"📋 Results ({len(df)} applications)")
        
        # Configure display columns
        display_columns = [
            'project_id', 'borough', 'title', 'address', 
            'submission_date', 'detected_keywords'
        ]
        
        # Make dataframe interactive
        edited_df = st.data_editor(
            df[display_columns],
            use_container_width=True,
            hide_index=True,
            column_config={
                'project_id': st.column_config.TextColumn('Project ID', width='small'),
                'borough': st.column_config.TextColumn('Borough', width='small'),
                'title': st.column_config.TextColumn('Title', width='large'),
                'address': st.column_config.TextColumn('Address', width='medium'),
                'submission_date': st.column_config.DateColumn('Submission Date', width='small'),
                'detected_keywords': st.column_config.TextColumn('Keywords', width='medium'),
            }
        )
        
        # Application details
        if st.checkbox("Show detailed view"):
            st.subheader("📄 Application Details")
            
            # Select application
            if len(df) > 0:
                selected_idx = st.selectbox(
                    "Select an application to view details:",
                    options=range(len(df)),
                    format_func=lambda x: f"{df.iloc[x]['project_id']} - {df.iloc[x]['title'][:50]}..."
                )
                
                selected_app = df.iloc[selected_idx]
                
                # Display details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Project ID:**", selected_app['project_id'])
                    st.write("**Borough:**", selected_app['borough'])
                    st.write("**Title:**", selected_app['title'])
                    st.write("**Address:**", selected_app['address'])
                
                with col2:
                    st.write("**Submission Date:**", selected_app['submission_date'])
                    st.write("**Keywords:**", selected_app['detected_keywords'])
                    st.write("**Scraped:**", selected_app['scraped_timestamp'])
                    
                    if selected_app['application_url']:
                        st.markdown(f"[🔗 View Application]({selected_app['application_url']})")
    
    except Exception as e:
        st.error(f"Error loading data: {e}")

def show_scraping_control():
    """Scraping control page for manual and scheduled scraping"""
    st.header("⚙️ Scraping Control")
    
    # Get current status
    try:
        status = st.session_state.scraping_manager.get_scraping_status()
        
        # Status overview
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔄 Scraping Status")
            if status['is_running']:
                st.success("✅ Scraping is currently running")
            else:
                st.info("⏸️ Scraping is not running")
            
            st.write(f"**Total Boroughs:** {status['total_boroughs']}")
            
        with col2:
            st.subheader("📊 Database Status")
            db_stats = status.get('database_stats', {})
            st.write(f"**Total Applications:** {db_stats.get('total_applications', 0)}")
            st.write(f"**Boroughs with Data:** {len(db_stats.get('by_borough', {}))}")
        
        # Manual scraping controls
        st.subheader("🎯 Manual Scraping")
        
        col1, col2 = st.columns(2)
        
        with col1:
            scrape_mode = st.radio(
                "Scraping Mode",
                ["All Boroughs", "Specific Borough"]
            )
            
            if scrape_mode == "Specific Borough":
                selected_borough = st.selectbox(
                    "Select Borough",
                    options=list(BOROUGHS_CONFIG.keys())
                )
        
        with col2:
            custom_keywords = st.text_area(
                "Custom Keywords (one per line, leave empty for default)",
                height=100
            )
            
            keywords = None
            if custom_keywords.strip():
                keywords = [kw.strip() for kw in custom_keywords.split('\n') if kw.strip()]
        
        # Scraping buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Start Scraping", type="primary"):
                if not status['is_running']:
                    with st.spinner("Starting scraping..."):
                        if scrape_mode == "All Boroughs":
                            # Run in background thread to avoid blocking UI
                            threading.Thread(
                                target=lambda: st.session_state.scraping_manager.scrape_all_boroughs(keywords),
                                daemon=True
                            ).start()
                            st.success("Scraping started for all boroughs!")
                        else:
                            result = st.session_state.scraping_manager.scrape_single_borough(
                                selected_borough, keywords
                            )
                            if result['success']:
                                st.success(f"✅ Scraping completed for {selected_borough}")
                                st.write(f"Found {result['new_applications']} new applications")
                            else:
                                st.error(f"❌ Scraping failed: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("Scraping is already running!")
        
        with col2:
            if st.button("⏹️ Stop Scraping"):
                st.session_state.scraping_manager.stop_scraping()
                st.info("Stop signal sent")
        
        with col3:
            if st.button("🧹 Initialize Scrapers"):
                st.session_state.scraping_manager.initialize_scrapers()
                st.success("Scrapers initialized")
        
        # Borough status table
        st.subheader("🏛️ Borough Status")
        if status.get('boroughs'):
            borough_status = []
            for borough, info in status['boroughs'].items():
                borough_status.append({
                    'Borough': borough,
                    'Status': info['status'],
                    'Last Run': info['last_run'] or 'Never',
                    'Applications Found': info['applications_found'],
                    'Last Error': info['last_error'] or 'None'
                })
            
            status_df = pd.DataFrame(borough_status)
            st.dataframe(status_df, use_container_width=True)
        else:
            st.info("No borough status available. Initialize scrapers first.")
    
    except Exception as e:
        st.error(f"Error loading scraping status: {e}")

def show_export_page():
    """Export data page"""
    st.header("📤 Export Data")
    
    # Export filters
    st.subheader("Export Filters")
    col1, col2 = st.columns(2)
    
    with col1:
        export_borough = st.selectbox(
            "Borough",
            options=["All"] + list(BOROUGHS_CONFIG.keys()),
            index=0,
            key="export_borough"
        )
    
    with col2:
        export_keyword = st.selectbox(
            "Monitoring Type",
            options=["All"] + MONITORING_KEYWORDS,
            index=0,
            key="export_keyword"
        )
    
    # Export format
    export_format = st.radio(
        "Export Format",
        ["CSV", "Excel"],
        horizontal=True
    )
    
    # Preview data
    try:
        preview_df = st.session_state.database.get_applications(
            borough=export_borough if export_borough != "All" else None,
            keyword=export_keyword if export_keyword != "All" else None
        )
        
        st.subheader(f"📊 Data Preview ({len(preview_df)} records)")
        if not preview_df.empty:
            st.dataframe(preview_df.head(10), use_container_width=True)
            
            # Export buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if export_format == "CSV":
                    csv_data = preview_df.to_csv(index=False)
                    st.download_button(
                        label="📄 Download CSV",
                        data=csv_data,
                        file_name=EXPORT_CONFIG['csv_filename'],
                        mime="text/csv"
                    )
            
            with col2:
                if export_format == "Excel":
                    # Convert to Excel in memory
                    from io import BytesIO
                    excel_buffer = BytesIO()
                    preview_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                    excel_data = excel_buffer.getvalue()
                    
                    st.download_button(
                        label="📊 Download Excel",
                        data=excel_data,
                        file_name=EXPORT_CONFIG['excel_filename'],
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.info("No data available for export with current filters.")
    
    except Exception as e:
        st.error(f"Error preparing export data: {e}")

def show_settings():
    """Settings page"""
    st.header("⚙️ Settings")
    
    # Database settings
    st.subheader("🗄️ Database")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Check Database Status"):
            try:
                stats = st.session_state.database.get_statistics()
                st.success("✅ Database is accessible")
                st.write(f"Total applications: {stats.get('total_applications', 0)}")
            except Exception as e:
                st.error(f"❌ Database error: {e}")
    
    with col2:
        if st.button("🧹 Clean Up Resources"):
            st.session_state.scraping_manager.cleanup()
            st.success("✅ Resources cleaned up")
    
    # Configuration display
    st.subheader("📋 Current Configuration")
    
    with st.expander("Borough Configuration"):
        st.json(BOROUGHS_CONFIG)
    
    with st.expander("Monitoring Keywords"):
        for i, keyword in enumerate(MONITORING_KEYWORDS, 1):
            st.write(f"{i}. {keyword}")
    
    # Application info
    st.subheader("ℹ️ About")
    st.markdown("""
    **London Planning Application Monitor**
    
    This application scrapes planning applications from London borough portals 
    to identify projects with environmental monitoring requirements.
    
    **Features:**
    - Automated scraping of 5 London boroughs
    - Keyword detection for monitoring requirements
    - SQLite database storage
    - Export to CSV/Excel
    - Polite scraping with rate limiting
    
    **Monitored Keywords:**
    - Remote monitoring
    - Noise monitoring
    - Vibration monitoring
    - Dust monitoring
    - Subsidence monitoring
    """)

if __name__ == "__main__":
    main() 