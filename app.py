from flask import Flask, request, jsonify
import sqlite3
import json

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cart_json TEXT,
            total REAL,
            discount REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    cart = data.get('cart')
    total = data.get('total')
    discount = data.get('discount')
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute('INSERT INTO sales (cart_json, total, discount) VALUES (?, ?, ?)',
              (json.dumps(cart), total, discount))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/sales', methods=['GET'])
def sales():
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute('SELECT id, cart_json, total, discount FROM sales ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    sales_list = []
    for row in rows:
        sales_list.append({
            "id": row[0],
            "cart": json.loads(row[1]),
            "total": row[2],
            "discount": row[3]
        })
    return jsonify(sales_list)

if __name__ == "__main__":
    app.run(debug=True)
