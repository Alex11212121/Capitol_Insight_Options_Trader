import requests
import sqlite3
import datetime
import time

API_KEY = 'XXXXXXXXXXXXXXXXX'  # replace with your key
BASE_URL = "https://api.govinfo.gov/v1/"
DATABASE_NAME = "congress.db"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

def setup_database():
    conn = sqlite3.connect("congress.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bills (
        bill_id TEXT PRIMARY KEY,
        title TEXT,
        summary TEXT,
        sponsor_id TEXT,
        sponsor_name TEXT,
        bill_type TEXT,
        introduction_date TEXT,
        congress INTEGER,
        chamber TEXT,
        uploaded_date DATETIME,
        LDA_trained INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

def insert_bill_into_db(bill):
    conn = sqlite3.connect("congress.db")
    cursor = conn.cursor()

    # Adjusted the check for duplicates as per the new data structure
    cursor.execute("SELECT * FROM bills WHERE bill_id=?", (bill["packageId"],))
    if cursor.fetchone():
        return

    current_time = datetime.datetime.now()

    cursor.execute("""
    INSERT INTO bills (bill_id, title, summary, uploaded_date)
    VALUES (?, ?, ?, ?)
    """, (
        bill["packageId"],
        bill["title"],
        bill.get("summary", ""),  
        current_time
    ))

    conn.commit()
    conn.close()

def get_bill_details(packageId):
    """Fetch specific details of a bill."""
    url = f"{BASE_URL}packages/{packageId}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def get_recent_bills():
    """Fetch the list of recent bills."""
    date_range = datetime.datetime.now().strftime('%Y-%m-%d')  
    url = f"{BASE_URL}collections/BILLS/NAID/granules?offset=0&pageSize=100&date={date_range}"  

    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return response.json()["granules"]  
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def main():
    setup_database()

    while True:
        bill_list = get_recent_bills()

        if bill_list:
            for bill in bill_list:
                bill_details = get_bill_details(bill["packageId"])
                if bill_details:
                    insert_bill_into_db(bill_details)
                    print(f"Added {bill_details['title']} to the database.")

        print("Sleeping for 6 hours...")
        time.sleep(6 * 60 * 60)

if __name__ == "__main__":
    main()
