import requests
from config import API_KEY, BASE_URL
from datetime import datetime

def check_time_values():
   symbol = 'NVDA'
   intraday_url = f'{BASE_URL}function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=1min&outputsize=full&entitlement=delayed&extended_hours=false&apikey={API_KEY}'
   
   try:
       response = requests.get(intraday_url)
       data = response.json()
       time_series = data['Time Series (1min)']
       
       # Today's date
       today = datetime.now().strftime('%Y-%m-%d')
       target_time = f"{today} 10:54:00"
       
       if target_time in time_series:
           values = time_series[target_time]
           print(f"\nValues at {target_time} for {symbol}:")
           print(f"Open: ${values['1. open']}")
           print(f"High: ${values['2. high']}")
           print(f"Low: ${values['3. low']}")
           print(f"Close: ${values['4. close']}")
           print(f"Volume: {values['5. volume']}")
       else:
           print(f"No data found for {target_time}")
           
   except Exception as e:
       print(f"Error: {e}")

if __name__ == "__main__":
   check_time_values()