# setup.py
# Handles initial database setup and historical data population

import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler 
from time import sleep, time
from stock_data import get_stock_data, process_daily_price_history, process_intraday_price_history
from database import create_connection, update_intraday_price_history, clear_price_history, create_tables
from datetime import datetime, timedelta

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
            daily_data, symbol = get_stock_data(symbol, intraday_data_needed=False)

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
        List of month strings in descending order
    """
    current_date = datetime.now()
    months = []
    
    for i in range(12):
        # Subtract i months from current date
        date = current_date - timedelta(days=30*i)
        # Format as YYYY-MM
        month_str = date.strftime('%Y-%m')
        months.append(month_str)
    
    return months

if __name__ == "__main__":
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