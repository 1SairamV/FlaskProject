from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
db_name = 'D:\COMPUTER SCIENCE\VS Programming\HB Assignment\Library2.db'

# Function to get the current number of available copies for a given book_id
def get_available_books(book_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Get total available copies from BOOK_MASTER
    cursor.execute("SELECT book_copies FROM BOOK_MASTER WHERE book_id=?", (book_id,))
    total_copies = cursor.fetchone()
    
    if total_copies is None:
        conn.close()
        return None  # Book not found
    
    total_copies = total_copies[0]

    # Get the number of books already borrowed for the given book_id
    cursor.execute("SELECT COUNT(*) FROM ORDER_TABLE WHERE book_id=? AND order_isActive=1", (book_id,))
    borrowed_count = cursor.fetchone()[0]

    # Get the number of books returned for the given book_id
    cursor.execute("SELECT COUNT(*) FROM RETURN_TABLE WHERE book_id=?", (book_id,))
    returned_count = cursor.fetchone()[0]

    # Calculate the current available copies
    available_copies = total_copies + returned_count - borrowed_count
    conn.close()
    return available_copies

# Function to check if the user is eligible to borrow a "Crime" genre book based on age
def is_eligible_for_crime_genre(cust_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Get the customer's age
    cursor.execute("SELECT cust_age FROM CUSTOMER_MASTER WHERE cust_id=?", (cust_id,))
    age = cursor.fetchone()
    
    conn.close()
    if age is None:
        return False  # Customer not found
    
    return age[0] >= 18  # Return True if age is 18 or older

@app.route('/order', methods=['POST'])
def order_book():
    data = request.json
    cust_id = data.get('cust_id')
    book_id = data.get('book_id')

    if not cust_id or not book_id:
        return jsonify({"message": "Customer ID and Book ID are required."}), 400

    # Check if the book exists and get available copies
    available_copies = get_available_books(book_id)
    if available_copies is None:
        return jsonify({"message": "Book not found."}), 404

    if available_copies > 0:
        # Check if the book is of the "Crime" genre and if the user is eligible
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT catg_id FROM BOOK_MASTER WHERE book_id=?", (book_id,))
        catg_id = cursor.fetchone()

        if catg_id is None:
            conn.close()
            return jsonify({"message": "Book not found in category."}), 404

        cursor.execute("SELECT catg_name FROM CATEGORY_MASTER WHERE catg_id=?", (catg_id[0],))
        genre = cursor.fetchone()
        conn.close()

        if genre and genre[0].lower() == 'crime':
            if not is_eligible_for_crime_genre(cust_id):
                return jsonify({"message": "User is not eligible to borrow Crime genre books. Age restriction applies."}), 403

        return jsonify({"message": f"Book with ID {book_id} is available for borrowing. Current available copies: {available_copies}"}), 200
    else:
        return jsonify({"message": f"Book with ID {book_id} is currently unavailable."}), 400

@app.route('/return', methods=['POST'])
def return_book():
    data = request.json
    cust_id = data.get('cust_id')
    book_id = data.get('book_id')

    if not cust_id or not book_id:
        return jsonify({"message": "Customer ID and Book ID are required."}), 400

    # Check if the book exists and return success message
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM ORDER_TABLE WHERE cust_id=? AND book_id=? AND order_isActive=1", (cust_id, book_id))
    borrowed_count = cursor.fetchone()[0]

    if borrowed_count > 0:
        # Mark the book as returned in the RETURN_TABLE
        cursor.execute("INSERT INTO RETURN_TABLE (cust_id, book_id, return_date) VALUES (?, ?, ?)",
                       (cust_id, book_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return jsonify({"message": "Book successfully returned. Thank you!"}), 200
    else:
        conn.close()
        return jsonify({"message": "The book was not borrowed or does not exist."}), 400

if __name__ == '_main_':
    app.run(debug=True)