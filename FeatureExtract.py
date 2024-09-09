import os
import pandas as pd
import Backtest  # Import the Backtest module

# Directory for saving feature extraction data
FEATURE_DIR = os.path.join(os.getcwd(), 'Feature Extraction')

# Ensure the directory for feature extraction data exists
if not os.path.exists(FEATURE_DIR):
    os.makedirs(FEATURE_DIR)

def calculate_ema(df, window):
    """Calculate the Exponential Moving Average (EMA) for a given window."""
    return df['close'].ewm(span=window, adjust=False).mean()

def extract_ema_features(ticker, historical_data_path):
    """Extract features based on EMA crossover strategy."""
    print(f"Extracting features for {ticker}...")
    
    # Load historical data
    try:
        df = pd.read_csv(historical_data_path, index_col='timestamp', parse_dates=True)  # Ensure correct column name
    except Exception as e:
        print(f"Error reading historical data for {ticker}: {e}")
        return
    
    # Calculate EMA 18 and EMA 200
    df['EMA_18'] = calculate_ema(df, 18)
    df['EMA_200'] = calculate_ema(df, 200)
    
    # Generate potential buy and sell signals
    df['Potential_Buy'] = (df['EMA_18'] > df['EMA_200']) & (df['EMA_18'].shift(1) <= df['EMA_200'].shift(1))
    df['Potential_Sell'] = (df['EMA_18'] < df['EMA_200']) & (df['EMA_18'].shift(1) >= df['EMA_200'].shift(1))
    
    # Initialize columns for confirmed signals and entry prices
    df['Confirmed_Buy'] = False
    df['Confirmed_Sell'] = False
    df['Entry_Price'] = None
    
    # Logic for confirming buy and sell signals
    for i in range(1, len(df)):
        if df.iloc[i]['Potential_Buy']:
            if (df.iloc[i + 1]['open'] > df.iloc[i]['high'] + 0.01 or
                df.iloc[i + 1]['high'] > df.iloc[i]['high'] + 0.01 or
                df.iloc[i + 1]['low'] > df.iloc[i]['high'] + 0.01 or
                df.iloc[i + 1]['close'] > df.iloc[i]['high'] + 0.01):
                df.at[df.index[i + 1], 'Confirmed_Buy'] = True
                df.at[df.index[i + 1], 'Entry_Price'] = df.iloc[i + 1]['close']

        if df.iloc[i]['Potential_Sell']:
            if (df.iloc[i + 1]['open'] < df.iloc[i]['low'] - 0.01 or
                df.iloc[i + 1]['high'] < df.iloc[i]['low'] - 0.01 or
                df.iloc[i + 1]['low'] < df.iloc[i]['low'] - 0.01 or
                df.iloc[i + 1]['close'] < df.iloc[i]['low'] - 0.01):
                df.at[df.index[i + 1], 'Confirmed_Sell'] = True
                df.at[df.index[i + 1], 'Entry_Price'] = df.iloc[i + 1]['close']

    # Save extracted features to a file, including open, high, low, close, and volume data
    feature_file = os.path.join(FEATURE_DIR, f"{ticker}_Feature.txt")
    df[['open', 'high', 'low', 'close', 'volume', 'EMA_18', 'EMA_200', 'Potential_Buy', 'Potential_Sell', 'Confirmed_Buy', 'Confirmed_Sell', 'Entry_Price']].to_csv(feature_file)
    print(f"Features extracted and saved for {ticker}.")

def start_feature_extraction():
    """Start the feature extraction process for all tickers."""
    historical_data_dir = os.path.join(os.getcwd(), 'Historical Data')
    
    for file_name in os.listdir(historical_data_dir):
        if file_name.endswith('.csv'):
            ticker = file_name.replace('.csv', '')
            historical_data_path = os.path.join(historical_data_dir, file_name)
            extract_ema_features(ticker, historical_data_path)

    # After feature extraction completes, initiate backtesting
    try:
        print("Feature extraction completed. Starting backtesting...")
        Backtest.start_backtesting()
    except Exception as e:
        print(f"Error during backtesting: {e}")
