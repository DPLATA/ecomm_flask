# from flask import Flask, render_template, request, redirect, url_for, session
# import os
# import mysql.connector
# from mysql.connector import Error
# import stripe
# import uuid
#
# # Get the absolute path of the directory containing this file
# template_dir = os.path.abspath(os.path.dirname(__file__))
# # Point to the templates folder
# template_dir = os.path.join(template_dir, 'templates')
#
# # Create the Flask app with the custom template folder
# app = Flask(__name__, template_folder=template_dir)
#
# app.secret_key = 'your_secret_key'  # Set a secret key for session management
#
# # MySQL configuration
# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'gplatac95',
#     'database': 'immet'
# }
#
# # Configure Stripe
# stripe.api_key = "sk_test_51LVgaTKBpIogN4FiyDfTqMvNR3U2sYEWatn5RCEYyBQCDQWn2fUpwqbWZcXboJuoHgLaV4sCWvDFmI6mMV0ByiQp00UbLXYYdz"
#
#
# def get_db_connection():
#     try:
#         connection = mysql.connector.connect(**db_config)
#         return connection
#     except Error as e:
#         print(f"Error connecting to MySQL: {e}")
#         return None
#
#
# @app.route('/')
# def product_detail():
#     connection = get_db_connection()
#     if connection:
#         try:
#             cursor = connection.cursor(dictionary=True)
#             cursor.execute("SELECT * FROM products LIMIT 1")
#             product = cursor.fetchone()
#             cursor.close()
#             connection.close()
#             return render_template('product_detail.html', product=product)
#         except Error as e:
#             print(f"Error: {e}")
#             return "An error occurred", 500
#     else:
#         return "Database connection failed", 500
#
#
# @app.route('/shipping', methods=['GET', 'POST'])
# def shipping():
#     if request.method == 'POST':
#         shipping_info = {
#             'name': request.form.get('name'),
#             'address': request.form.get('address'),
#             'city': request.form.get('city'),
#             'country': request.form.get('country'),
#             'zip_code': request.form.get('zip')
#         }
#         session['shipping_info'] = shipping_info
#         return redirect(url_for('create_checkout_session'))
#     return render_template('shipping.html')
#
#
# @app.route('/create-checkout-session', methods=['GET'])
# def create_checkout_session():
#     connection = get_db_connection()
#     if connection:
#         try:
#             cursor = connection.cursor(dictionary=True)
#             cursor.execute("SELECT * FROM products LIMIT 1")
#             product = cursor.fetchone()
#             cursor.close()
#             connection.close()
#
#             checkout_session = stripe.checkout.Session.create(
#                 payment_method_types=['card'],
#                 line_items=[
#                     {
#                         'price_data': {
#                             'currency': 'usd',
#                             'unit_amount': int(float(product['price']) * 100),
#                             'product_data': {
#                                 'name': product['name'],
#                                 'description': product['description'],
#                             },
#                         },
#                         'quantity': 1,
#                     },
#                 ],
#                 mode='payment',
#                 success_url=url_for('success', _external=True),
#                 cancel_url=url_for('product_detail', _external=True),
#             )
#             return redirect(checkout_session.url, code=303)
#         except Error as e:
#             print(f"Error: {e}")
#             return "An error occurred", 500
#     else:
#         return "Database connection failed", 500
#
#
# @app.route('/success')
# def success():
#     order_number = str(uuid.uuid4().hex)[:8].upper()
#     shipping_info = session.get('shipping_info', {})
#
#     connection = get_db_connection()
#     if connection:
#         try:
#             cursor = connection.cursor(dictionary=True)
#
#             # Get the product
#             cursor.execute("SELECT * FROM products LIMIT 1")
#             product = cursor.fetchone()
#
#             # Create a new order
#             shipping_address = f"{shipping_info.get('address')}, {shipping_info.get('city')}, {shipping_info.get('country')}, {shipping_info.get('zip_code')}"
#             cursor.execute("""
#                 INSERT INTO orders (user_id, status, total_price, shipping_address)
#                 VALUES (%s, %s, %s, %s)
#             """, (1, 'Completed', product['price'], shipping_address))
#             order_id = cursor.lastrowid
#
#             # Add order item
#             cursor.execute("""
#                 INSERT INTO order_items (order_id, product_id, quantity, price)
#                 VALUES (%s, %s, %s, %s)
#             """, (order_id, product['id'], 1, product['price']))
#
#             connection.commit()
#             cursor.close()
#             connection.close()
#
#             session.pop('shipping_info', None)
#
#             return render_template('order_details.html', order_number=order_number, product=product,
#                                    shipping_info=shipping_info)
#         except Error as e:
#             print(f"Error: {e}")
#             return "An error occurred", 500
#     else:
#         return "Database connection failed", 500
#
#
# if __name__ == '__main__':
#     app.run(debug=True)


from flask import Flask
from app.extensions import stripe
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    stripe.api_key = app.config['STRIPE_API_KEY']

    # Register blueprints
    from app.blueprints.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.orders import bp as orders_bp
    app.register_blueprint(orders_bp, url_prefix='/orders')

    from app.blueprints.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app