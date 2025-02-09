# stock_data.py
# Handles all API interactions and data processing for stock information

import requests
import json
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
from config import API_KEY, BASE_URL
  
# CHANGE: Remove current_data_needed parameter and its related logic
def get_stock_data(stock_symbol, month=None, daily_data_needed=True, intraday_data_needed=True, current_data_needed=True):
    """
    Fetch stock data from Alpha Vantage API.
    
    Args:
        stock_symbol: The stock ticker symbol (e.g., 'AAPL')
        month: Optional month for historical data (format: 'YYYY-MM')
        daily_data_needed: Whether to fetch daily price data
        intraday_data_needed: Whether to fetch intraday price data
    
    Returns:
        Tuple containing the requested data and stock symbol
    """
    try:
        # Construct intraday API URL based on whether month is specified
        if month:
            intraday_url = f'{BASE_URL}function=TIME_SERIES_INTRADAY&symbol={stock_symbol}&interval=1min&month={month}&outputsize=full&entitlement=delayed&extended_hours=false&apikey={API_KEY}'
        else:
            intraday_url = f'{BASE_URL}function=TIME_SERIES_INTRADAY&symbol={stock_symbol}&interval=1min&outputsize=full&entitlement=delayed&extended_hours=false&apikey={API_KEY}'

        # Handle different combinations of data requests
        if current_data_needed:
            quote_url = f'{BASE_URL}function=GLOBAL_QUOTE&symbol={stock_symbol}&entitlement=delayed&apikey={API_KEY}'
            quote_response = requests.get(quote_url)
            quote_data = quote_response.json()
            return quote_data, stock_symbol
        
        elif daily_data_needed:
            daily_url = f'{BASE_URL}function=TIME_SERIES_DAILY_ADJUSTED&symbol={stock_symbol}&outputsize=full&apikey={API_KEY}'
            daily_response = requests.get(daily_url)
            daily_data = daily_response.json()

            return daily_data, stock_symbol
        
        elif intraday_data_needed:
            intraday_response = requests.get(intraday_url)
            intraday_data = intraday_response.json()

            return intraday_data, stock_symbol

    except Exception as e:
        print(f"Error getting stock data for {stock_symbol}: {e}")
        return None, stock_symbol
     
def process_current_stock_data(quote_data, stock_symbol):
   """Process raw quote data into current stock information."""
   try:
       quote = quote_data['Global Quote - DATA DELAYED BY 15 MINUTES']

       latest_timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
       current_time = datetime.now().time()

       if current_time < time(9, 30) or current_time > time(16, 0):
           latest_timestamp = f"{quote['07. latest trading day']}  4:00:00 PM"
           
       return {
           'stock_symbol': stock_symbol,
           'open_price': round(float(quote['02. open']), 2),
           'high_price': round(float(quote['03. high']), 2), 
           'low_price': round(float(quote['04. low']), 2),
           'price': round(float(quote['05. price']), 2),
           'volume': int(quote['06. volume']),
           'latest_timestamp': latest_timestamp,
           'previous_close': round(float(quote['08. previous close']), 2),
           'change': round(float(quote['09. change']), 2),
           'change_percent': str(round(float(quote['10. change percent'].strip('%')), 2)) + '%'    
       }
   except Exception as e:
       print(f"Error processing data for {stock_symbol}: {e}")
       return None
   
def process_daily_price_history(daily_data, stock_symbol, date):
    """
    Process raw API data into daily historical prices.
    
    Args:
        daily_data: JSON response from daily API endpoint
        stock_symbol: Stock ticker symbol
        date: Trading date to process
        
    Returns:
        Dictionary containing processed daily price data
    """
    try:
        time_series = daily_data['Time Series (Daily)']
        
        return {
            'stock_symbol': stock_symbol,
            'close_price': round(float(time_series[date]['5. adjusted close']), 2),
            'open_price': round(float(time_series[date]['1. open']), 2),
            'high_price': round(float(time_series[date]['2. high']), 2),
            'low_price': round(float(time_series[date]['3. low']), 2),
            'volume': int(time_series[date]['6. volume']),
            'timestamp': date + " 16:00:00",  # Market close time
        }

    except Exception as e:
        print(f"Error processing data for {stock_symbol}: {e}")
        return None

def process_intraday_price_history(intraday_data, stock_symbol, timestamp):
    """
    Process raw API data into intraday historical prices.
    
    Args:
        intraday_data: JSON response from intraday API endpoint
        stock_symbol: Stock ticker symbol
        timestamp: Specific timestamp to process
        
    Returns:
        Dictionary containing processed intraday price data
    """
    try:
        time_series = intraday_data['Time Series (1min)']
        
        return {
            'stock_symbol': stock_symbol,
            'close_price': round(float(time_series[timestamp]['4. close']), 2),
            'open_price': round(float(time_series[timestamp]['1. open']), 2),
            'high_price': round(float(time_series[timestamp]['2. high']), 2),
            'low_price': round(float(time_series[timestamp]['3. low']), 2),
            'volume': int(time_series[timestamp]['5. volume']),
            'timestamp': timestamp
        }

    except Exception as e:
        print(f"Error processing data for {stock_symbol}: {e}")
        return None

if __name__ == "__main__":
    pass




