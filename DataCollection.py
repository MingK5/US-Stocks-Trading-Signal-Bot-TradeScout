import os
# Automatically set the current working directory to the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print(f"Current working directory set to: {os.getcwd()}")  # Debugging statement
import pandas as pd
from datetime import datetime
import alpaca_trade_api as tradeapi
import FeatureExtract

# Directory for saving historical data
DATA_DIR = os.path.join(os.getcwd(), 'Historical Data')

# Ensure the directory for historical data exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def start_data_collection(api):
    print("Starting data collection...")  # Debugging statement
    tickers = read_database_file()
    
    # Check if tickers were loaded correctly
    if not tickers:
        print("No tickers found. Please check Database.txt file.")
        return  # Exit if no tickers were loaded

    for ticker in tickers:
        print(f"Processing ticker: {ticker}")  # Debugging statement
        check_historical_data(ticker, api)

    print("Data collection complete. Starting feature extraction...")
    FeatureExtract.start_feature_extraction()

def read_database_file():
    # Reads stock tickers from the Database.txt file.
    DATABASE_FILE = os.path.join(os.getcwd(), 'Database.txt')
    if not os.path.exists(DATABASE_FILE):
        print(f"{DATABASE_FILE} does not exist. Creating a default file with some tickers.")
        with open(DATABASE_FILE, 'w') as file:
            file.write("SPY\nQQQ\nDJI\nAAPL\nTSLA\n")  # Default tickers
    
    # Check file contents
    with open(DATABASE_FILE, 'r') as file:
        tickers = [line.strip() for line in file.readlines()]
    
    # Log the tickers that were read
    print(f"Tickers read from {DATABASE_FILE}: {tickers}")
    return tickers

def check_historical_data(ticker, api):
    # Check if historical data for the ticker exists and is up to date. If not, fetch it.
    data_path = os.path.join(DATA_DIR, f"{ticker}.csv")
    
    # If data does not exist, or is outdated, download new data
    if not os.path.exists(data_path):
        print(f"No historical data for {ticker}. Initiating download...")  # Debugging statement
        download_historical_data(ticker, api)
    else:
        # Try to read the CSV file and parse dates using the correct column name
        try:
            last_data_date = pd.read_csv(data_path, index_col='timestamp', parse_dates=['timestamp']).index[-1]
            last_data_date = pd.to_datetime(last_data_date)
            today = pd.Timestamp.today().normalize()

            if last_data_date < today:
                print(f"Data for {ticker} is outdated. Downloading new data...")  # Debugging statement
                download_historical_data(ticker, api)
            else:
                print(f"Historical data for {ticker} is up to date.")  # Debugging statement
        except Exception as e:
            print(f"Error reading existing data for {ticker}: {e}")  # Debugging statement
            download_historical_data(ticker, api)

def download_historical_data(ticker, api):
    # Download historical data for a given stock ticker from Alpaca
    print(f"Downloading historical data for {ticker}...")  # Debugging statement
    
    # Define the start and end dates for the data (e.g., last 5 years)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - pd.DateOffset(years=5)).strftime('%Y-%m-%d')
    
    try:
        # Fetch daily bars for the given ticker with a limit of 5000 data points
        barset = api.get_bars(
            symbol=ticker,
            timeframe='1Day',
            start=start_date,
            end=end_date,
            limit=5000,  # Limiting to 5000 data points
            feed='iex',
            adjustment='all'
        ).df.tz_convert('America/New_York')  # Convert to New York timezone
        
        # Save data to CSV in the "Historical Data" directory
        barset.to_csv(os.path.join(DATA_DIR, f"{ticker}.csv"))
        print(f"Downloaded and saved historical data for {ticker}.")  # Debugging statement
    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")  # Debugging statement
