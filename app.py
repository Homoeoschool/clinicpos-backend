from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import sqlite3
import json
import csv
from io import StringIO

app = Flask(__name__)
CORS(app)  # Allow all origins. You can restrict if needed.

# Initialize or upgrade database
def init_db():
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    # Add name and op_number columns if missing
    try:
        c.execute("ALTER TABLE sales ADD COLUMN name TEXT")
    except:
        pass  # already exists
    try:
        c.execute("ALTER TABLE sales ADD COLUMN op_number TEXT")
    except:
        pass  # already exists
    # Create table if doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            op_number TEXT,
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
                <li>/sales (GET, filter: ?date=YYYY-MM-DD, ?month=MM&year=YYYY, ?year=YYYY)</li>
                <li>/export_csv (GET, same filters)</li>
            </ul>
        </p>
    '''

@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        data = request.get_json(force=True)
        name = data.get('name', '').strip()
        op_number = data.get('op_number', '').strip()
        cart = data.get('cart')
        total = data.get('total')
        discount = data.get('discount')
        if not all([name, op_number, cart, total is not None, discount is not None]):
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400

        conn = sqlite3.connect('sales.db')
        c = conn.cursor()
        c.execute(
            'INSERT INTO sales (name, op_number, cart_json, total, discount) VALUES (?, ?, ?, ?, ?)',
            (name, op_number, json.dumps(cart), total, discount)
        )
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/sales', methods=['GET'])
def sales():
    # Filters
    date_filter = request.args.get('date')
    month_filter = request.args.get('month')
    year_filter = request.args.get('year')

    query = 'SELECT id, name, op_number, cart_json, total, discount, timestamp FROM sales'
    params = []
    filters = []
    if date_filter:
        filters.append("date(timestamp) = ?")
        params.append(date_filter)
    if month_filter:
        filters.append("strftime('%m', timestamp) = ?")
        params.append(month_filter.zfill(2))
    if year_filter:
        filters.append("strftime('%Y', timestamp) = ?")
        params.append(year_filter)
    if filters:
        query += ' WHERE ' + ' AND '.join(filters)
    query += ' ORDER BY id DESC'

    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    sales_list = []
    for row in rows:
        sales_list.append({
            "id": row[0],
            "name": row[1],
            "op_number": row[2],
            "cart": json.loads(row[3]),
            "total": row[4],
            "discount": row[5],
            "timestamp": row[6]
        })
    return jsonify(sales_list)

@app.route('/export_csv', methods=['GET'])
def export_csv():
    # Same filters as /sales
    date_filter = request.args.get('date')
    month_filter = request.args.get('month')
    year_filter = request.args.get('year')

    query = 'SELECT id, name, op_number, cart_json, total, discount, timestamp FROM sales'
    params = []
    filters = []
    if date_filter:
        filters.append("date(timestamp) = ?")
        params.append(date_filter)
    if month_filter:
        filters.append("strftime('%m', timestamp) = ?")
        params.append(month_filter.zfill(2))
    if year_filter:
        filters.append("strftime('%Y', timestamp) = ?")
        params.append(year_filter)
    if filters:
        query += ' WHERE ' + ' AND '.join(filters)
    query += ' ORDER BY id DESC'

    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'OP Number', 'Cart', 'Total', 'Discount', 'Timestamp'])
    for row in rows:
        writer.writerow([
            row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        ])
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=sales_report.csv"}
    )

@app.route('/checkout', methods=['GET'])
def checkout_get_info():
    return "<h3>POST sales data to this endpoint to record a sale.</h3>"

if __name__ == "__main__":
    app.run(debug=True)
