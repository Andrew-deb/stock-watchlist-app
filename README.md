# Stock Watchlist App

A modern stock watchlist application built with Flask and Databricks Lakebase (Postgres).

## Features

- 📈 Add stocks to your personal watchlist
- 💰 Real-time stock price tracking via Massive API
- 🗑️ Delete stocks from watchlist
- 🔍 Search and filter stocks
- 📊 Sortable columns
- 📱 Responsive design
- 📈 Statistics dashboard

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: Databricks Lakebase (Managed Postgres)
- **API**: Massive Stock Market API
- **Deployment**: Databricks Apps

## Setup

1. Configure secrets in Databricks:
   - `lakebase-url`: Your Lakebase connection URL
   - `api-key`: Your Massive API key

2. Deploy using Databricks Apps CLI:
   ```bash
   databricks apps deploy stock-watchlist-app
   ```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export LAKEBASE_URL="your-lakebase-url"
export MASSIVE_API_KEY="your-api-key"

# Run the app
python app.py
```

## License

MIT License - Feel free to use and modify
