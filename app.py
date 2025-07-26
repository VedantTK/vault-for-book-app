from flask import Flask, request, render_template_string, redirect, url_for
import configparser
import hvac
import psycopg2

app = Flask(__name__)

# Load Vault and DB config
config = configparser.ConfigParser()
config.read('config.ini')

vault = hvac.Client(
    url=config['Vault']['vault_addr'],
    token=config['Vault']['vault_token']
)

db_secret_path = f"{config['Vault']['db_path']}/{config['Vault']['db_role']}"

def get_db_connection():
    secret = vault.read(db_secret_path)['data']
    username = secret['username']
    password = secret['password']

    conn = psycopg2.connect(
        host=config['Database']['host'],
        port=config['Database']['port'],
        dbname=config['Database']['dbname'],
        user=username,
        password=password
    )
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, author, price, image_url FROM books LIMIT 3")
    books = cur.fetchall()
    cur.close()
    conn.close()

    home_template = '''
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Vedant's Book Haven</title>
      <script src="https://cdn.tailwindcss.com"></script>
      <style>
        .card {
          transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .card:hover {
          transform: translateY(-5px);
          box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
        }
        .btn {
          transition: background-color 0.3s ease;
        }
        .btn:hover {
          background-color: #1e40af;
        }
      </style>
    </head>
    <body class="bg-gray-100 min-h-screen flex flex-col">
      <nav class="bg-indigo-600 text-white p-4 sticky top-0 z-10 shadow-md">
        <div class="container mx-auto flex justify-between items-center">
          <h1 class="text-2xl font-bold">Book Haven</h1>
          <div class="space-x-6">
            <a href="/" class="hover:underline">Home</a>
            <a href="#" class="hover:underline">About</a>
            <a href="#" class="hover:underline">Contact</a>
          </div>
        </div>
      </nav>

      <main class="container mx-auto py-8 flex-grow">
        <h2 class="text-3xl font-semibold text-center text-gray-800 mb-8">Welcome to Your Book Haven</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {% for book in books %}
            <div class="card bg-white rounded-lg shadow-md p-6">
              <img src="{{ book[4] }}" alt="{{ book[1] }}" class="w-full h-48 object-cover rounded-md mb-4">
              <h3 class="text-xl font-semibold text-gray-800">{{ book[1] }}</h3>
              <p class="text-gray-600">Author: {{ book[2] }}</p>
              <p class="text-gray-600 font-bold">Price: ${{ book[3] }}</p>
              <a href="{{ url_for('buy_book', book_id=book[0]) }}" class="btn inline-block mt-4 px-6 py-2 bg-indigo-600 text-white rounded-md">Buy Now</a>
            </div>
          {% endfor %}
        </div>
      </main>

      <footer class="bg-gray-800 text-white text-center py-4">
        <p>&copy; 2025 Vedant's Book Haven | All Rights Reserved</p>
      </footer>
    </body>
    </html>
    '''
    return render_template_string(home_template, books=books)

@app.route('/buy/<int:book_id>', methods=['GET', 'POST'])
def buy_book(book_id):
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        quantity = int(request.form['quantity'])

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO customers (name, email, phone, address, book_id, quantity)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, email, phone, address, book_id, quantity))
            conn.commit()
            cur.close()
            conn.close()
            return '''
            <!doctype html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>Order Confirmation</title>
              <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-100 min-h-screen flex items-center justify-center">
              <div class="bg-white p-8 rounded-lg shadow-md text-center">
                <h3 class="text-2xl font-semibold text-gray-800">Thank you, {}!</h3>
                <p class="text-gray-600 mt-2">Your order has been placed successfully.</p>
                <a href="/" class="mt-4 inline-block px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">Return to Home</a>
              </div>
            </body>
            </html>
            '''.format(name)
        except Exception as e:
            return '''
            <!doctype html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>Error</title>
              <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-100 min-h-screen flex items-center justify-center">
              <div class="bg-white p-8 rounded-lg shadow-md text-center">
                <h3 class="text-2xl font-semibold text-red-600">Error</h3>
                <p class="text-gray-600 mt-2">{}</p>
                <a href="/" class="mt-4 inline-block px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">Return to Home</a>
              </div>
            </body>
            </html>
            '''.format(str(e))

    form_html = '''
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Buy Book</title>
      <script src="https://cdn.tailwindcss.com"></script>
      <style>
        input, textarea {
          transition: border-color 0.3s ease;
        }
        input:focus, textarea:focus {
          border-color: #4f46e5;
          outline: none;
        }
        .btn:hover {
          background-color: #1e40af;
        }
      </style>
    </head>
    <body class="bg-gray-100 min-h-screen flex items-center justify-center">
      <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h3 class="text-2xl font-semibold text-gray-800 mb-6 text-center">Buy This Book</h3>
        <form method="post" class="space-y-4">
          <div>
            <input type="text" name="name" placeholder="Your Name" required class="w-full p-3 border border-gray-300 rounded-md">
          </div>
          <div>
            <input type="email" name="email" placeholder="Email" required class="w-full p-3 border border-gray-300 rounded-md">
          </div>
          <div>
            <input type="text" name="phone" placeholder="Phone Number" class="w-full p-3 border border-gray-300 rounded-md">
          </div>
          <div>
            <textarea name="address" placeholder="Shipping Address" required class="w-full p-3 border border-gray-300 rounded-md resize-none h-24"></textarea>
          </div>
          <div>
            <input type="number" name="quantity" min="1" value="1" required class="w-full p-3 border border-gray-300 rounded-md">
          </div>
          <input type="submit" value="Place Order" class="btn w-full p-3 bg-indigo-600 text-white rounded-md cursor-pointer">
        </form>
      </div>
    </body>
    </html>
    '''
    return render_template_string(form_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)