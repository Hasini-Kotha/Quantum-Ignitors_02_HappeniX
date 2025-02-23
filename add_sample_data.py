import sqlite3

# Connect to the database
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Insert sample education workshops
c.execute("INSERT INTO workshops (title, description, date, type) VALUES (?, ?, ?, ?)",
          ('Python Basics', 'Learn the basics of Python programming.', '2023-11-15', 'education'))
c.execute("INSERT INTO workshops (title, description, date, type) VALUES (?, ?, ?, ?)",
          ('Web Development with Flask', 'Build web applications using Flask.', '2023-11-20', 'education'))

# Insert sample office workshops
c.execute("INSERT INTO workshops (title, description, date, type) VALUES (?, ?, ?, ?)",
          ('Board Meeting Q4', 'Quarterly board meeting for Q4.', '2023-11-25', 'office'))
c.execute("INSERT INTO workshops (title, description, date, type) VALUES (?, ?, ?, ?)",
          ('Leadership Training', 'Training workshop for leadership skills.', '2023-12-01', 'office'))

# Commit changes and close the connection
conn.commit()
conn.close()

print("Sample data added successfully!")