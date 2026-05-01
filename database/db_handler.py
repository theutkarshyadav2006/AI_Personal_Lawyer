import sqlite3

def get_connection():
    conn = sqlite3.connect("legal_cases.db")
    return conn