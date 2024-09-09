US Stocks Trading Signal Bot – TradeScout

Overview:
The US Stocks Trading Signal Bot automates the analysis of stock data, generating buy/sell signals and providing actionable insights for traders. It consists of seven key modules that form a pipeline for data collection, feature extraction, model training, prediction, and presentation through a graphical user interface (GUI).

Process Flow and Key Algorithms:
1. LoginPage Module: Authenticates the user’s credentials via the Alpaca API and, upon successful login, initiates the data collection process.
2. DataCollection Module: Retrieves historical stock data using the Alpaca API and stores it as CSV files. This data is crucial for the subsequent feature extraction and backtesting processes.
3. FeatureExtract Module: Extracts important features such as Exponential Moving Averages (EMAs) from historical stock data, identifying potential buy/sell signals based on EMA crossovers.
4. Backtest Module: Conducts grid search optimization on various EMA combinations to find the best-performing strategy for each stock. It uses EMA crossover strategies to backtest trades and calculate Return on Investment (ROI).
5. ModelTrain Module: Trains two Random Forest models to predict ROI categories (Low, Medium, High) and the probability of success (High/Low). The trained models are saved for use during the prediction stage.
6. Prediction Module: Utilizes the trained models to predict stock performance over the last 30 days, sorts predictions based on ROI, success probability, and confirmation status, and saves the top 5 stocks to a text file.
7. Dashboard Module: Presents the top 5 stocks in a user-friendly dashboard, allowing users to search for stocks, view historical price charts, and see suggested entry criteria based on the bot's analysis.

Key Algorithms and Strategies:
- EMA Crossover Strategy: Generates buy/sell signals based on EMA crossovers.
- Grid Search Optimization: Applied during the backtesting process to find the best EMA combinations.
- Random Forest Classifier: Used in the model training module to predict ROI and success probability.

Installation and Running the Program:

Step 1: Install Python - Ensure Python 3.x is installed on your system.

Step 2: Install Required Libraries - Open your terminal or command prompt and run the following command to install the necessary libraries:
pip install tkinter matplotlib pandas requests alpaca-trade-api scikit-learn joblib

Step 3: Obtain API Keys - Get your API keys from Alpaca.
The Alpha Vantage API key has already been hardcoded into the script, but you can update it if needed.
Update the LoginPage and Dashboard modules with your API keys.

Step 4: Run the Bot
Start the program by running LoginPage.py. This will prompt you to enter your Alpaca API credentials.
After successful login, the bot will automatically collect data, extract features, backtest strategies, train models, and make predictions.
Once the predictions are made, the dashboard will launch, displaying the top 5 stocks to buy.

This bot automates complex stock analysis to help traders make informed decisions based on AI-driven insights and backtested strategies.
