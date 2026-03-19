import sqlite3

def delete_admin():
    conn = sqlite3.connect('c:/Users/JEFFY D MARTIN/Desktop/OrphanageFoodProject/account.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE name LIKE '%admin%' OR email LIKE '%admin%'")
    print(f"Deleted {cursor.rowcount} admin-related users.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    delete_admin()
