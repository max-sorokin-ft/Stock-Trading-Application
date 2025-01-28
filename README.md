# Stock Market Analytics Platform

## Overview
A real-time stock market tracking application built with Flask that provides live stock price monitoring, interactive charts, and historical data analysis. The application uses the Alpha Vantage API for market data and features an intuitive interface for viewing stock information across different time periods.

## Features
- **Real-time Price Tracking**: Live updates of stock prices during market hours
- **Interactive Charts**: Dynamic price charts with multiple timeframes:
  - 1 Day (1-minute intervals)
  - 1 Week (5-minute intervals)
  - 1 Month (15-minute intervals)
  - 3 Months (30-minute intervals)
  - 6 Months (60-minute intervals)
  - 1 Year (4-hour intervals)
  - 5 Years (daily intervals)
- **Market Hours Awareness**: Automatically adjusts displays for market hours (9:30 AM - 4:00 PM EST)
- **Automated Updates**: Background data refresh every minute
- **Local Data Storage**: SQLite database for efficient data management

## Coming Soon
- User authentication system
- Portfolio tracking
- Transaction history
- Candlestick charts
- Performance analytics

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stock-analytics.git
cd stock-analytics
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Unix/MacOS
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create a config.py file in the root directory:
```python
API_KEY = 'your_alpha_vantage_api_key'
BASE_URL = 'https://www.alphavantage.co/query?'
```

5. Initialize the database:
```bash
python setup.py
```

6. Start the application:
```bash
python app.py
```

7. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Enter a stock symbol in the search bar (e.g., AAPL for Apple)
2. View the interactive price chart
3. Use the dropdown menu to change the time period
4. Data automatically updates every minute during market hours

## Project Structure
```
project/
│
├── app.py              # Main Flask application
├── database.py         # Database operations
├── stock_data.py       # Stock data processing
├── setup.py           # Initial setup script
├── requirements.txt   # Dependencies
├── portfolio.db       # SQLite database
│
├── static/
│   └── styles.css     # CSS styles
│
└── templates/
    ├── index.html     # Home page
    └── stock.html     # Stock details page
```

## API Limitations
The free tier of Alpha Vantage API has the following limits:
- 25 API calls per day
- 5 calls per minute
- Potentially 15 min delayed data

Consider upgrading to a paid tier for production use.

## Contributing
Feel free to fork the repository and submit pull requests. For major changes:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## License
This project is under the MIT License - see LICENSE.md for details.