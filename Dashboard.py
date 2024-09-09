import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd
import requests

ALPHA_VANTAGE_API_KEY = 'F85JS97CHAY518Y2' #Standard API rate limit is 25 requests per day. 

def load_top_5_stocks():
    top_5_stocks = []
    input_file_path = os.path.join(os.getcwd(), "top_5_stocks.txt")
    
    try:
        with open(input_file_path, "r") as file:
            lines = file.readlines()
            for line in lines:
                parts = line.strip().split(",")
                if len(parts) >= 3:
                    ticker = parts[0].strip()
                    potential_roi = parts[1].strip()
                    potential_success = parts[2].strip()
                    top_5_stocks.append((ticker, potential_roi, potential_success))
                else:
                    print(f"Skipping line with incorrect data: {line.strip()}")
    except Exception as e:
        print(f"Error loading top 5 stocks: {e}")
    
    print(f"Loaded top 5 stocks: {top_5_stocks}")
    return top_5_stocks

def fetch_company_overview(ticker):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data

def setup_ui(top_5_stocks):
    print("Setting up UI...")
    
    root = tk.Tk()
    root.title("TradeScout Dashboard")

    frame_left = tk.Frame(root)
    frame_left.pack(side=tk.LEFT, padx=20, pady=20)

    tk.Label(frame_left, text="Top 5 Stocks to Buy").grid(row=0, columnspan=3)

    columns = ('Ticker', 'Potential ROI', 'Potential Success')
    tree = ttk.Treeview(frame_left, columns=columns, show='headings')
    for col in columns:
        tree.heading(col, text=col)
    tree.grid(row=1, column=0, columnspan=3)

    tickers_in_top_5 = []
    for stock in top_5_stocks:
        try:
            ticker, potential_roi, potential_success = stock
            tree.insert("", "end", values=(ticker, potential_roi, potential_success))
            tickers_in_top_5.append(ticker)
        except ValueError as ve:
            print(f"Error inserting stock into Treeview: {ve}, stock: {stock}")

    frame_right = tk.Frame(root)
    frame_right.pack(side=tk.RIGHT, padx=20, pady=20)

    tk.Label(frame_right, text="Search Details:").grid(row=0, column=0)
    search_entry = tk.Entry(frame_right)
    search_entry.grid(row=0, column=1)

    def display_chart(ticker):
        print(f"Displaying chart for: {ticker}")

        csv_file_path = os.path.join(os.getcwd(), 'Historical Data', f'{ticker}.csv')
        if not os.path.exists(csv_file_path):
            messagebox.showerror("Error", f"No historical data available for {ticker}.")
            return

        try:
            data = pd.read_csv(csv_file_path, parse_dates=['timestamp'], index_col='timestamp')
            data = data[['close']]
            print(f"Loaded data for {ticker}:")
            print(data.head())

            chart_window = tk.Toplevel()
            chart_window.title(f"{ticker} Price Chart")

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(data.index, data['close'], label='Close Price', color='black')

            top_5_file_path = os.path.join(os.getcwd(), "top_5_stocks.txt")
            confirmed_status = None
            with open(top_5_file_path, "r") as file:
                for line in file:
                    if line.startswith(ticker):
                        confirmed_status = line.split(",")[-1].strip()
                        break
            print(f"Confirmed status for {ticker}: {confirmed_status}")

            ema_file_name = f'{ticker}_{"Confirmed" if confirmed_status == "Confirmed" else "Non_Confirmed"}_EMA_Combo.txt'
            ema_file_path = os.path.join(os.getcwd(), 'Backtesting', ema_file_name)
            print(f"Loading EMA file: {ema_file_path}")

            short_ema = None
            long_ema = None

            if os.path.exists(ema_file_path):
                with open(ema_file_path, "r") as file:
                    lines = file.readlines()
                    # Extract Short EMA and Long EMA only from the first line that contains them
                    for line in lines:
                        if "Short EMA" in line and "Long EMA" in line:
                            short_ema = int(line.split('=')[1].split(',')[0].strip())
                            long_ema = int(line.split('=')[2].strip())
                            print(f"Short EMA for {ticker}: {short_ema}")
                            print(f"Long EMA for {ticker}: {long_ema}")
                            break  # Stop after the first occurrence of Short EMA and Long EMA

                    buy_signals = []
                    sell_signals = []
                    for line in lines:
                        if "BUY at" in line:
                            parts = line.split()
                            date = pd.to_datetime(parts[2] + " " + parts[3])
                            price = float(parts[6].strip(','))
                            buy_signals.append((date, price))
                        elif "SELL at" in line:
                            parts = line.split()
                            date = pd.to_datetime(parts[2] + " " + parts[3])
                            price = float(parts[6].strip(','))
                            sell_signals.append((date, price))

                    if short_ema and long_ema:
                        data[f'Short EMA ({short_ema})'] = data['close'].ewm(span=short_ema).mean()
                        data[f'Long EMA ({long_ema})'] = data['close'].ewm(span=long_ema).mean()
                        print(f"EMA data for {ticker}:")
                        print(data[[f'Short EMA ({short_ema})', f'Long EMA ({long_ema})']].head())
                        ax.plot(data.index, data[f'Short EMA ({short_ema})'], label=f'Short EMA ({short_ema})', color='orange')
                        ax.plot(data.index, data[f'Long EMA ({long_ema})'], label=f'Long EMA ({long_ema})', color='green')

                    buy_offset = 0.90
                    sell_offset = 1.10

                    if buy_signals:
                        buy_prices = [price * buy_offset for _, price in buy_signals]
                        ax.scatter(*zip(*[(date, price) for (date, _), price in zip(buy_signals, buy_prices)]), 
                                   marker='^', color='blue', label='Buy Signal')
                    if sell_signals:
                        sell_prices = [price * sell_offset for _, price in sell_signals]
                        ax.scatter(*zip(*[(date, price) for (date, _), price in zip(sell_signals, sell_prices)]), 
                                   marker='v', color='red', label='Sell Signal')

            ax.legend(loc='upper left')
            ax.set_title(f'{ticker} Price Chart')
            canvas = FigureCanvasTkAgg(fig, master=chart_window)
            canvas.draw()
            canvas.get_tk_widget().pack()

            # Add suggested entry criteria panel
            overview_data = fetch_company_overview(ticker)
            entry_price = buy_signals[-1][1] if buy_signals else None
            stop_loss = round(entry_price * 0.9, 2) if entry_price else None

            entry_criteria_frame = tk.Frame(chart_window)
            entry_criteria_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

            tk.Label(entry_criteria_frame, text=f"Symbol: {ticker}").pack(anchor='w')
            tk.Label(entry_criteria_frame, text=f"Name: {overview_data.get('Name')}").pack(anchor='w')
            tk.Label(entry_criteria_frame, text=f"Exchange: {overview_data.get('Exchange')}").pack(anchor='w')
            tk.Label(entry_criteria_frame, text=f"Sector: {overview_data.get('Sector')}").pack(anchor='w')
            tk.Label(entry_criteria_frame, text=f"Suggested Entry Price: ${entry_price}").pack(anchor='w')
            tk.Label(entry_criteria_frame, text=f"Suggested Stop Loss: ${stop_loss}").pack(anchor='w')
            tk.Label(entry_criteria_frame, text=f"EMA Combo: Short EMA = {short_ema}, Long EMA = {long_ema}").pack(anchor='w')

        except Exception as e:
            print(f"Error during plotting for {ticker}: {e}")
            messagebox.showerror("Error", f"Failed to load and plot data for {ticker}. Error: {e}")

    # Search function
    def on_search():
        ticker = search_entry.get().strip().upper()
        if not ticker:
            print("No ticker entered.")  # Debugging statement
            messagebox.showwarning("Input Error", "Please enter a stock ticker.")
            return
        
        print(f"Search initiated for: {ticker}")  # Debugging statement
        if ticker in tickers_in_top_5:
            print(f"Ticker {ticker} found in top 5 stocks.")  # Debugging statement
            display_chart(ticker)
        else:
            print(f"Ticker {ticker} not found in top 5 stocks.")  # Debugging statement
            # Display a warning or message to the user
            messagebox.showwarning("Invalid Ticker", f"{ticker} is not in the Top 5 Stocks to Buy.")

    search_button = tk.Button(frame_right, text="Search", command=on_search)
    search_button.grid(row=0, column=2)

    root.mainloop()

if __name__ == "__main__":
    top_5_stocks = load_top_5_stocks()
    if top_5_stocks:
        setup_ui(top_5_stocks)
    else:
        print("No stocks loaded to display on the dashboard.")
