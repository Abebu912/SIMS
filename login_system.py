import json
import os
import tkinter as tk
from tkinter import messagebox

class UserData:
    def __init__(self):
        self.filename = "user_data.json"
        print(f"Looking for file: {self.filename}")  # DEBUG
        self.users = self.load_data()
        print(f"Loaded users: {self.users}")  # DEBUG
    
    def load_data(self):
        if os.path.exists(self.filename):
            print("File exists! Loading data...")  # DEBUG
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    print(f"Data loaded: {data}")  # DEBUG
                    return data
            except Exception as e:
                print(f"Error loading file: {e}")  # DEBUG
                return {}
        else:
            print("File does not exist, starting fresh")  # DEBUG
            return {}
    
    def save_data(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.users, f)
            print(f"Data saved: {self.users}")  # DEBUG
            return True
        except Exception as e:
            print(f"Error saving: {e}")  # DEBUG
            return False
    
    def register(self, username, password):
        print(f"Trying to register: {username}")  # DEBUG
        if username in self.users:
            print("Username already exists!")  # DEBUG
            return False
        self.users[username] = password
        if self.save_data():
            print("Registration successful!")  # DEBUG
            return True
        else:
            print("Registration failed to save!")  # DEBUG
            # Remove from memory if save failed
            if username in self.users:
                del self.users[username]
            return False
    
    def login(self, username, password):
        print(f"Login attempt: {username}")  # DEBUG
        print(f"Available users: {self.users}")  # DEBUG
        if username in self.users and self.users[username] == password:
            print("Login successful!")  # DEBUG
            return True
        print("Login failed!")  # DEBUG
        return False

class LoginPage:
    def __init__(self, root, user_data):
        self.root = root
        self.user_data = user_data
        self.create_login_page()
    
    def create_login_page(self):
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        print("Creating login page...")  # DEBUG
        
        # Login title
        title = tk.Label(self.root, text="LOGIN", font=("Arial", 16))
        title.pack(pady=20)
        
        # Username
        user_label = tk.Label(self.root, text="Username:")
        user_label.pack()
        self.user_entry = tk.Entry(self.root, width=20)
        self.user_entry.pack(pady=5)
        
        # Password
        pass_label = tk.Label(self.root, text="Password:")
        pass_label.pack()
        self.pass_entry = tk.Entry(self.root, width=20, show="*")
        self.pass_entry.pack(pady=5)
        
        # Login button
        login_btn = tk.Button(self.root, text="Login", command=self.do_login, width=15)
        login_btn.pack(pady=10)
        
        # Register button
        reg_btn = tk.Button(self.root, text="Go to Register", command=self.go_to_register, width=15)
        reg_btn.pack(pady=5)
        
        # Focus on username field
        self.user_entry.focus()
    
    def do_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()
        
        print(f"Login clicked - Username: '{username}', Password: '{password}'")  # DEBUG
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both fields")
            return
        
        if self.user_data.login(username, password):
            messagebox.showinfo("Success", "Login successful!")
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def go_to_register(self):
        print("Going to register page...")  # DEBUG
        RegisterPage(self.root, self.user_data)

class RegisterPage:
    def __init__(self, root, user_data):
        self.root = root
        self.user_data = user_data
        self.create_register_page()
    
    def create_register_page(self):
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        print("Creating register page...")  # DEBUG
        
        # Register title
        title = tk.Label(self.root, text="REGISTER", font=("Arial", 16))
        title.pack(pady=20)
        
        # Username
        user_label = tk.Label(self.root, text="Username:")
        user_label.pack()
        self.user_entry = tk.Entry(self.root, width=20)
        self.user_entry.pack(pady=5)
        
        # Password
        pass_label = tk.Label(self.root, text="Password:")
        pass_label.pack()
        self.pass_entry = tk.Entry(self.root, width=20, show="*")
        self.pass_entry.pack(pady=5)
        
        # Confirm Password
        confirm_label = tk.Label(self.root, text="Confirm Password:")
        confirm_label.pack()
        self.confirm_entry = tk.Entry(self.root, width=20, show="*")
        self.confirm_entry.pack(pady=5)
        
        # Register button
        reg_btn = tk.Button(self.root, text="Register", command=self.do_register, width=15)
        reg_btn.pack(pady=10)
        
        # Back to login button
        back_btn = tk.Button(self.root, text="Back to Login", command=self.go_to_login, width=15)
        back_btn.pack(pady=5)
        
        # Focus on username field
        self.user_entry.focus()
    
    def do_register(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()
        confirm = self.confirm_entry.get()
        
        print(f"Register clicked - Username: '{username}', Password: '{password}', Confirm: '{confirm}'")  # DEBUG
        
        if not username or not password or not confirm:
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords don't match")
            return
        
        if len(username) < 3:
            messagebox.showerror("Error", "Username must be at least 3 characters")
            return
        
        if len(password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters")
            return
        
        if self.user_data.register(username, password):
            messagebox.showinfo("Success", "Registration successful!")
            self.go_to_login()
        else:
            messagebox.showerror("Error", "Username already exists")
    
    def go_to_login(self):
        print("Going back to login page...")  # DEBUG
        LoginPage(self.root, self.user_data)

# Main application
def main():
    root = tk.Tk()
    root.title("Login System - DEBUG VERSION")
    root.geometry("300x400")
    
    print("=== APPLICATION STARTED ===")  # DEBUG
    
    # Initialize user data (this loads existing data automatically)
    user_data = UserData()
    
    # Start with login page
    LoginPage(root, user_data)
    
    root.mainloop()

if __name__ == "__main__":
    main()