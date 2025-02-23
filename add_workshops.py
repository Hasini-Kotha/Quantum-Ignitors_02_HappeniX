import sqlite3

# Connect to the database
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Insert more workshops
c.execute("INSERT INTO workshops (title, description, date) VALUES (?, ?, ?)",
          ('Advanced Python', 'Learn advanced Python concepts.', '2023-12-01 10:00'))
c.execute("INSERT INTO workshops (title, description, date) VALUES (?, ?, ?)",
          ('Machine Learning Basics', 'Introduction to machine learning.', '2023-12-05 14:00'))
c.execute("INSERT INTO workshops (title, description, date) VALUES (?, ?, ?)",
          ('Cloud Computing with AWS', 'Learn how to use AWS for cloud computing.', '2023-12-10 09:00'))

# Commit changes and close the connection
conn.commit()
conn.close()