import os
import pandas as pd
import joblib
from datetime import datetime, timedelta
import Dashboard  # Import the setup_ui function from Dashboard.py

# Load the trained models
roi_model = joblib.load(os.path.join('Model Training', 'roi_model.pkl'))
success_model = joblib.load(os.path.join('Model Training', 'success_model.pkl'))

# Set the date range (last 30 days)
current_date = datetime.now()
start_date = current_date - timedelta(days=30)

def parse_datetime_naive(date_str):
    # Parse the datetime string and remove timezone information to make it naive
    dt = pd.to_datetime(date_str)
    return dt.tz_localize(None)  # Convert to naive datetime (removes timezone)

def extract_features_from_backtesting_file(file_path):
    features = []
    file_source = None  # This will store the file (Confirmed or Non-confirmed)

    # Determine if the file is Confirmed or Non-confirmed
    if "Non_Confirmed" in file_path:
        confirmation_status = 0  # It's non-confirmed since we're reading from a Non_Confirmed file
        file_source = "Non-Confirmed"
    else:
        confirmation_status = 1  # It's confirmed since we're reading from a Confirmed file
        file_source = "Confirmed"
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
        parsing_buy_trades = False
        
        for line in lines:
            if line.startswith("Buy Trades Executed:"):
                parsing_buy_trades = True
                continue
            if parsing_buy_trades and not line.startswith("BUY"):
                break
            if parsing_buy_trades and line.startswith("BUY"):
                # Extract trade date, volume, short EMA, and long EMA
                parts = line.split()
                trade_date_str = parts[2] + " " + parts[3]
                trade_date = parse_datetime_naive(trade_date_str)
                
                roi_part = line.split("ROI = ")[1].split(",")[0].strip()
                if roi_part == "Pending" and trade_date >= start_date:
                    volume = int(line.split("Volume = ")[1].split(",")[0].strip())
                    short_ema = int(line.split("Short EMA = ")[1].split(",")[0].strip())
                    long_ema = int(line.split("Long EMA = ")[1].split(",")[0].strip())
                    # Add features: Volume, Confirmation_Status, Short EMA, Long EMA
                    features.append([volume, confirmation_status, short_ema, long_ema])
                    break
    return features, file_source

def predict_stock_potential(file_path):
    features, file_source = extract_features_from_backtesting_file(file_path)
    predictions = []
    if features:
        for feature in features:
            roi_prediction = roi_model.predict([feature])[0]
            success_prediction = success_model.predict([feature])[0]
            predictions.append((roi_prediction, success_prediction, file_source))
    return predictions

def start_predict():
    print("Start prediction...")

    backtesting_dir = os.path.join(os.getcwd(), 'Backtesting')
    stock_predictions = {}

    for file_name in os.listdir(backtesting_dir):
        if file_name.endswith('_EMA_Combo.txt'):
            file_path = os.path.join(backtesting_dir, file_name)
            stock_ticker = file_name.split('_')[0]
            features, file_source = extract_features_from_backtesting_file(file_path)
            if features:
                predictions = predict_stock_potential(file_path)
                if stock_ticker in stock_predictions:
                    existing_signal = stock_predictions[stock_ticker][0][2]
                    if existing_signal == "Non-Confirmed" and file_source == "Confirmed":
                        stock_predictions[stock_ticker] = predictions
                else:
                    stock_predictions[stock_ticker] = predictions

    sorted_stocks = sorted(stock_predictions.items(), key=lambda x: (
        -1 if x[1][0][0] == 'High ROI' else (0 if x[1][0][0] == 'Medium ROI' else 1),
        -1 if x[1][0][1] == 'High' else 1,
        -1 if x[1][0][2] == 'Confirmed' else 1,
        x[0]
    ))

    top_5_stocks = sorted_stocks[:5]

    # Store all data in a txt file in the current working directory
    output_file_path = os.path.join(os.getcwd(), "top_5_stocks.txt")
    with open(output_file_path, "w") as file:
        for stock in top_5_stocks:
            ticker, predictions = stock
            file.write(f"{ticker},{predictions[0][0]},{predictions[0][1]},{predictions[0][2]}\n")

    print("Top 5 Stocks to Buy:")
    for ticker, prediction in top_5_stocks:
        print(f"{ticker}: {prediction[0]}")

    # Now call the Dashboard module to load the data and display the UI
    top_5_stocks_data = Dashboard.load_top_5_stocks()  # Load data in Dashboard
    if top_5_stocks_data:
        Dashboard.setup_ui(top_5_stocks_data)
    else:
        print("No stocks loaded to display on the dashboard.")