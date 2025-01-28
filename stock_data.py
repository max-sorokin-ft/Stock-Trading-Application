import requests
import json
from apscheduler.schedulers.background import BackgroundScheduler
from config import API_KEY, BASE_URL
  
def get_stock_data(stock_symbol, month = None, daily_data_needed = True, intraday_data_needed = True):
  try:
    if month:
       intraday_url = f'{BASE_URL}function=TIME_SERIES_INTRADAY&symbol={stock_symbol}&interval=1min&month={month}&outputsize=full&entitlement=delayed&extended_hours=false&apikey={API_KEY}'
    else:
       intraday_url = f'{BASE_URL}function=TIME_SERIES_INTRADAY&symbol={stock_symbol}&interval=1min&outputsize=full&entitlement=delayed&extended_hours=false&apikey={API_KEY}'

    if daily_data_needed and intraday_data_needed:
      daily_url = f'{BASE_URL}function=TIME_SERIES_DAILY_ADJUSTED&symbol={stock_symbol}&outputsize=full&apikey={API_KEY}'
      daily_data_request = requests.get(daily_url)
      daily_data = daily_data_request.json()

      intraday_data_request = requests.get(intraday_url)
      intraday_data = intraday_data_request.json()

      return daily_data, intraday_data, stock_symbol
    elif daily_data_needed and not intraday_data_needed:
      daily_url = f'{BASE_URL}function=TIME_SERIES_DAILY_ADJUSTED&symbol={stock_symbol}&outputsize=full&apikey={API_KEY}'
      daily_data_request = requests.get(daily_url)
      daily_data = daily_data_request.json()

      return daily_data, stock_symbol
    elif intraday_data_needed and not daily_data_needed:
      intraday_data_request = requests.get(intraday_url)
      intraday_data = intraday_data_request.json()

      return intraday_data, stock_symbol
  except Exception as e:
     print(f"Error getting stock data for {stock_symbol}: {e}")
     if daily_data_needed and intraday_data_needed:
        return None, None, stock_symbol
     else:
        return None, stock_symbol
     
  
def process_current_stock_data(daily_data, intraday_data, stock_symbol):
   try:
       current_market_day = daily_data['Meta Data']['3. Last Refreshed'] 
       current_day_values = daily_data['Time Series (Daily)'][current_market_day]

       trading_days = list(daily_data['Time Series (Daily)'].keys())
       previous_market_day = trading_days[1]
       previous_day_values = daily_data['Time Series (Daily)'][previous_market_day]

       market_timestamps = list(intraday_data['Time Series (1min)'].keys())
       most_recent_timestamp = market_timestamps[0]
       intraday_values = intraday_data['Time Series (1min)'][most_recent_timestamp]

       processed_current_stock_data = {
           'stock_symbol': stock_symbol,
           'current_price': round(float(intraday_values['4. close']), 2),
           'open_price': round(float(current_day_values['1. open']), 2), 
           'high_price': round(float(current_day_values['2. high']), 2),
           'low_price': round(float(current_day_values['3. low']), 2),
           'volume': int(current_day_values['6. volume']),
           'daily_change': round(float(intraday_values['4. close']) - float(previous_day_values['5. adjusted close']), 2),
           'last_updated': most_recent_timestamp
       }

       return processed_current_stock_data

   except Exception as e:
       print(f"Error processing data for {stock_symbol}: {e}")
       return None
   
def process_daily_price_history(daily_data, stock_symbol, date):
   try:
       time_daily_series = daily_data['Time Series (Daily)']
       
       processed_daily_price_history = {
           'stock_symbol': stock_symbol,
           'close_price': round(float(time_daily_series[date]['5. adjusted close']), 2),
           'open_price': round(float(time_daily_series[date]['1. open']), 2),
           'high_price': round(float(time_daily_series[date]['2. high']), 2),
           'low_price': round(float(time_daily_series[date]['3. low']), 2),
           'volume': int(time_daily_series[date]['6. volume']),
           'timestamp': date + " 16:00:00",
       }

       return processed_daily_price_history
   except Exception as e:
       print(f"Error processing data for {stock_symbol}: {e}")
       return None

def process_intraday_price_history(intraday_data, stock_symbol, timestamp):
    try:
       time_intraday_series = intraday_data['Time Series (1min)']
       
       processed_intraday_price_history = {
           'stock_symbol': stock_symbol,
           'close_price': round(float(time_intraday_series[timestamp]['4. close']), 2),
           'open_price': round(float(time_intraday_series[timestamp]['1. open']), 2),
           'high_price': round(float(time_intraday_series[timestamp]['2. high']), 2),
           'low_price': round(float(time_intraday_series[timestamp]['3. low']), 2),
           'volume': int(time_intraday_series[timestamp]['5. volume']),
           'timestamp': timestamp
       }

       return processed_intraday_price_history
    except Exception as e:
       print(f"Error processing data for {stock_symbol}: {e}")
       return None

      
     

  
if __name__ == "__main__":
    pass




