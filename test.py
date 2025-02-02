import pandas_market_calendars as mcal
from datetime import datetime, timedelta

nyse = mcal.get_calendar('NYSE')
end_date = datetime.now()
start_date = end_date - timedelta(days=10)
valid_days = nyse.valid_days(start_date=start_date, end_date=end_date)

print(valid_days[-1])