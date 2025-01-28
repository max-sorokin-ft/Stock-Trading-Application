import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler 
from time import sleep, time
from stock_data import get_stock_data, process_daily_price_history, process_intraday_price_history
from database import create_connection, update_intraday_price_history, clear_price_history, create_tables
from datetime import datetime, timedelta

def update_daily_price_history(stock_symbols):
  try:
    connection, cursor =  create_connection()

    for stock_symbol in stock_symbols:
      daily_data, stock_symbol = get_stock_data(stock_symbol, intraday_data_needed = False)

      if not daily_data:
         print(f"Skipping {stock_symbol} - no data available")
         continue
      
      trading_days = list(daily_data['Time Series (Daily)'].keys())

      for date in trading_days:
        processed_daily_price_history = process_daily_price_history(daily_data, stock_symbol, date)

        cursor.execute('''
        INSERT OR IGNORE INTO price_history
            (stock_symbol, price, timestamp)
            VALUES  (?, ?, ?)
          ''', (
              processed_daily_price_history['stock_symbol'],
              processed_daily_price_history['close_price'],
              processed_daily_price_history['timestamp']
          ))
        
    connection.commit()
  except Exception as e:
       print(f"Error setting up stock data for {stock_symbol}: {e}")
  finally:
     connection.close()

## Helper
def get_last_12_months():
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
   # clear_price_history()
  stock_symbols = ['TSLA', 'AAPL', 'NVDA', 'MSFT', 'WMT']

  update_daily_price_history(stock_symbols)

  months = get_last_12_months()

  for month in months:
     update_intraday_price_history(stock_symbols, month)

  stock_symbols = ['TSLA', 'AAPL', 'NVDA', 'MSFT', 'WMT']
  connection, cursor = create_connection()
  for symbol in stock_symbols:
      cursor.execute('SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM price_history WHERE stock_symbol = ?', (symbol,))
      start_date, end_date, count = cursor.fetchone()
      print(f"\n{symbol}:")
      print(f"From {start_date} to {end_date}")
      print(f"Total records: {count}")
  connection.close()