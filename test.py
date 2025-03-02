# test_quote.py
from stock_data import get_stock_data
import json
from datetime import datetime

def test_quote():
    # Test with a few different symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    test_data = {}
    for symbol in symbols:
        quote_data, symbol = get_stock_data(
            symbol, 
            daily_data_needed=False, 
            intraday_data_needed=False
        )
        test_data[symbol] = quote_data
    
    # Save to file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'quote_test_{timestamp}.json'
    
    with open(filename, 'w') as f:
        json.dump(test_data, f, indent=2)
        
    print(f"Data saved to {filename}")

if __name__ == "__main__":
    test_quote()