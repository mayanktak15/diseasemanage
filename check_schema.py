from app import app, db
import sqlite3

# Create database
with app.app_context():
    db.create_all()
    print('✓ Database created successfully!\n')

# Check schema
conn = sqlite3.connect('instance/docify.db')
cursor = conn.cursor()

# User table
cursor.execute('PRAGMA table_info(user)')
print('=' * 70)
print('USER TABLE SCHEMA')
print('=' * 70)
print(f"{'Column':<25} {'Type':<20} {'Nullable':<10}")
print('-' * 70)
for row in cursor.fetchall():
    col_name = row[1]
    col_type = row[2]
    nullable = 'Yes' if not row[3] else 'No'
    print(f'{col_name:<25} {col_type:<20} {nullable:<10}')

# Consultation table
cursor.execute('PRAGMA table_info(consultation)')
print('\n' + '=' * 70)
print('CONSULTATION TABLE SCHEMA')
print('=' * 70)
print(f"{'Column':<25} {'Type':<20} {'Nullable':<10}")
print('-' * 70)
for row in cursor.fetchall():
    col_name = row[1]
    col_type = row[2]
    nullable = 'Yes' if not row[3] else 'No'
    print(f'{col_name:<25} {col_type:<20} {nullable:<10}')

conn.close()
print('\n✓ Schema check complete!')
