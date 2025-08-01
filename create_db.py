import sqlite3

# Connect (or create) the users database
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Drop the old users table (if it exists)
c.execute('DROP TABLE IF EXISTS users')

# Create the new users table using email instead of username
c.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_subscriber INTEGER DEFAULT 0
)
''')

conn.commit()
conn.close()

print("✅ users.db recreated with email-only authentication.")