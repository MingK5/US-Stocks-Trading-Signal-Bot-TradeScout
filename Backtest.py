import os
import pandas as pd
import numpy as np
import ModelTrain  # Import the ModelTrain module

# Get the current working directory and define paths
current_dir = os.getcwd()
BACKTEST_DIR = os.path.join(current_dir, 'Backtesting')
FEATURE_DIR = os.path.join(current_dir, 'Feature Extraction')

# Ensure the directory for backtesting data exists
if not os.path.exists(BACKTEST_DIR):
    os.makedirs(BACKTEST_DIR)

# Grid search for the optimal EMA combination
def grid_search_optimization(ticker, feature_data):
    ema_combos = [
    (12, 26),  # Commonly used in MACD
    (9, 21),   # Short-term momentum 
    (20, 50),  # Medium-term trend
    (50, 200), # Long-term trend reversal (Golden Cross/Death Cross)
    (10, 30),  # Aggressive short-term focus
    (15, 45),  # Balanced short-to-medium trend
    (18, 200), # Short-to-medium term momentum
    (18, 100), # Mid-to-long term trend reversal
    (30, 90),  # Slower trends
    (5, 15),   # Scalping strategy
    (100, 200) # Very long-term strategy
    ]
    
    # Confirmed trades handling
    best_combo_confirmed = None
    best_roi_confirmed = -np.inf
    confirmed_trades = []

    for short_ema, long_ema in ema_combos:
        confirmed_trades_set, confirmed_roi = backtest_strategy(ticker, feature_data, short_ema, long_ema, confirmed=True)
        if confirmed_roi > best_roi_confirmed:
            best_combo_confirmed = (short_ema, long_ema)
            best_roi_confirmed = confirmed_roi
            confirmed_trades = confirmed_trades_set

    save_best_combo_results(ticker, best_combo_confirmed, confirmed_trades, best_roi_confirmed, confirmed=True)

    # Non-confirmed trades handling
    best_combo_non_confirmed = None
    best_roi_non_confirmed = -np.inf
    non_confirmed_trades = []

    for short_ema, long_ema in ema_combos:
        non_confirmed_trades_set, non_confirmed_roi = backtest_strategy(ticker, feature_data, short_ema, long_ema, confirmed=False)
        if non_confirmed_roi > best_roi_non_confirmed:
            best_combo_non_confirmed = (short_ema, long_ema)
            best_roi_non_confirmed = non_confirmed_roi
            non_confirmed_trades = non_confirmed_trades_set

    save_best_combo_results(ticker, best_combo_non_confirmed, non_confirmed_trades, best_roi_non_confirmed, confirmed=False)


def backtest_strategy(ticker, df, short_ema, long_ema, confirmed=True):
    """
    Backtest the EMA crossover strategy. If `confirmed` is True, only execute trades with confirmation. 
    If `confirmed` is False, execute trades based solely on EMA crossover signals.
    Ensure only one buy and one sell trade per day.
    """
    df['EMA_Short'] = df['close'].ewm(span=short_ema, adjust=False).mean()
    df['EMA_Long'] = df['close'].ewm(span=long_ema, adjust=False).mean()

    df['Buy_Signal'] = (df['EMA_Short'] > df['EMA_Long']) & (df['EMA_Short'].shift(1) <= df['EMA_Long'].shift(1))
    df['Sell_Signal'] = (df['EMA_Short'] < df['EMA_Long']) & (df['EMA_Short'].shift(1) >= df['EMA_Long'].shift(1))

    trades = []
    in_position = False
    entry_price = None
    stop_loss = None
    capital = 100000
    position_size = 0

    last_trade_date = None

    for i in range(1, len(df) - 1):
        trade_date = df.index[i].date()  # Extract date only

        # Buy signal: ensure only one trade per day
        if df.iloc[i]['Buy_Signal'] and not in_position and (last_trade_date is None or last_trade_date != trade_date):
            if not confirmed or (df.iloc[i + 1]['open'] > df.iloc[i]['high'] + 0.01 or
                                 df.iloc[i + 1]['high'] > df.iloc[i]['high'] + 0.01 or
                                 df.iloc[i + 1]['low'] > df.iloc[i]['high'] + 0.01 or
                                 df.iloc[i + 1]['close'] > df.iloc[i]['high'] + 0.01):
                entry_price = df.iloc[i + 1]['close'] + 0.01
                stop_loss = entry_price * 0.9
                position_size = capital / entry_price
                in_position = True
                trades.append(('BUY', df.index[i + 1], entry_price, confirmed))
                last_trade_date = trade_date  # Update last trade date

        # Sell signal: ensure only one trade per day
        if in_position and (df.iloc[i]['Sell_Signal'] or df.iloc[i]['close'] <= stop_loss):
            if not confirmed or (df.iloc[i + 1]['open'] < df.iloc[i]['low'] - 0.01 or
                                 df.iloc[i + 1]['high'] < df.iloc[i]['low'] - 0.01 or
                                 df.iloc[i + 1]['low'] < df.iloc[i]['low'] - 0.01 or
                                 df.iloc[i + 1]['close'] < df.iloc[i]['low'] - 0.01):
                exit_price = df.iloc[i + 1]['close'] - 0.01
                capital += (exit_price - entry_price) * position_size
                trades.append(('SELL', df.index[i + 1], exit_price, confirmed))
                in_position = False
                last_trade_date = trade_date  # Update last trade date

    roi = (capital - 100000) / 100000 * 100
    return trades, roi


def get_trade_volume(ticker, trade_timestamp):
    """
    Retrieve the volume data for a specific trade timestamp from the Feature Extraction file.
    """
    feature_data_path = os.path.join(FEATURE_DIR, f"{ticker}_Feature.txt")
    
    # Load the feature data
    feature_df = pd.read_csv(feature_data_path, index_col='timestamp', parse_dates=True)
    
    # Extract the volume for the specific timestamp
    if trade_timestamp in feature_df.index:
        return feature_df.loc[trade_timestamp, 'volume']
    else:
        return "N/A"  # Return N/A if no volume data is found for the timestamp


def save_best_combo_results(ticker, best_combo, trades, roi, confirmed):
    """
    Save the best EMA combination and all trades executed with this combo.
    """
    file_suffix = "Confirmed" if confirmed else "Non_Confirmed"
    results_file = os.path.join(BACKTEST_DIR, f"{ticker}_{file_suffix}_EMA_Combo.txt")

    with open(results_file, 'w') as f:
        # Write the best EMA combination and ROI
        f.write(f"Best EMA Combo for {ticker}: Short EMA = {best_combo[0]}, Long EMA = {best_combo[1]}\n")
        f.write(f"Total ROI ({file_suffix} Trades): {roi:.2f}%\n\n")

        # Write the Buy Trades Executed section
        f.write("Buy Trades Executed:\n")
        for i in range(len(trades)):
            trade = trades[i]
            if trade[0] == 'BUY':
                volume = get_trade_volume(ticker, trade[1])
                roi_value = "Pending"
                if i + 1 < len(trades) and trades[i + 1][0] == 'SELL':
                    buy_price = trade[2]
                    sell_price = trades[i + 1][2]
                    roi_value = f"{((sell_price - buy_price) / buy_price) * 100:.2f}%"
                # Append Short EMA and Long EMA to the Buy trade information
                f.write(f"{trade[0]} at {trade[1]} with price {trade[2]:.2f}, Volume = {volume}, ROI = {roi_value}, {file_suffix}, Short EMA = {best_combo[0]}, Long EMA = {best_combo[1]}\n")

        # Write the Trades Executed section (includes both buy and sell trades)
        f.write("\nTrades Executed:\n")
        for trade in trades:
            volume = get_trade_volume(ticker, trade[1])
            f.write(f"{trade[0]} at {trade[1]} with price {trade[2]:.2f}, Volume = {volume}\n")


def start_backtesting():
    """Start the backtesting process for all tickers."""
    for file_name in os.listdir(FEATURE_DIR):
        if file_name.endswith('_Feature.txt'):
            ticker = file_name.replace('_Feature.txt', '')
            feature_data_path = os.path.join(FEATURE_DIR, file_name)
            feature_data = pd.read_csv(feature_data_path, index_col='timestamp', parse_dates=True)
            grid_search_optimization(ticker, feature_data)
    
    # After backtesting is complete, start model training
    try:
        print("Backtesting completed. Starting model training...")
        ModelTrain.start_model_training()
    except Exception as e:
        print(f"Error during model training: {e}")
