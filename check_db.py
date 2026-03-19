import sqlite3

def check_admin():
    conn = sqlite3.connect('c:/Users/JEFFY D MARTIN/Desktop/OrphanageFoodProject/account.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name LIKE '%admin%' OR email LIKE '%admin%'")
    rows = cursor.fetchall()
    print("Admin related users:")
    for row in rows:
        print(row)
    conn.close()

if __name__ == "__main__":
    check_admin()
