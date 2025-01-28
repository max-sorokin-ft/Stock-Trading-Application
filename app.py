from flask import Flask, render_template, redirect, request, url_for
from apscheduler.schedulers.background import BackgroundScheduler  
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
import plotly
import plotly.graph_objs as go
import json
from database import create_connection, update_current_stock_data, update_intraday_price_history, update_current_month_data
from setup import update_daily_price_history

# Create Flask app
app = Flask(__name__)   

def get_stock_chart_data(symbol, period):
   connection, cursor = create_connection()
   
   end_date = datetime.now()
   if period == '1week':
       start_date = end_date - timedelta(days=7)
       interval = 5
   elif period == '1day':
       now = datetime.now()
       current_time = now.time()
       market_open = time(9, 30)
       market_close = time(16, 0)
       start_date = end_date - timedelta(days=1)
       interval = 1
       
       if current_time < market_open or current_time > market_close:
           query = '''
               SELECT timestamp, price
               FROM price_history
               WHERE stock_symbol = ?
               AND date(timestamp) = (
                   SELECT date(timestamp) 
                   FROM price_history 
                   WHERE substr(timestamp, 12, 8) >= '09:30:00' AND substr(timestamp, 12, 8) <= '16:00:00'
                   ORDER BY timestamp DESC 
                   LIMIT 1
               )
               AND substr(timestamp, 12, 8) >= '09:30:00' AND substr(timestamp, 12, 8) <= '16:00:00'
               ORDER BY timestamp ASC
           '''
           params = (symbol,)
       else:
           today = now.strftime('%Y-%m-%d')
           query = '''
               SELECT timestamp, price
               FROM price_history
               WHERE stock_symbol = ?
               AND date(timestamp) = ?
               AND substr(timestamp, 12, 8) >= '09:30:00' AND substr(timestamp, 12, 8) <= '16:00:00'
               ORDER BY timestamp ASC
           '''
           params = (symbol, today)
   elif period == '1mo':
       start_date = end_date - relativedelta(months=1)
       print(f"Start date: {start_date}")
       print(f"End date: {end_date}")
       interval = 15
   elif period == '3mo':
       start_date = end_date - relativedelta(months=3)
       interval = 30
   elif period == '6mo':
       start_date = end_date - relativedelta(months=6)
       interval = 60
   elif period == '1y':
       start_date = end_date - relativedelta(years=1)
       interval = 240
   else:  # 5y
       start_date = end_date - relativedelta(years=5)
       
   if period != '1day':
       if period == '5y':
           query = '''
               SELECT timestamp, price
               FROM price_history
               WHERE stock_symbol = ?
               AND timestamp BETWEEN ? AND ?
               AND substr(timestamp, 12, 8) = '16:00:00'
               GROUP BY date(timestamp)
               ORDER BY timestamp ASC
           '''
           params = (symbol, start_date.strftime('%Y-%m-%d %H:%M:%S'),
                    end_date.strftime('%Y-%m-%d %H:%M:%S'))
       else:
           query = '''
               SELECT timestamp, price
               FROM price_history
               WHERE stock_symbol = ?
               AND timestamp BETWEEN ? AND ?
               AND substr(timestamp, 12, 8) >= '09:30:00' AND substr(timestamp, 12, 8) <= '16:00:00'
               GROUP BY strftime('%s', timestamp) / (? * 60)
               ORDER BY timestamp ASC
           '''
           params = (symbol, start_date.strftime('%Y-%m-%d %H:%M:%S'),
                    end_date.strftime('%Y-%m-%d %H:%M:%S'), interval)

   cursor.execute(query, params)
   data = cursor.fetchall()
   connection.close()

   if not data:
       return json.dumps({
           'data': [],
           'layout': {'title': f'No data available for {symbol}'}
       })

   trace = go.Scatter(
       x=[row[0] for row in data],
       y=[row[1] for row in data],
       mode='lines',
       name=symbol
   )

   if period == '1day' and current_time >= market_open and current_time <= market_close:
       layout = go.Layout(
           title=f'{symbol} Stock Price',
           xaxis={
               'title': 'Timestamp',
               'type': 'date',
               'range': [
                   now.strftime('%Y-%m-%d') + ' 09:30:00',
                   now.strftime('%Y-%m-%d') + ' 16:00:00'
               ],
               'showticklabels': False,
               'gridcolor': 'rgba(0,0,0,0)'
            },
           yaxis={'title': 'Price',
                  'gridcolor': 'rgba(0,0,0,0)'
            },
           template='plotly_white'
       )
   else:
       layout = go.Layout(
           title=f'{symbol} Stock Price',
           xaxis={
               'title': 'Timestamp',
               'type': 'category',
               'showticklabels': False,
               'gridcolor': 'rgba(0,0,0,0)'
            },
           yaxis={'title': 'Price',
                  'gridcolor': 'rgba(0,0,0,0)'
            },
           template='plotly_white',
       )

   fig = go.Figure(data=[trace], layout=layout)
   return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        symbol = request.form.get('symbol', '').upper()
        if symbol:
            return redirect(url_for('stock_detail', 
                                  symbol=symbol))
    return render_template('index.html')

@app.route('/stock/<symbol>')
def stock_detail(symbol):
    period = request.args.get('period', '1mo')  # Default to 1 month
    
    # Get the chart data
    chart_json = get_stock_chart_data(symbol, period)
    
    # Get current stock data
    connection, cursor = create_connection()
    cursor.execute('SELECT * FROM stocks_current WHERE stock_symbol = ?', (symbol,))
    current_data = cursor.fetchone()
    connection.close()
    
    return render_template('stock.html', 
                         symbol=symbol, 
                         period=period,
                         chart_json=chart_json,
                         current_data=current_data)

def update_charts():
    # List of stocks to update
    stock_symbols = ['TSLA', 'AAPL', 'NVDA', 'MSFT', 'WMT']
    update_current_month_data(stock_symbols)
    update_daily_price_history(stock_symbols)

if __name__ == "__main__":
    update_charts()
    # Set up the scheduler for data updates
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_charts, trigger="interval", seconds=60, misfire_grace_time=30)
    scheduler.start()
    
    # Start the Flask app
    app.run(debug=True)