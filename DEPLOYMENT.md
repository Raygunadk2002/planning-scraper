# Deployment Guide

## Cloud Deployment (Streamlit Cloud, Heroku, etc.)

### Option 1: Basic Deployment (No Selenium)

For initial deployment without Selenium functionality:

1. Use `requirements-basic.txt` instead of `requirements.txt`:
   ```bash
   mv requirements.txt requirements-full.txt
   mv requirements-basic.txt requirements.txt
   ```

2. Deploy to your platform. The app will work with all scrapers except those requiring JavaScript rendering.

### Option 2: Full Deployment (With Selenium)

For full functionality including Selenium:

1. Ensure these files are present:
   - `requirements.txt` (full version)
   - `packages.txt` (system dependencies)
   - `runtime.txt` (Python version)

2. The app will automatically detect if Selenium is available and gracefully degrade if not.

### Platform-Specific Instructions

#### Streamlit Cloud
- Fork the repository
- Connect to Streamlit Cloud
- Deploy with default settings
- The `packages.txt` will automatically install Chrome

#### Heroku
Add this to your `Procfile`:
```
web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
```

Add buildpacks:
```bash
heroku buildpacks:add heroku/python
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-google-chrome
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-chromedriver
```

#### Docker
Use the provided Dockerfile (if created) or create one:

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Troubleshooting

#### Dependency Installation Errors

1. **lxml issues**: Sometimes lxml requires system libraries
   - Add to `packages.txt`: `libxml2-dev libxslt1-dev`

2. **Selenium issues**: Chrome/driver not found
   - Ensure `packages.txt` includes chromium packages
   - Check if system Chrome paths are correct in `scrapers.py`

3. **Memory issues**: 
   - Reduce concurrent scraping threads in config
   - Use basic requirements without Selenium initially

#### Runtime Errors

1. **Chrome binary not found**:
   - App will log warning and continue without Selenium
   - Scraping will work for non-JS sites

2. **Database errors**:
   - Check file permissions for SQLite database
   - Ensure writable directory

### Environment Variables

For production, set these environment variables:

```bash
PYTHONPATH=/app
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Performance Optimization

1. **Reduce scraping frequency** in production
2. **Use caching** for repeated queries
3. **Limit concurrent requests** to avoid being blocked
4. **Monitor resource usage** and adjust accordingly

### Security

1. **Rate limiting** is built-in but monitor usage
2. **Respect robots.txt** - enabled by default
3. **Use VPN/proxy** if needed for production scraping
4. **Monitor logs** for blocked requests or issues 