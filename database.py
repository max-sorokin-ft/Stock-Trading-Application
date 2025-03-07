# database.py
# Handles all database operations including setup, updates, and queries

import sqlite3
from datetime import datetime, timedelta
from stock_data import process_current_stock_data, get_stock_data, process_intraday_price_history
from apscheduler.schedulers.background import BackgroundScheduler 
from time import sleep, time
import pandas_market_calendars as mcal

def create_connection():
    """Create a connection to the SQLite database"""
    try:
        connection = sqlite3.connect('portfolio.db')
        cursor = connection.cursor()
        return connection, cursor
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None, None

def create_tables():
    """Create all necessary database tables if they don't exist"""
    connection, cursor = create_connection()
    
    # Price history table - stores every price update
    # Columns: id, stock_symbol, price, timestamp
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS price_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_symbol TEXT NOT NULL,
        price REAL NOT NULL,
        timestamp TEXT NOT NULL,
        UNIQUE(stock_symbol, timestamp)
    )
    ''')
    
    # Current stock data table - stores latest info for each stock
    # Columns: stock_symbol, current_price, open_price, high_price, low_price,
    #          volume, daily_change, last_updated
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stocks_current(
        stock_symbol TEXT PRIMARY KEY,
        open_price REAL NOT NULL,
        high_price REAL NOT NULL,
        low_price REAL NOT NULL,
        price REAL NOT NULL,
        volume INTEGER NOT NULL,
        latest_trading_day TEXT NOT NULL,
        previous_close REAL NOT NULL,
        change REAL NOT NULL,
        change_percent REAL NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS portfolios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        stock_symbol TEXT NOT NULL,
        shares INTEGER NOT NULL,
        average_price REAL NOT NULL,
        UNIQUE(user_id, stock_symbol)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        stock_symbol TEXT NOT NULL,
        transaction_type TEXT CHECK(transaction_type IN ('BUY', 'SELL')) NOT NULL,
        shares INTEGER NOT NULL,
        price_per_share REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Users table - stores user account information
    # Columns: id, username, password_hash, email, created_at
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    connection.commit()
    connection.close()

def clear_price_history():
    """Clear all data from the price_history table"""
    connection, cursor = create_connection()
    try:
        cursor.execute('DELETE FROM price_history')
        connection.commit()
        print("Successfully cleared price_history table")
    except Exception as e:
        print(f"Error clearing data: {e}")
    finally:
        connection.close()

def update_current_stock_data(stock_symbols):
    """
    Update current stock information for specified symbols
    
    Args:
        stock_symbols: List of stock ticker symbols to update
    """
    try:
        connection, cursor = create_connection()

        for symbol in stock_symbols:
            quote_data, symbol = get_stock_data(symbol, daily_data_needed=False, intraday_data_needed=False)
            
            if not quote_data:
                continue
            
            processed_data = process_current_stock_data(quote_data, symbol)

            if not processed_data:
                continue
            
            # Update stocks_current table with latest data
            cursor.execute('''
                INSERT OR REPLACE INTO stocks_current 
                (stock_symbol, open_price, high_price, low_price, price,
                volume, latest_trading_day, previous_close, change, change_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                processed_data['stock_symbol'],
                processed_data['open_price'],
                processed_data['high_price'],
                processed_data['low_price'],
                processed_data['price'],
                processed_data['volume'],
                processed_data['latest_timestamp'],
                processed_data['previous_close'],
                processed_data['change'],
                processed_data['change_percent']
            ))
            connection.commit()
    
    except Exception as e:
        print(f"Error updating stock data: {e}")
    finally:
        connection.close()

def update_intraday_price_history(stock_symbols, month):
    """
    Update intraday price history for specified symbols and month
    
    Args:
        stock_symbols: List of stock ticker symbols to update
        month: Month to update in format 'YYYY-MM'
    """
    try:
        connection, cursor = create_connection()

        for symbol in stock_symbols:
            intraday_data, symbol = get_stock_data(symbol, month, daily_data_needed=False, current_data_needed=False)

            if not intraday_data:
                print(f"Skipping {symbol} - no data available")
                continue
            
            timestamps = list(intraday_data['Time Series (1min)'].keys())  

            for timestamp in timestamps:
                processed_data = process_intraday_price_history(intraday_data, symbol, timestamp)

                cursor.execute('''
                INSERT OR REPLACE INTO price_history
                    (stock_symbol, price, timestamp)
                    VALUES  (?, ?, ?)
                ''', (
                    processed_data['stock_symbol'],
                    processed_data['close_price'],
                    processed_data['timestamp']
                ))
                
        connection.commit()
    except Exception as e:
        print(f"Error updating intraday data: {e}")
    finally:
        connection.close()

def update_current_month_data(stock_symbols):
    """Update price history for current month for specified symbols"""
    nyse = mcal.get_calendar('NYSE')
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10)
    valid_days = nyse.valid_days(start_date=start_date, end_date=end_date)
    current_month = valid_days[-1].strftime('%Y-%m')
    update_intraday_price_history(stock_symbols, current_month)

if __name__ == "__main__":
    # Test stock symbols
    test_symbols = ['TSLA', 'AAPL', 'IBM', 'MSFT']
    
    # Initial update
    print("\nInitial stock update:")
    update_current_stock_data(test_symbols)
    
    # Verify initial data
    connection, cursor = create_connection()
    for symbol in test_symbols:
        cursor.execute('SELECT * FROM stocks_current WHERE stock_symbol = ?', (symbol,))
        print(cursor.fetchone())
    connection.close()
    
    def update_stocks():
        print("\nScheduled update:")
        update_current_stock_data(test_symbols)
        
        connection, cursor = create_connection()
        for symbol in test_symbols:
            cursor.execute('SELECT * FROM stocks_current WHERE stock_symbol = ?', (symbol,))
            print(cursor.fetchone())
        connection.close()
    
    # Set up scheduler for periodic updates
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_stocks, trigger="interval", seconds=60, misfire_grace_time=60)
    
    print("\nScheduler started - you should see new data every 60 seconds")
    scheduler.start()
    
    while True:
        pass

        
    
  




