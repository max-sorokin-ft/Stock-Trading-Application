import sqlite3
from datetime import datetime
from stock_data import process_current_stock_data, get_stock_data, process_intraday_price_history
from apscheduler.schedulers.background import BackgroundScheduler 
from time import sleep, time

def create_connection():
  try:
    connection = sqlite3.connect('portfolio.db')
    cursor = connection.cursor()
    return connection, cursor
  except sqlite3.Error as e:
    print(f"Database connection error: {e}")
    return None, None

def create_tables():
    """Create necessary tables if they don't exist"""
    connection, cursor = create_connection()
    
    # Stock price history table - stores every price update
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS price_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_symbol TEXT NOT NULL,
        price REAL NOT NULL,
        timestamp TEXT NOT NULL,
        UNIQUE(stock_symbol, timestamp)
    )
    ''')
    
    # Current stock data table - stores latest info
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stocks_current(
        stock_symbol TEXT PRIMARY KEY,
        current_price REAL NOT NULL,
        open_price REAL NOT NULL,
        high_price REAL NOT NULL,
        low_price REAL NOT NULL,
        volume INTEGER NOT NULL,
        daily_change REAL NOT NULL,
        last_updated TEXT NOT NULL
    )
    ''')
    
    # Transaction history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_symbol TEXT NOT NULL,
        price REAL NOT NULL,
        shares INTEGER NOT NULL,
        transaction_type TEXT CHECK(transaction_type IN ('BUY', 'SELL')) NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY(stock_symbol) REFERENCES stocks_current(stock_symbol)
    )
    ''')

    cursor.execute('''
    CREATE TABLE users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    
    connection.commit()
    connection.close()


def clear_price_history():
    connection, cursor = create_connection()
    try:
        # Delete all price history data
        cursor.execute('DELETE FROM price_history')
        connection.commit()
        print("Successfully cleared price_history table")
    except Exception as e:
        print(f"Error clearing data: {e}")
    finally:
        connection.close()

def update_current_stock_data(stock_symbols):
    try:
      connection, cursor = create_connection()

      for stock_symbol in stock_symbols:
        daily_data, intraday_data, stock_symbol = get_stock_data(stock_symbol)
        
        if not daily_data or not intraday_data:
            return None
        
        processed_current_stock_data = process_current_stock_data(daily_data, intraday_data, stock_symbol)

        if not processed_current_stock_data:
            return None
        
        cursor.execute('''
            INSERT OR REPLACE INTO stocks_current 
            (stock_symbol, current_price, open_price, high_price, low_price,
            volume, daily_change, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            processed_current_stock_data['stock_symbol'],
            processed_current_stock_data['current_price'],
            processed_current_stock_data['open_price'],
            processed_current_stock_data['high_price'],
            processed_current_stock_data['low_price'],
            processed_current_stock_data['volume'],
            processed_current_stock_data['daily_change'],
            processed_current_stock_data['last_updated']
        ))
        connection.commit()
    
    except Exception as e:
       print(f"Error updating stock data for {stock_symbol}: {e}")
    finally:
       connection.close()

def update_intraday_price_history(stock_symbols, month):
  try:
    connection, cursor =  create_connection()

    for stock_symbol in stock_symbols:
      intraday_data, stock_symbol = get_stock_data(stock_symbol, month, daily_data_needed = False)

      if not intraday_data:
         print(f"Skipping {stock_symbol} - no data available")
         continue
      
      intraday_timestamps = list(intraday_data['Time Series (1min)'].keys())  

      for timestamp in intraday_timestamps:
        processed_intraday_price_history = process_intraday_price_history(intraday_data, stock_symbol, timestamp)

        cursor.execute('''
        INSERT OR REPLACE INTO price_history
            (stock_symbol, price, timestamp)
            VALUES  (?, ?, ?)
          ''', (
              processed_intraday_price_history['stock_symbol'],
              processed_intraday_price_history['close_price'],
              processed_intraday_price_history['timestamp']
          ))
        
    connection.commit()
  except Exception as e:
       print(f"Error setting up stock data for {stock_symbol}: {e}")
  finally:
     connection.close()

def update_current_month_data(stock_symbols):
    current_month = datetime.now().strftime('%Y-%m')
    update_intraday_price_history(stock_symbols, current_month)
   

if __name__ == "__main__":
    stock_symbols = ['TSLA', 'AAPL', 'IBM', 'MSFT']
    
    # Initial update
    print("\nInitial stock update:")
    update_current_stock_data(stock_symbols)
    
    # Verify initial data
    connection, cursor = create_connection()
    for symbol in stock_symbols:
        cursor.execute('SELECT * FROM stocks_current WHERE stock_symbol = ?', (symbol,))
        print(cursor.fetchone())
    connection.close()
    
    def update_stocks():
        print("\nScheduled update:")
        update_current_stock_data(stock_symbols)
        
        # Verify updated data
        connection, cursor = create_connection()
        for symbol in stock_symbols:
            cursor.execute('SELECT * FROM stocks_current WHERE stock_symbol = ?', (symbol,))
            print(cursor.fetchone())
        connection.close()
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_stocks, trigger="interval", seconds=60, misfire_grace_time=60)
    
    print("\nScheduler started - you should see new data every 60 seconds")
    scheduler.start()
    
    while True:
        pass

        
    
  




