# 🏗️ London Planning Application Monitor

## 🌐 Live Demo on Streamlit Cloud

This application monitors planning applications across London boroughs for environmental monitoring requirements.

### 📊 Features
- **Interactive Dashboard** with charts and metrics
- **Data Explorer** with filtering capabilities
- **Real Westminster Data** including Palace of Westminster and Lords Cricket Ground
- **Environmental Monitoring** keywords detection

### 🚀 Streamlit Cloud Deployment

**Current Status**: Cloud-ready with sample data

**Requirements**: 
- streamlit>=1.28.0
- pandas>=1.3.0
- plotly>=5.0.0

**Sample Applications Include**:
- Palace of Westminster structural monitoring (25/03344/LBC)
- Lords Cricket Ground monitoring strategy (25/02299/ADFULL)
- Berkeley Square noise monitoring (17/08991/ADFULL)
- Environmental monitoring installations

### 🔧 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_app.py
```

### 📈 Production System

The full production system includes:
- Westminster borough scraper (operational)
- Anti-bot protection bypass
- SQLite database integration
- Real-time scraping capabilities
- 29 monitoring applications extracted

For production deployment, see the local system files.

## 🎯 Overview

This application automatically scrapes planning applications from London borough portals to identify projects that mention:
- Remote monitoring
- Noise monitoring
- Vibration monitoring
- Dust monitoring
- Subsidence monitoring

## 🏛️ Supported Boroughs

- **Camden** - camdenpas.camden.gov.uk
- **Westminster** - idoxpa.westminster.gov.uk
- **Hammersmith & Fulham** - public-access.lbhf.gov.uk
- **Tower Hamlets** - development.towerhamlets.gov.uk
- **Southwark** - planning.southwark.gov.uk

## 🚀 Features

- **Automated Web Scraping**: Uses requests/BeautifulSoup and Selenium for different portal types
- **Polite Scraping**: Implements rate limiting, respects robots.txt, and handles errors gracefully
- **SQLite Database**: Structured storage with duplicate prevention
- **Streamlit Dashboard**: Beautiful web interface for viewing and filtering results
- **Export Functionality**: CSV and Excel export capabilities
- **Keyword Detection**: Intelligent detection of monitoring requirements in application texts
- **Concurrent Processing**: Multi-threaded scraping for efficiency
- **Comprehensive Logging**: Detailed logging and error tracking

## 📋 Requirements

- Python 3.8+
- Chrome/Chromium browser (for Selenium)
- Internet connection

## 🚀 Getting Started

### Quick Setup
```bash
# Clone the repository
git clone https://github.com/Raygunadk2002/planning-scraper.git
cd planning-scraper

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run streamlit_app.py
```

### Viewing Scraper Outputs

The application provides **ultra-granular real-time monitoring** with several ways to see exactly what the scrapers are doing:

#### 1. **Live Activity Monitoring** 📊
- Visit the **"🔍 Live Scraping Activity"** page in the Streamlit app
- See real-time logs with millisecond timestamps
- Track which URLs are being accessed
- Monitor HTTP requests, response parsing, and data processing
- Auto-refreshes every 2 seconds for live updates

#### 2. **Borough Progress Tracking** 🎯
- Real-time progress bars for each borough
- Current keyword being searched
- Completion status and timing
- Request counters and processing metrics

#### 3. **Database Results** 📈
- View found applications in the **"📊 Data Dashboard"** page
- Export results to CSV/Excel
- Filter by borough, keywords, and dates
- Statistics and analytics

#### 4. **Command Line Testing** 🔬
```bash
# Test individual scrapers
python3 test_scraping.py

# View detailed logs
python3 -c "
from scraper_manager import ScrapingManager
manager = ScrapingManager()
result = manager.scrape_single_borough('Westminster', ['extension'])
print(result)
"
```

### ⚠️ Current Status: Anti-Bot Protection

**Planning portals currently block automated searches** with HTTP 403 (Forbidden) responses due to:
- CAPTCHA protection
- Bot detection algorithms  
- Rate limiting systems

**Solutions:**
1. **Manual verification** may be required for first-time access
2. **Browser automation** (Selenium) can potentially bypass some protections
3. **API access** from council developers would be ideal
4. **Scheduled runs** during off-peak hours may have better success

The system provides **full visibility** into the scraping process, so you can see exactly:
- Which URLs are being accessed
- HTTP response codes (200 success, 403 blocked, etc.)
- Processing steps and timing
- Any errors or issues

This transparency makes debugging and optimization much easier!

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd planning-scraper
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```bash
   python -c "import streamlit, requests, selenium; print('All dependencies installed successfully!')"
   ```

## 🎮 Usage

### Running the Streamlit Dashboard

1. **Start the application**:
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Open your browser** to `http://localhost:8501`

3. **Navigate through the interface**:
   - **Dashboard**: View overview statistics and charts
   - **Data Explorer**: Filter and examine detailed results
   - **Scraping Control**: Manually trigger scraping operations
   - **Export Data**: Download results in CSV or Excel format
   - **Settings**: View configuration and manage resources

### Command Line Usage

**Scrape all boroughs**:
```bash
python scraper_manager.py
```

**Scrape specific borough**:
```bash
python scraper_manager.py Camden
```

**Database operations**:
```bash
python database.py  # Initialize database
```

## 📊 Dashboard Features

### Dashboard Overview
- Total applications found
- Borough coverage statistics
- Keyword detection summary
- Recent scraping activity
- Interactive charts and visualizations

### Data Explorer
- Filter by borough, keyword, and date range
- Detailed application view
- Interactive data tables
- Direct links to original applications

### Scraping Control
- Manual scraping triggers
- Real-time status monitoring
- Borough-specific operations
- Custom keyword searches

### Export Options
- CSV format for data analysis
- Excel format with formatting
- Filtered exports based on criteria
- Direct download from browser

## 🗄️ Database Schema

### planning_applications
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| project_id | TEXT | Borough's application reference |
| borough | TEXT | Borough name |
| title | TEXT | Application title/description |
| address | TEXT | Development address |
| submission_date | TEXT | Application submission date |
| application_url | TEXT | Link to full application |
| detected_keywords | TEXT | Comma-separated keywords found |
| scraped_timestamp | TEXT | When data was scraped |
| source_url | TEXT | Original search URL |
| status | TEXT | Record status |

### scraping_logs
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| borough | TEXT | Borough name |
| scrape_timestamp | TEXT | When scraping occurred |
| records_found | INTEGER | Total records found |
| records_new | INTEGER | New records added |
| status | TEXT | Scraping status |
| error_message | TEXT | Error details if any |

## ⚙️ Configuration

### Key Configuration Files

- **`config.py`**: Main configuration including URLs, keywords, and settings
- **`requirements.txt`**: Python dependencies
- **Database**: SQLite file (`planning_applications.db`) created automatically

### Customizing Keywords

Edit `MONITORING_KEYWORDS` in `config.py`:
```python
MONITORING_KEYWORDS = [
    "your custom keyword",
    "another keyword",
    # ... add more as needed
]
```

### Adjusting Scraping Behavior

Modify `SCRAPING_CONFIG` in `config.py`:
```python
SCRAPING_CONFIG = {
    "request_delay": 2.0,  # Delay between requests
    "timeout": 30,         # Request timeout
    "max_retries": 3,      # Retry attempts
    "max_pages_per_borough": 10,  # Limit per borough
    # ... other settings
}
```

## 🤖 Architecture

### Core Components

1. **Scrapers (`scrapers.py`)**:
   - `IdoxScraper`: For Idox-based portals (Camden, Westminster, H&F, Tower Hamlets)
   - `SouthwarkScraper`: Specialized for Southwark portal
   - `SeleniumScraper`: JavaScript-heavy sites fallback

2. **Database (`database.py`)**:
   - SQLite operations
   - Data validation and cleaning
   - Export functionality

3. **Utils (`utils.py`)**:
   - Rate limiting and robots.txt compliance
   - Text processing and keyword detection
   - Data validation utilities

4. **Manager (`scraper_manager.py`)**:
   - Coordinates multi-borough scraping
   - Threading and concurrent operations
   - Status tracking and logging

5. **Frontend (`streamlit_app.py`)**:
   - Web dashboard interface
   - Interactive data visualization
   - Export and control features

### Data Flow

```
Borough Portals → Scrapers → Data Validation → SQLite Database → Streamlit Dashboard
                                     ↓
                              Error Handling & Logging
```

## 🔧 Troubleshooting

### Common Issues

**1. Chrome/Selenium Issues**:
```bash
# Install Chrome if missing
sudo apt-get install google-chrome-stable  # Ubuntu/Debian
brew install --cask google-chrome          # macOS
```

**2. Database Permissions**:
```bash
# Ensure write permissions in project directory
chmod 755 .
```

**3. Network/Firewall Issues**:
- Check internet connection
- Verify access to borough websites
- Consider proxy settings if needed

**4. Memory Issues**:
- Reduce `max_pages_per_borough` in config
- Lower `max_workers` in concurrent operations

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance Optimization

### Recommendations

1. **Rate Limiting**: Adjust `request_delay` based on server response
2. **Concurrent Workers**: Tune `max_workers` for your system
3. **Page Limits**: Set reasonable `max_pages_per_borough` limits
4. **Database Indexing**: Indexes are created automatically for common queries
5. **Caching**: Consider implementing caching for repeated requests

## 🔒 Ethics & Compliance

### Responsible Scraping

- **Rate Limiting**: Built-in delays between requests
- **Robots.txt**: Automatic compliance checking
- **Error Handling**: Graceful failure and retry logic
- **Data Attribution**: Source URLs and timestamps included
- **Terms Compliance**: Designed to respect portal terms of service

### Data Usage Guidelines

- Use scraped data responsibly and in accordance with terms
- Include proper attribution when sharing or publishing data
- Consider reaching out to boroughs for official data APIs where available
- Regularly review and update scraping practices

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style

- Follow PEP 8 conventions
- Add type hints where appropriate
- Include docstrings for functions and classes
- Maintain comprehensive error handling

## 📝 License

This project is provided for educational and research purposes. Please ensure compliance with individual borough terms of service and applicable data protection regulations.

## 📞 Support

For issues, questions, or contributions:
1. Check existing issues in the repository
2. Create a new issue with detailed description
3. Include system information and error logs
4. Suggest improvements or enhancements

## 🔄 Version History

- **v1.0.0**: Initial release with full functionality
  - Multi-borough scraping support
  - Streamlit dashboard
  - SQLite database storage
  - Export capabilities
  - Comprehensive error handling

---

**Note**: This application is designed for monitoring public planning applications. Always respect website terms of service and implement appropriate rate limiting to avoid overwhelming server resources. 