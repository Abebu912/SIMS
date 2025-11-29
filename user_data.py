import json
import os
import tkinter as tk
from tkinter import messagebox

class UserData:
    def __init__(self):
        self.filename = "user_data.json"
        print(f"Looking for file: {self.filename}")  # DEBUG
        self.users = self.load_data()
        self.create_superuser()  # Create superuser if doesn't exist
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
    
    def create_superuser(self):
        """Create a superuser if it doesn't exist"""
        superuser_username = "admin"
        superuser_password = "admin123"
        
        if superuser_username not in self.users:
            self.users[superuser_username] = {
                "password": superuser_password,
                "role": "superuser",
                "created_at": "system"
            }
            self.save_data()
            print(f"Superuser created: {superuser_username}")  # DEBUG
    
    def register(self, username, password):
        print(f"Trying to register: {username}")  # DEBUG
        if username in self.users:
            print("Username already exists!")  # DEBUG
            return False
        
        # Store user data with role
        self.users[username] = {
            "password": password,
            "role": "regular_user",
            "created_at": "user_created"
        }
        
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
        
        if username in self.users:
            user_data = self.users[username]
            # Check if it's old format (just password string) or new format (dictionary)
            if isinstance(user_data, dict):
                # New format with role
                if user_data["password"] == password:
                    print("Login successful!")  # DEBUG
                    return True, user_data.get("role", "regular_user")
            else:
                # Old format (just password string)
                if user_data == password:
                    print("Login successful!")  # DEBUG
                    # Convert to new format
                    self.users[username] = {
                        "password": password,
                        "role": "regular_user",
                        "created_at": "converted"
                    }
                    self.save_data()
                    return True, "regular_user"
        
        print("Login failed!")  # DEBUG
        return False, None

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
        
        # Superuser info
        info_label = tk.Label(self.root, text="Superuser: admin/admin123", 
                             font=("Arial", 8), fg="gray")
        info_label.pack(pady=10)
        
        # Focus on username field
        self.user_entry.focus()
    
    def do_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()
        
        print(f"Login clicked - Username: '{username}', Password: '{password}'")  # DEBUG
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both fields")
            return
        
        success, role = self.user_data.login(username, password)
        
        if success:
            if role == "superuser":
                messagebox.showinfo("Success", f"Welcome Superuser {username}!")
                self.show_superuser_dashboard(username)
            else:
                messagebox.showinfo("Success", f"Login successful! Welcome {username}!")
                self.show_user_dashboard(username)
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def show_user_dashboard(self, username):
        """Show regular user dashboard"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        title = tk.Label(self.root, text=f"Welcome {username}!", font=("Arial", 16))
        title.pack(pady=20)
        
        info = tk.Label(self.root, text="Regular User Dashboard")
        info.pack(pady=10)
        
        logout_btn = tk.Button(self.root, text="Logout", command=self.go_to_login, width=15)
        logout_btn.pack(pady=10)
    
    def show_superuser_dashboard(self, username):
        """Show superuser dashboard with admin features"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        title = tk.Label(self.root, text=f"Welcome Superuser {username}!", 
                        font=("Arial", 16), fg="red")
        title.pack(pady=20)
        
        # Superuser features
        features_label = tk.Label(self.root, text="Superuser Features:", 
                                 font=("Arial", 12, "bold"))
        features_label.pack(pady=5)
        
        # Show all users
        users_text = tk.Text(self.root, height=8, width=30)
        users_text.pack(pady=10)
        
        # Display all users
        users_text.insert(tk.END, "All Registered Users:\n")
        users_text.insert(tk.END, "-" * 20 + "\n")
        for user, data in self.user_data.users.items():
            if isinstance(data, dict):
                role = data.get("role", "regular_user")
                users_text.insert(tk.END, f"User: {user} | Role: {role}\n")
            else:
                users_text.insert(tk.END, f"User: {user} | Role: regular_user\n")
        
        users_text.config(state=tk.DISABLED)
        
        logout_btn = tk.Button(self.root, text="Logout", command=self.go_to_login, width=15)
        logout_btn.pack(pady=10)
    
    def go_to_register(self):
        print("Going to register page...")  # DEBUG
        RegisterPage(self.root, self.user_data)
    
    def go_to_login(self):
        LoginPage(self.root, self.user_data)

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
        
        # Prevent registering as superuser
        if username.lower() == "admin":
            messagebox.showerror("Error", "Cannot register as 'admin' - this is a reserved superuser account")
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
    root.title("Login System with Superuser")
    root.geometry("350x500")
    
    print("=== APPLICATION STARTED ===")  # DEBUG
    
    # Initialize user data (this loads existing data automatically)
    user_data = UserData()
    
    # Start with login page
    LoginPage(root, user_data)
    
    root.mainloop()

if __name__ == "__main__":
    main()