import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib  # To save the trained model
import Prediction

# Directory for storing models and training data
MODEL_DIR = os.path.join(os.getcwd(), 'Model Training')

# Ensure the directory exists
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

def load_data_and_labels():
    """
    Load data from both confirmed and non-confirmed files and generate labels based on Volume, ROI, EMA values, and Probability of Success.
    Returns the combined features and labels as separate datasets.
    """
    data = []
    roi_labels = []
    success_labels = []
    
    backtesting_dir = os.path.join(os.getcwd(), 'Backtesting')
    
    # Loop through both confirmed and non-confirmed files
    for confirmed_status in ['Confirmed', 'Non_Confirmed']:
        for file_name in os.listdir(backtesting_dir):
            if file_name.endswith(f'{confirmed_status}_EMA_Combo.txt'):
                file_path = os.path.join(backtesting_dir, file_name)
                print(f"Processing file: {file_path}")
                
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    parsing_buy_trades = False
                    
                    for line in lines:
                        # Start parsing after encountering "Buy Trades Executed:"
                        if line.startswith("Buy Trades Executed:"):
                            parsing_buy_trades = True
                            continue  # Skip this line and start parsing the next ones
                        
                        # Stop parsing when encountering another section like "Trades Executed:"
                        if line.startswith("Trades Executed:"):
                            parsing_buy_trades = False
                        
                        if parsing_buy_trades and line.startswith("BUY"):
                            try:
                                # Extracting data from the Buy Trades section
                                parts = line.strip().split(", ")
                                
                                # Initialize variables
                                volume = None
                                roi = None
                                short_ema = None
                                long_ema = None
                                confirmation_status = 1 if confirmed_status == 'Confirmed' else 0
                                
                                for part in parts:
                                    if "Volume =" in part:
                                        volume = int(part.split("=")[1].strip())
                                    elif "ROI =" in part:
                                        roi_text = part.split("=")[1].strip()
                                        if roi_text != "Pending":
                                            roi = float(roi_text.replace("%", "").strip())
                                    elif "Short EMA =" in part:
                                        short_ema = int(part.split("=")[1].strip())
                                    elif "Long EMA =" in part:
                                        long_ema = int(part.split("=")[1].strip())
                                
                                # Ensure that we have successfully extracted all required fields
                                if volume is not None and roi is not None and short_ema is not None and long_ema is not None:
                                    # Label based on ROI categories
                                    if roi <= 10:
                                        roi_label = "Low ROI"
                                    elif 11 <= roi <= 30:
                                        roi_label = "Medium ROI"
                                    else:
                                        roi_label = "High ROI"
                                    
                                    # Success label based on ROI (High/Low Probability of Success)
                                    success_label = "High" if roi > 0 else "Low"
                                    
                                    # Append features and labels
                                    data.append([volume, confirmation_status, short_ema, long_ema])
                                    roi_labels.append(roi_label)
                                    success_labels.append(success_label)
                                else:
                                    print(f"Skipping line due to missing data: {line.strip()}")
                            
                            except Exception as e:
                                print(f"Error processing line: {line.strip()} -> {e}")
    
    print(f"Total entries collected: {len(data)}")
    return data, roi_labels, success_labels

def train_model(data, roi_labels, success_labels):
    """
    Train two Random Forest models and evaluate their performance.
    One model will predict the ROI label, and the other will predict the success probability.
    """
    # Convert to DataFrame
    df = pd.DataFrame(data, columns=['volume', 'confirmation_status', 'short_ema', 'long_ema'])  # Include EMA values as features
    roi_labels_df = pd.Series(roi_labels)
    success_labels_df = pd.Series(success_labels)
    
    # Split the data into training and testing sets
    X_train, X_test, y_train_roi, y_test_roi = train_test_split(df[['volume', 'confirmation_status', 'short_ema', 'long_ema']], roi_labels_df, test_size=0.2, random_state=42)
    X_train_s, X_test_s, y_train_success, y_test_success = train_test_split(df[['volume', 'confirmation_status', 'short_ema', 'long_ema']], success_labels_df, test_size=0.2, random_state=42)
    
    # Initialize and train the ROI model
    roi_model = RandomForestClassifier(n_estimators=100, random_state=42)
    roi_model.fit(X_train, y_train_roi)
    
    # Initialize and train the Success Probability model
    success_model = RandomForestClassifier(n_estimators=100, random_state=42)
    success_model.fit(X_train_s, y_train_success)
    
    # Make predictions on the test set
    y_pred_roi = roi_model.predict(X_test)
    y_pred_success = success_model.predict(X_test_s)
    
    # Evaluate the models
    print("ROI Model Performance:")
    print(confusion_matrix(y_test_roi, y_pred_roi))
    print(classification_report(y_test_roi, y_pred_roi))
    
    print("Success Probability Model Performance:")
    print(confusion_matrix(y_test_success, y_pred_success))
    print(classification_report(y_test_success, y_pred_success))
    
    # Save the trained models
    roi_model_path = os.path.join(MODEL_DIR, 'roi_model.pkl')
    success_model_path = os.path.join(MODEL_DIR, 'success_model.pkl')
    joblib.dump(roi_model, roi_model_path)
    joblib.dump(success_model, success_model_path)
    print(f"Models saved to {roi_model_path} and {success_model_path}")

def start_model_training():
    """
    Main function to load data, train the models, and save the results.
    """
    print("Loading data and labels...")
    data, roi_labels, success_labels = load_data_and_labels()
    print(f"Data collected: {len(data)} entries")
    
    if data and roi_labels and success_labels:
        try:
            train_model(data, roi_labels, success_labels)
            print("Model training successful!")
            Prediction.start_predict()
        except Exception as e:
            print(f"Error during model training: {e}")
    else:
        print("No data available for training.")
