# Example: Custom Account Generation
# This file shows different ways to generate accounts instead of random generation

import random

# ============================================
# EXAMPLE 1: Load from Text File
# ============================================
def load_from_file(filename="accounts.txt"):
    """
    Read accounts from a text file
    Format: username:password (one per line)
    """
    try:
        with open(filename, 'r') as f:
            accounts = [line.strip() for line in f if ':' in line]
        
        if not accounts:
            return None, None, None
        
        # Get random account and remove it from file
        account = random.choice(accounts)
        username, password = account.split(':', 1)
        combo = account
        
        # Remove used account from file
        accounts.remove(account)
        with open(filename, 'w') as f:
            f.write('\n'.join(accounts))
        
        return username, password, combo
    except FileNotFoundError:
        print(f"File {filename} not found!")
        return None, None, None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None, None, None


# ============================================
# EXAMPLE 2: Load from Database (SQLite)
# ============================================
def load_from_database():
    """
    Load account from SQLite database
    You'll need to create the database first
    """
    import sqlite3
    
    try:
        conn = sqlite3.connect('accounts.db')
        cursor = conn.cursor()
        
        # Get a random unused account
        cursor.execute("""
            SELECT id, username, password 
            FROM accounts 
            WHERE used = 0 
            ORDER BY RANDOM() 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return None, None, None
        
        account_id, username, password = result
        combo = f"{username}:{password}"
        
        # Mark as used
        cursor.execute("UPDATE accounts SET used = 1 WHERE id = ?", (account_id,))
        conn.commit()
        conn.close()
        
        return username, password, combo
    except Exception as e:
        print(f"Database error: {e}")
        return None, None, None


# ============================================
# EXAMPLE 3: API Integration
# ============================================
def load_from_api():
    """
    Get account from an external API
    Replace with your actual API endpoint
    """
    import requests
    
    try:
        response = requests.get("https://your-api.com/generate-account")
        if response.status_code == 200:
            data = response.json()
            username = data.get('username')
            password = data.get('password')
            combo = f"{username}:{password}"
            return username, password, combo
        else:
            print(f"API error: {response.status_code}")
            return None, None, None
    except Exception as e:
        print(f"API request failed: {e}")
        return None, None, None


# ============================================
# HOW TO USE IN YOUR BOT
# ============================================
"""
In discord_formatter_bot.py, replace the generation section in the 
/generate command with one of these methods:

# Original (random generation):
username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))
combo = f"{username}:{password}"

# Replace with:

# Option 1: File-based
username, password, combo = load_from_file("accounts.txt")
if not username:
    await interaction.response.send_message("❌ No accounts available!", ephemeral=True)
    return

# Option 2: Database-based
username, password, combo = load_from_database()
if not username:
    await interaction.response.send_message("❌ No accounts available!", ephemeral=True)
    return

# Option 3: API-based
username, password, combo = load_from_api()
if not username:
    await interaction.response.send_message("❌ Failed to generate account!", ephemeral=True)
    return
"""

# ============================================
# CREATING THE DATABASE (Run this once)
# ============================================
def create_database():
    """
    Create the accounts database
    Run this once to set up the database
    """
    import sqlite3
    
    conn = sqlite3.connect('accounts.db')
    cursor = conn.cursor()
    
    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Example: Add some accounts
    sample_accounts = [
        ('user1', 'pass1'),
        ('user2', 'pass2'),
        ('user3', 'pass3'),
    ]
    
    cursor.executemany(
        "INSERT INTO accounts (username, password) VALUES (?, ?)",
        sample_accounts
    )
    
    conn.commit()
    conn.close()
    print("Database created successfully!")

# Uncomment to create database:
# create_database()
