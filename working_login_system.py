import json
import os
import tkinter as tk
from tkinter import messagebox

class UserManager:
    def __init__(self):
        self.data_file = "users.json"
        self.users = self.load_users()
        self.create_default_admin()
    
    def load_users(self):
        """Load users from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as file:
                    return json.load(file)
            return {}
        except:
            return {}
    
    def save_users(self):
        """Save users to JSON file"""
        try:
            with open(self.data_file, 'w') as file:
                json.dump(self.users, file, indent=2)
            return True
        except:
            return False
    
    def create_default_admin(self):
        """Create default admin account if it doesn't exist"""
        if "admin" not in self.users:
            self.users["admin"] = {
                "password": "admin123",
                "role": "superuser",
                "email": "admin@system.com"
            }
            self.save_users()
    
    def register_user(self, username, password, email=""):
        """Register a new user"""
        if username in self.users:
            return False, "Username already exists!"
        
        self.users[username] = {
            "password": password,
            "role": "user",
            "email": email
        }
        
        if self.save_users():
            return True, "Registration successful!"
        else:
            if username in self.users:
                del self.users[username]
            return False, "Registration failed!"
    
    def login_user(self, username, password):
        """Login user"""
        if username not in self.users:
            return False, "User not found!"
        
        user_data = self.users[username]
        
        # Handle both string password (old format) and dict (new format)
        if isinstance(user_data, dict):
            if user_data["password"] == password:
                return True, f"Welcome {username}!"
            else:
                return False, "Wrong password!"
        else:
            # Old format where password was stored as string
            if user_data == password:
                return True, f"Welcome {username}!"
            else:
                return False, "Wrong password!"

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Login System - WORKING VERSION")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        
        # Center the window
        self.center_window()
        
        self.user_manager = UserManager()
        self.show_login_page()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def clear_window(self):
        """Clear all widgets from window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_login_page(self):
        """Show login page"""
        self.clear_window()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="USER LOGIN", font=('Arial', 20, 'bold'), 
                              bg='white', fg='#2c3e50')
        title_label.pack(pady=(0, 30))
        
        # Username
        username_frame = tk.Frame(main_frame, bg='white')
        username_frame.pack(fill='x', pady=10)
        
        tk.Label(username_frame, text="Username:", font=('Arial', 12), 
                bg='white').pack(anchor='w')
        self.login_username = tk.Entry(username_frame, font=('Arial', 12), 
                                      width=25, relief='solid', bd=1)
        self.login_username.pack(fill='x', pady=(5, 0))
        self.login_username.focus()
        
        # Password
        password_frame = tk.Frame(main_frame, bg='white')
        password_frame.pack(fill='x', pady=10)
        
        tk.Label(password_frame, text="Password:", font=('Arial', 12), 
                bg='white').pack(anchor='w')
        self.login_password = tk.Entry(password_frame, font=('Arial', 12), 
                                      width=25, show='*', relief='solid', bd=1)
        self.login_password.pack(fill='x', pady=(5, 0))
        
        # Bind Enter key to login
        self.login_password.bind('<Return>', lambda e: self.handle_login())
        
        # Login button
        login_btn = tk.Button(main_frame, text="LOGIN", font=('Arial', 12, 'bold'),
                             bg='#3498db', fg='white', relief='flat',
                             command=self.handle_login, width=20, height=2)
        login_btn.pack(pady=20)
        
        # Register link
        register_btn = tk.Button(main_frame, text="Don't have an account? Register here", 
                                font=('Arial', 10), bg='white', fg='#3498db',
                                relief='flat', command=self.show_register_page)
        register_btn.pack(pady=10)
        
        # Admin info
        admin_info = tk.Label(main_frame, 
                             text="Default Admin: admin / admin123",
                             font=('Arial', 9), bg='white', fg='#7f8c8d')
        admin_info.pack(pady=(20, 0))
    
    def show_register_page(self):
        """Show registration page"""
        self.clear_window()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="CREATE ACCOUNT", font=('Arial', 20, 'bold'), 
                              bg='white', fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # Username
        username_frame = tk.Frame(main_frame, bg='white')
        username_frame.pack(fill='x', pady=8)
        
        tk.Label(username_frame, text="Username:", font=('Arial', 12), 
                bg='white').pack(anchor='w')
        self.reg_username = tk.Entry(username_frame, font=('Arial', 12), 
                                    width=25, relief='solid', bd=1)
        self.reg_username.pack(fill='x', pady=(5, 0))
        self.reg_username.focus()
        
        # Email
        email_frame = tk.Frame(main_frame, bg='white')
        email_frame.pack(fill='x', pady=8)
        
        tk.Label(email_frame, text="Email (optional):", font=('Arial', 12), 
                bg='white').pack(anchor='w')
        self.reg_email = tk.Entry(email_frame, font=('Arial', 12), 
                                 width=25, relief='solid', bd=1)
        self.reg_email.pack(fill='x', pady=(5, 0))
        
        # Password
        password_frame = tk.Frame(main_frame, bg='white')
        password_frame.pack(fill='x', pady=8)
        
        tk.Label(password_frame, text="Password:", font=('Arial', 12), 
                bg='white').pack(anchor='w')
        self.reg_password = tk.Entry(password_frame, font=('Arial', 12), 
                                    width=25, show='*', relief='solid', bd=1)
        self.reg_password.pack(fill='x', pady=(5, 0))
        
        # Confirm Password
        confirm_frame = tk.Frame(main_frame, bg='white')
        confirm_frame.pack(fill='x', pady=8)
        
        tk.Label(confirm_frame, text="Confirm Password:", font=('Arial', 12), 
                bg='white').pack(anchor='w')
        self.reg_confirm = tk.Entry(confirm_frame, font=('Arial', 12), 
                                   width=25, show='*', relief='solid', bd=1)
        self.reg_confirm.pack(fill='x', pady=(5, 0))
        
        # Bind Enter key to register
        self.reg_confirm.bind('<Return>', lambda e: self.handle_register())
        
        # Register button
        register_btn = tk.Button(main_frame, text="CREATE ACCOUNT", 
                               font=('Arial', 12, 'bold'), bg='#27ae60', fg='white',
                               relief='flat', command=self.handle_register, 
                               width=20, height=2)
        register_btn.pack(pady=20)
        
        # Back to login
        back_btn = tk.Button(main_frame, text="Back to Login", 
                           font=('Arial', 10), bg='white', fg='#e74c3c',
                           relief='flat', command=self.show_login_page)
        back_btn.pack(pady=10)
    
    def handle_login(self):
        """Handle login process"""
        username = self.login_username.get().strip()
        password = self.login_password.get()
        
        # Validation
        if not username:
            messagebox.showerror("Error", "Please enter username!")
            self.login_username.focus()
            return
        
        if not password:
            messagebox.showerror("Error", "Please enter password!")
            self.login_password.focus()
            return
        
        # Attempt login
        success, message = self.user_manager.login_user(username, password)
        
        if success:
            messagebox.showinfo("Success", message)
            self.show_dashboard(username)
        else:
            messagebox.showerror("Error", message)
            self.login_password.delete(0, tk.END)
            self.login_password.focus()
    
    def handle_register(self):
        """Handle registration process"""
        username = self.reg_username.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_password.get()
        confirm_password = self.reg_confirm.get()
        
        # Validation
        if not username:
            messagebox.showerror("Error", "Please enter username!")
            self.reg_username.focus()
            return
        
        if len(username) < 3:
            messagebox.showerror("Error", "Username must be at least 3 characters!")
            self.reg_username.focus()
            return
        
        if not password:
            messagebox.showerror("Error", "Please enter password!")
            self.reg_password.focus()
            return
        
        if len(password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters!")
            self.reg_password.focus()
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match!")
            self.reg_confirm.delete(0, tk.END)
            self.reg_confirm.focus()
            return
        
        # Prevent admin registration
        if username.lower() == "admin":
            messagebox.showerror("Error", "Username 'admin' is reserved!")
            self.reg_username.delete(0, tk.END)
            self.reg_username.focus()
            return
        
        # Attempt registration
        success, message = self.user_manager.register_user(username, password, email)
        
        if success:
            messagebox.showinfo("Success", message)
            self.show_login_page()
        else:
            messagebox.showerror("Error", message)
            self.reg_username.focus()
    
    def show_dashboard(self, username):
        """Show user dashboard after login"""
        self.clear_window()
        
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Welcome message
        welcome_label = tk.Label(main_frame, 
                               text=f"Welcome, {username}!",
                               font=('Arial', 18, 'bold'), bg='white', fg='#2c3e50')
        welcome_label.pack(pady=20)
        
        # User info
        info_label = tk.Label(main_frame, 
                            text="You have successfully logged in!",
                            font=('Arial', 12), bg='white', fg='#7f8c8d')
        info_label.pack(pady=10)
        
        # Logout button
        logout_btn = tk.Button(main_frame, text="LOGOUT", 
                             font=('Arial', 12, 'bold'), bg='#e74c3c', fg='white',
                             relief='flat', command=self.show_login_page,
                             width=15, height=2)
        logout_btn.pack(pady=30)

def main():
    # Create and run the application
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()