import tkinter as tk
from tkinter import messagebox
import alpaca_trade_api as tradeapi
import DataCollection

class LoginPage(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TradeScout Login")
        self.geometry("330x150")
        self.configure(bg="silver")
        
        # Labels and Entry fields for API Key and Secret Key
        tk.Label(self, text="API Key:", bg="silver").grid(row=0, column=0, padx=15, pady=15, sticky='e')
        self.api_key_entry = tk.Entry(self, width=30)
        self.api_key_entry.grid(row=0, column=1, padx=15, pady=15)
        
        tk.Label(self, text="Secret Key:", bg="silver").grid(row=1, column=0, padx=15, pady=15, sticky='e')
        self.secret_key_entry = tk.Entry(self, show='*', width=30)
        self.secret_key_entry.grid(row=1, column=1, padx=15, pady=15)
        
        # Login button
        tk.Button(self, text="Login", command=self.authenticate, bg="white").grid(row=2, columnspan=2, pady=5)
    
    def authenticate(self):
        api_key = self.api_key_entry.get()
        secret_key = self.secret_key_entry.get()
        
        # Attempt to authenticate with Alpaca
        try:
            self.api = tradeapi.REST(api_key, secret_key, base_url='https://paper-api.alpaca.markets')
            account = self.api.get_account()
            if account.status == "ACTIVE":
                messagebox.showinfo("Login Success", "Successfully authenticated!")
                self.destroy()  # Close login window
                
                # Call the DataCollection module after successful login
                DataCollection.start_data_collection(self.api)  # Assuming the function to start the process is named `start_data_collection`
            else:
                messagebox.showerror("Login Failed", "Unable to authenticate with Alpaca.")
        except Exception as e:
            messagebox.showerror("Login Failed", str(e))

# Run the login page
if __name__ == "__main__":
    login_page = LoginPage()
    login_page.mainloop()
