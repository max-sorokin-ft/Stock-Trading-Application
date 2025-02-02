# app.py - Main Flask application file
# Handles routing, chart generation, and scheduled updates

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler  
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
import plotly
import plotly.graph_objs as go
import json
from database import create_connection, update_current_stock_data, update_intraday_price_history, update_current_month_data
from setup import update_daily_price_history
import secrets

# Initialize Flask application
app = Flask(__name__)   
app.config['SECRET_KEY'] = secrets.token_hex() 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    @staticmethod
    def get(user_id):
        connection, cursor = create_connection()
        cursor.execute('''SELECT * FROM users WHERE id = ?''', (user_id,))
        user_information = cursor.fetchone()
        connection.close()

        if user_information:
            return User(user_information[0], user_information[1])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        connection, cursor = create_connection()
        cursor.execute('''SELECT * FROM users WHERE username = ?''', (username,))
        user = cursor.fetchone()
        connection.close()

        if user and check_password_hash(user[2], password):
            user_obj = User(user[0], user[1])  # id, username
            login_user(user_obj)
            return redirect(url_for('index'))
        
        flash('Wrong username or password')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        connection, cursor = create_connection()
        cursor.execute('''SELECT * FROM users WHERE username = ?''', (username,))
        
        if cursor.fetchone():
            flash('Username already exists')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        cursor.execute('''INSERT INTO users (username, password_hash) VALUES(?, ?)''', (username, hashed_password))

        connection.commit()
        connection.close()

        return redirect(url_for('login')) 
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))  


def get_stock_chart_data(symbol, period):
    """
    Generate chart data for a given stock symbol and time period.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        period: Time period for chart ('1day', '1week', '1mo', '3mo', '6mo', '1y', '5y')
    
    Returns:
        JSON string containing chart data and layout configuration
    """
    connection, cursor = create_connection()
    
    # Calculate date range based on selected period
    end_date = datetime.now()
    if period == '1week':
        start_date = end_date - timedelta(days=7)
        interval = 5  # 5-minute intervals
    elif period == '1day':
        now = datetime.now()
        current_time = now.time()
        market_open = time(9, 30)  # Market opens at 9:30 AM EST
        market_close = time(16, 0)  # Market closes at 4:00 PM EST
        start_date = end_date - timedelta(days=1)
        interval = 1  # 1-minute intervals
        
        # Handle market hours logic
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
        interval = 15  # 15-minute intervals
    elif period == '3mo':
        start_date = end_date - relativedelta(months=3)
        interval = 30  # 30-minute intervals
    elif period == '6mo':
        start_date = end_date - relativedelta(months=6)
        interval = 60  # 60-minute intervals
    elif period == '1y':
        start_date = end_date - relativedelta(years=1)
        interval = 240  # 4-hour intervals
    else:  # 5y
        start_date = end_date - relativedelta(years=5)
        
    # Build query based on period
    if period != '1day':
        if period == '5y':
            # For 5-year view, use daily closing prices
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
            # For other periods, group by interval
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

    # Execute query and fetch data
    cursor.execute(query, params)
    chart_data = cursor.fetchall()
    connection.close()

    # Handle no data case
    if not chart_data:
        return json.dumps({
            'data': [],
            'layout': {'title': f'No data available for {symbol}'}
        })

    # Create Plotly trace
    trace = go.Scatter(
        x=[row[0] for row in chart_data],
        y=[row[1] for row in chart_data],
        mode='lines',
        name=symbol
    )

    # Configure chart layout
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

    # Return JSON-encoded chart configuration
    fig = go.Figure(data=[trace], layout=layout)
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/', methods=['GET', 'POST'])
def index():
    """Handle home page requests"""
    if request.method == 'POST':
        symbol = request.form.get('symbol', '').upper()
        if symbol:
            return redirect(url_for('stock_detail', symbol=symbol))
    return render_template('index.html')

@app.route('/stock/<symbol>')
def stock_detail(symbol):
    """
    Display detailed stock information and chart
    
    Args:
        symbol: Stock ticker symbol
    """
    period = request.args.get('period', '1mo')  # Default to 1 month view
    
    # Generate chart data
    chart_json = get_stock_chart_data(symbol, period)
    
    # Get current stock information
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
    """Update stock data for tracked symbols"""
    # List of tracked stocks (limited to 20 on lowest paid API tier)
    tracked_symbols = ['TSLA', 'AAPL', 'NVDA', 'MSFT', 'WMT']
    update_current_month_data(tracked_symbols)
    update_daily_price_history(tracked_symbols)

if __name__ == "__main__":
    # Initial data update
    update_charts()
    
    # Configure scheduler for periodic updates
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_charts, 
                     trigger="interval", 
                     seconds=60,  # Update every minute
                     misfire_grace_time=30)
    scheduler.start()
    
    # Start Flask application
    app.run(debug=True)