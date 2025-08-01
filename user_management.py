import sqlite3
import time
import hashlib

class UserManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.setup_database()
    
    def setup_database(self):
        """Setup the users table"""
        cursor = self.connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT,
                is_admin BOOLEAN DEFAULT 0
            )
        ''')
        self.connection.commit()
    
    def authenticate_user(self, username, password):
        """FIXED: Use parameterized queries to prevent SQL injection"""
        cursor = self.connection.cursor()
        hashed_password = self.hash_password(password)
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        result = cursor.fetchone()
        return result is not None
    
    def get_user_permissions(self, username):
        """FIXED: Proper error handling for non-existent users"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if result is None:
            raise ValueError(f"User '{username}' not found in database")
        
        return result[0]
    
    def find_users_by_prefix(self, prefix):
        """FIXED: Use database-level filtering for optimal performance"""
        cursor = self.connection.cursor()
        # Use SQL LIKE operator for efficient prefix matching
        cursor.execute("SELECT username FROM users WHERE username LIKE ? || '%'", (prefix,))
        results = cursor.fetchall()
        
        # Extract usernames from tuples
        return [user[0] for user in results]
    
    def hash_password(self, password):
        """Secure password hashing"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, password, email, is_admin=False):
        """Create a new user with hashed password"""
        hashed_password = self.hash_password(password)
        cursor = self.connection.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, password, email, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (username, hashed_password, email, is_admin))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def close(self):
        """Close database connection"""
        self.connection.close()


# Example usage demonstrating the bugs
if __name__ == "__main__":
    user_mgr = UserManager("users.db")
    
    # Create some test users
    user_mgr.create_user("admin", "password123", "admin@example.com", True)
    user_mgr.create_user("john_doe", "mypassword", "john@example.com", False)
    user_mgr.create_user("jane_smith", "secret456", "jane@example.com", False)
    
    # Test secure authentication (SQL injection now prevented)
    print("Testing authentication...")
    print(user_mgr.authenticate_user("admin", "password123"))  # Normal case
    print(user_mgr.authenticate_user("admin' OR '1'='1", "anything"))  # Now returns False
    
    # Test proper error handling for non-existent users
    try:
        print(user_mgr.get_user_permissions("nonexistent_user"))
    except ValueError as e:
        print(f"Handled error properly: {e}")
    
    # Performance issue with large datasets
    print("Finding users with prefix 'j'...")
    start_time = time.time()
    results = user_mgr.find_users_by_prefix("j")
    end_time = time.time()
    print(f"Found users: {results}")
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    
    user_mgr.close()