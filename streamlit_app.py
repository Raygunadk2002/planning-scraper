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
    """Scraping control page for manual and scheduled scraping with real-time monitoring"""
    st.header("⚙️ Scraping Control & Live Monitor")
    
    # Initialize session state for real-time updates
    if 'scraping_logs' not in st.session_state:
        st.session_state.scraping_logs = []
    if 'scraping_progress' not in st.session_state:
        st.session_state.scraping_progress = {}
    if 'current_scraping_keywords' not in st.session_state:
        st.session_state.current_scraping_keywords = MONITORING_KEYWORDS
    
    # Get current status
    try:
        status = st.session_state.scraping_manager.get_scraping_status()
        
        # Real-time Status Display
        st.subheader("🔴 Live Status")
        
        # Top status row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if status['is_running']:
                st.metric("Status", "🟢 ACTIVE", delta="Running")
            else:
                st.metric("Status", "🔴 IDLE", delta="Stopped")
        
        with col2:
            total_apps = status.get('database_stats', {}).get('total_applications', 0)
            st.metric("Total Apps", total_apps)
        
        with col3:
            active_boroughs = len([b for b in status.get('boroughs', {}).values() 
                                 if b.get('status') == 'running'])
            st.metric("Active Boroughs", active_boroughs)
        
        with col4:
            st.metric("Keywords", len(st.session_state.current_scraping_keywords))
        
        # Live Progress Section
        if status['is_running']:
            st.subheader("⏳ Live Progress")
            
            # Overall progress
            borough_count = len(BOROUGHS_CONFIG)
            completed_count = len([b for name, b in status.get('boroughs', {}).items() 
                                 if b.get('status') in ['completed', 'error']])
            
            overall_progress = completed_count / borough_count if borough_count > 0 else 0
            st.progress(overall_progress, text=f"Overall Progress: {completed_count}/{borough_count} boroughs")
            
            # Individual borough progress
            st.write("**Borough Progress:**")
            
            for borough_name, borough_info in status.get('boroughs', {}).items():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    if borough_info.get('status') == 'running':
                        st.write(f"🔄 **{borough_name}**: Searching keywords...")
                        # Show current keyword if available
                        current_keyword = st.session_state.scraping_progress.get(borough_name, {}).get('current_keyword')
                        if current_keyword:
                            st.caption(f"Current: {current_keyword}")
                    elif borough_info.get('status') == 'completed':
                        st.write(f"✅ **{borough_name}**: Complete")
                    elif borough_info.get('status') == 'error':
                        st.write(f"❌ **{borough_name}**: Error")
                    else:
                        st.write(f"⏸️ **{borough_name}**: {borough_info.get('status', 'Unknown')}")
                
                with col2:
                    apps_found = borough_info.get('applications_found', 0)
                    st.write(f"Apps: {apps_found}")
                
                with col3:
                    if borough_info.get('last_run'):
                        last_run = datetime.fromisoformat(borough_info['last_run']).strftime("%H:%M:%S")
                        st.write(f"Last: {last_run}")
        
        # Current Keywords Being Searched
        st.subheader("🔍 Current Search Keywords")
        
        # Display keywords in a nice grid
        keyword_cols = st.columns(3)
        for i, keyword in enumerate(st.session_state.current_scraping_keywords):
            with keyword_cols[i % 3]:
                # Show if this keyword is currently being searched
                is_active = any(
                    st.session_state.scraping_progress.get(borough, {}).get('current_keyword') == keyword
                    for borough in BOROUGHS_CONFIG.keys()
                )
                if is_active:
                    st.success(f"🔍 {keyword}")
                else:
                    st.info(f"📝 {keyword}")
        
        # Manual scraping controls
        st.subheader("🎯 Manual Scraping Controls")
        
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
            st.write("**Keywords to Search:**")
            custom_keywords = st.text_area(
                "Custom Keywords (one per line, leave empty for default)",
                height=100,
                placeholder="\n".join(MONITORING_KEYWORDS)
            )
            
            keywords = None
            if custom_keywords.strip():
                keywords = [kw.strip() for kw in custom_keywords.split('\n') if kw.strip()]
                st.session_state.current_scraping_keywords = keywords
            else:
                st.session_state.current_scraping_keywords = MONITORING_KEYWORDS
        
        # Action buttons
        st.subheader("🚀 Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🚀 Start Scraping", type="primary", use_container_width=True):
                if not status['is_running']:
                    with st.spinner("Starting scraping..."):
                        if scrape_mode == "All Boroughs":
                            # Start scraping with progress tracking
                            def scraping_with_progress():
                                try:
                                    st.session_state.scraping_manager.scrape_all_boroughs(keywords)
                                    st.session_state.scraping_logs.append(
                                        f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Scraping completed for all boroughs"
                                    )
                                except Exception as e:
                                    st.session_state.scraping_logs.append(
                                        f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Scraping error: {str(e)}"
                                    )
                            
                            threading.Thread(target=scraping_with_progress, daemon=True).start()
                            st.success("🚀 Scraping started for all boroughs!")
                            st.session_state.scraping_logs.append(
                                f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Started scraping all boroughs"
                            )
                        else:
                            result = st.session_state.scraping_manager.scrape_single_borough(
                                selected_borough, keywords
                            )
                            if result['success']:
                                st.success(f"✅ Scraping completed for {selected_borough}")
                                st.write(f"Found {result['new_applications']} new applications")
                                st.session_state.scraping_logs.append(
                                    f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {selected_borough}: {result['new_applications']} new apps"
                                )
                            else:
                                st.error(f"❌ Scraping failed: {result.get('error', 'Unknown error')}")
                                st.session_state.scraping_logs.append(
                                    f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {selected_borough}: {result.get('error')}"
                                )
                    st.rerun()
                else:
                    st.warning("Scraping is already running!")
        
        with col2:
            if st.button("⏹️ Stop", use_container_width=True):
                st.session_state.scraping_manager.stop_scraping()
                st.info("Stop signal sent")
                st.session_state.scraping_logs.append(
                    f"[{datetime.now().strftime('%H:%M:%S')}] ⏹️ Stop signal sent"
                )
                st.rerun()
        
        with col3:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        with col4:
            if st.button("🧹 Reset", use_container_width=True):
                st.session_state.scraping_manager.initialize_scrapers()
                st.success("Scrapers reset")
                st.session_state.scraping_logs.append(
                    f"[{datetime.now().strftime('%H:%M:%S')}] 🧹 Scrapers initialized"
                )
                st.rerun()
        
        # Live Activity Log
        st.subheader("📊 Live Activity Log")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto-refresh (every 5 seconds)", value=True)
        
        if auto_refresh:
            # Auto-refresh using experimental_rerun with timer
            if status['is_running']:
                time.sleep(2)  # Small delay to prevent too frequent updates
                st.rerun()
        
        # Show recent logs
        log_container = st.container()
        with log_container:
            if st.session_state.scraping_logs:
                # Show last 10 log entries
                recent_logs = st.session_state.scraping_logs[-10:]
                for log_entry in reversed(recent_logs):  # Show newest first
                    if "✅" in log_entry:
                        st.success(log_entry)
                    elif "❌" in log_entry:
                        st.error(log_entry)
                    elif "🚀" in log_entry:
                        st.info(log_entry)
                    else:
                        st.write(log_entry)
            else:
                st.info("No activity logs yet. Start scraping to see live updates!")
        
        # Clear logs button
        if st.button("🗑️ Clear Logs"):
            st.session_state.scraping_logs = []
            st.rerun()
        
        # Detailed Borough Status Table
        st.subheader("🏛️ Detailed Borough Status")
        
        if status.get('boroughs'):
            borough_data = []
            for borough, info in status['boroughs'].items():
                status_emoji = {
                    'running': '🔄',
                    'completed': '✅', 
                    'error': '❌',
                    'initialized': '⏸️'
                }.get(info.get('status', 'unknown'), '❓')
                
                borough_data.append({
                    'Borough': borough,
                    'Status': f"{status_emoji} {info.get('status', 'Unknown').title()}",
                    'Last Run': info.get('last_run', 'Never'),
                    'Apps Found': info.get('applications_found', 0),
                    'Last Error': info.get('last_error', 'None')[:50] + ('...' if len(str(info.get('last_error', ''))) > 50 else '')
                })
            
            status_df = pd.DataFrame(borough_data)
            st.dataframe(
                status_df, 
                use_container_width=True,
                column_config={
                    'Borough': st.column_config.TextColumn('Borough', width='medium'),
                    'Status': st.column_config.TextColumn('Status', width='medium'),
                    'Last Run': st.column_config.TextColumn('Last Run', width='medium'),
                    'Apps Found': st.column_config.NumberColumn('Apps Found', width='small'),
                    'Last Error': st.column_config.TextColumn('Last Error', width='large')
                }
            )
        else:
            st.info("No borough status available. Click 'Reset' to initialize scrapers.")
    
    except Exception as e:
        st.error(f"Error loading scraping status: {e}")
        logger.error(f"Scraping control page error: {e}")

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