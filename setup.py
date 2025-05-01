# setup.py
# Handles initial database setup and historical data population

import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler 
from time import sleep, time
from stock_data import get_stock_data, process_daily_price_history, process_intraday_price_history
from database import create_connection, update_intraday_price_history, clear_price_history, create_tables, update_current_month_data
from datetime import datetime, timedelta
import pandas_market_calendars as mcal
import pandas as pd

def update_daily_price_history(stock_symbols):
    """
    Update daily price history for all specified stock symbols
    
    Args:
        stock_symbols: List of stock symbols to update
    """
    try:
        connection, cursor = create_connection()

        for symbol in stock_symbols:
            # Get daily data from API
            daily_data, symbol = get_stock_data(symbol, intraday_data_needed=False, current_data_needed=False)

            if not daily_data:
                print(f"Skipping {symbol} - no data available")
                continue
            
            # Process each trading day
            trading_days = list(daily_data['Time Series (Daily)'].keys())
            for date in trading_days:
                processed_data = process_daily_price_history(daily_data, symbol, date)

                # Store closing prices in price_history table
                cursor.execute('''
                INSERT OR IGNORE INTO price_history
                    (stock_symbol, price, timestamp)
                    VALUES  (?, ?, ?)
                ''', (
                    processed_data['stock_symbol'],
                    processed_data['close_price'],
                    processed_data['timestamp']
                ))
                
        connection.commit()
    except Exception as e:
        print(f"Error setting up stock data for {symbol}: {e}")
    finally:
        connection.close()

def get_last_12_months():
    """
    Generate list of last 12 months in YYYY-MM format
    
    Returns:
        List of month strings in descending order`
    """
    nyse = mcal.get_calendar('NYSE')
    end_date = datetime.now()
    start_date = end_date - timedelta(days=400)
    valid_days = nyse.valid_days(start_date=start_date, end_date=end_date)
    
    months = []
    for day in valid_days:
        month = day.strftime('%Y-%m')
        months.append(month)
    
    unique_months = list(set(months))
    
    return unique_months

if __name__ == "__main__":
    create_tables()
    # List of stocks to track
    stock_symbols = ['TSLA', 'AAPL', 'NVDA', 'MSFT', 'WMT']

    # Update daily historical data
    update_daily_price_history(stock_symbols)

    # Update intraday data for last 12 months
    months = get_last_12_months()
    for month in months:
        update_intraday_price_history(stock_symbols, month)

    # Print data coverage summary
    connection, cursor = create_connection()
    for symbol in stock_symbols:
        cursor.execute('SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM price_history WHERE stock_symbol = ?', (symbol,))
        start_date, end_date, count = cursor.fetchone()
        print(f"\n{symbol}:")
        print(f"From {start_date} to {end_date}")
        print(f"Total records: {count}")
    connection.close()