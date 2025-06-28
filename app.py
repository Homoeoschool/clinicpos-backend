from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json

app = Flask(__name__)
CORS(app)


# Initialize SQLite database (creates sales.db if not present)
def init_db():
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cart_json TEXT,
            total REAL,
            discount REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET'])
def home():
    return '''
        <h2>Clinic POS backend is running!</h2>
        <p>Endpoints:
            <ul>
                <li>/checkout (POST)</li>
                <li>/sales (GET)</li>
            </ul>
        </p>
    '''

@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        data = request.get_json(force=True)
        cart = data.get('cart')
        total = data.get('total')
        discount = data.get('discount')
        if cart is None or total is None or discount is None:
            return jsonify({'status': 'error', 'message': 'Missing cart, total, or discount'}), 400

        conn = sqlite3.connect('sales.db')
        c = conn.cursor()
        c.execute(
            'INSERT INTO sales (cart_json, total, discount) VALUES (?, ?, ?)',
            (json.dumps(cart), total, discount)
        )
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/sales', methods=['GET'])
def sales():
    try:
        conn = sqlite3.connect('sales.db')
        c = conn.cursor()
        c.execute('SELECT id, cart_json, total, discount, timestamp FROM sales ORDER BY id DESC')
        rows = c.fetchall()
        conn.close()
        sales_list = []
        for row in rows:
            sales_list.append({
                "id": row[0],
                "cart": json.loads(row[1]),
                "total": row[2],
                "discount": row[3],
                "timestamp": row[4]
            })
        return jsonify(sales_list)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Optional: Helpful info if someone tries GET on /checkout
@app.route('/checkout', methods=['GET'])
def checkout_get_info():
    return "<h3>POST sales data to this endpoint to record a sale.</h3>"

if __name__ == "__main__":
    app.run(debug=True)
	