"""
Database management module for Planning Scraper Application
Handles SQLite database operations and schema management
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import pandas as pd

from config import DATABASE_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlanningDatabase:
    """Handles all database operations for planning applications"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DATABASE_CONFIG["db_path"]
        self.init_database()
    
    def init_database(self):
        """Initialize database and create tables if they don't exist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create planning_applications table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS planning_applications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        borough TEXT NOT NULL,
                        title TEXT,
                        address TEXT,
                        submission_date TEXT,
                        application_url TEXT,
                        detected_keywords TEXT,
                        scraped_timestamp TEXT NOT NULL,
                        source_url TEXT,
                        status TEXT DEFAULT 'active',
                        UNIQUE(project_id, borough)
                    )
                """)
                
                # Create scraping_logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scraping_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        borough TEXT NOT NULL,
                        scrape_timestamp TEXT NOT NULL,
                        records_found INTEGER DEFAULT 0,
                        records_new INTEGER DEFAULT 0,
                        status TEXT,
                        error_message TEXT
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_borough_date 
                    ON planning_applications (borough, submission_date)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_keywords 
                    ON planning_applications (detected_keywords)
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def insert_planning_application(self, application_data: Dict) -> bool:
        """Insert a single planning application into the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO planning_applications 
                    (project_id, borough, title, address, submission_date, 
                     application_url, detected_keywords, scraped_timestamp, source_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    application_data.get('project_id'),
                    application_data.get('borough'),
                    application_data.get('title'),
                    application_data.get('address'),
                    application_data.get('submission_date'),
                    application_data.get('application_url'),
                    ', '.join(application_data.get('detected_keywords', [])),
                    datetime.now().isoformat(),
                    application_data.get('source_url')
                ))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Error inserting application: {e}")
            return False
    
    def bulk_insert_applications(self, applications: List[Dict]) -> Tuple[int, int]:
        """Insert multiple planning applications, return (total, new) counts"""
        total_count = len(applications)
        new_count = 0
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for app in applications:
                    cursor.execute("""
                        INSERT OR IGNORE INTO planning_applications 
                        (project_id, borough, title, address, submission_date, 
                         application_url, detected_keywords, scraped_timestamp, source_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        app.get('project_id'),
                        app.get('borough'),
                        app.get('title'),
                        app.get('address'),
                        app.get('submission_date'),
                        app.get('application_url'),
                        ', '.join(app.get('detected_keywords', [])),
                        datetime.now().isoformat(),
                        app.get('source_url')
                    ))
                    
                    if cursor.rowcount > 0:
                        new_count += 1
                
                conn.commit()
                logger.info(f"Bulk insert completed: {new_count} new out of {total_count} total")
                return total_count, new_count
                
        except sqlite3.Error as e:
            logger.error(f"Error in bulk insert: {e}")
            return total_count, 0
    
    def log_scraping_session(self, borough: str, records_found: int, 
                           records_new: int, status: str, error_message: str = None):
        """Log scraping session results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO scraping_logs 
                    (borough, scrape_timestamp, records_found, records_new, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    borough,
                    datetime.now().isoformat(),
                    records_found,
                    records_new,
                    status,
                    error_message
                ))
                
                conn.commit()
                
        except sqlite3.Error as e:
            logger.error(f"Error logging scraping session: {e}")
    
    def get_applications(self, borough: str = None, keyword: str = None, 
                        date_from: str = None, date_to: str = None) -> pd.DataFrame:
        """Retrieve planning applications with optional filters"""
        try:
            with self.get_connection() as conn:
                query = "SELECT * FROM planning_applications WHERE 1=1"
                params = []
                
                if borough:
                    query += " AND borough = ?"
                    params.append(borough)
                
                if keyword:
                    query += " AND detected_keywords LIKE ?"
                    params.append(f"%{keyword}%")
                
                if date_from:
                    query += " AND submission_date >= ?"
                    params.append(date_from)
                
                if date_to:
                    query += " AND submission_date <= ?"
                    params.append(date_to)
                
                query += " ORDER BY submission_date DESC"
                
                return pd.read_sql_query(query, conn, params=params)
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving applications: {e}")
            return pd.DataFrame()
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total applications
                cursor.execute("SELECT COUNT(*) FROM planning_applications")
                total_apps = cursor.fetchone()[0]
                
                # Applications by borough
                cursor.execute("""
                    SELECT borough, COUNT(*) 
                    FROM planning_applications 
                    GROUP BY borough
                """)
                by_borough = dict(cursor.fetchall())
                
                # Applications by keyword
                keyword_stats = {}
                from config import MONITORING_KEYWORDS
                for keyword in MONITORING_KEYWORDS:
                    cursor.execute("""
                        SELECT COUNT(*) FROM planning_applications 
                        WHERE detected_keywords LIKE ?
                    """, (f"%{keyword}%",))
                    keyword_stats[keyword] = cursor.fetchone()[0]
                
                # Recent scraping activity
                cursor.execute("""
                    SELECT borough, MAX(scrape_timestamp) as last_scrape
                    FROM scraping_logs 
                    GROUP BY borough
                """)
                last_scrapes = dict(cursor.fetchall())
                
                return {
                    'total_applications': total_apps,
                    'by_borough': by_borough,
                    'by_keyword': keyword_stats,
                    'last_scrapes': last_scrapes
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def export_to_csv(self, filename: str, borough: str = None, 
                     keyword: str = None) -> bool:
        """Export data to CSV file"""
        try:
            df = self.get_applications(borough=borough, keyword=keyword)
            df.to_csv(filename, index=False)
            logger.info(f"Data exported to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def export_to_excel(self, filename: str, borough: str = None, 
                       keyword: str = None) -> bool:
        """Export data to Excel file"""
        try:
            df = self.get_applications(borough=borough, keyword=keyword)
            df.to_excel(filename, index=False, engine='openpyxl')
            logger.info(f"Data exported to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False 