from flask import render_template, redirect, url_for, session
from app.blueprints.orders import bp
from app.db import get_db_connection
from app.extensions import stripe
from app.utils.unique_ids import generate_order_number
from mysql.connector import Error

SAMPLE_USER_ID = 1  # This is the ID of our sample user


@bp.route('/create-checkout-session', methods=['GET'])
def create_checkout_session():
    product_id = session.get('product_id')
    if not product_id:
        # If there's no product_id in the session, redirect to the product list
        return redirect(url_for('main.product_list'))

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            cursor.close()
            connection.close()

            if not product:
                # If the product doesn't exist, redirect to the product list
                return redirect(url_for('main.product_list'))

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': int(float(product['price']) * 100),
                            'product_data': {
                                'name': product['name'],
                                'description': product['description'],
                            },
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=url_for('orders.success', _external=True),
                cancel_url=url_for('main.product_detail', product_id=product_id, _external=True),
            )
            return redirect(checkout_session.url, code=303)
        except Error as e:
            print(f"Error: {e}")
            return "An error occurred", 500
    else:
        return "Database connection failed", 500


@bp.route('/success')
def success():
    order_number = generate_order_number()
    shipping_info = session.get('shipping_info', {})
    product_id = session.get('product_id')

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)

            # Get the product
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()

            if not product:
                return "Product not found", 404

            # Create a new order
            shipping_address = f"{shipping_info.get('address')}, {shipping_info.get('city')}, {shipping_info.get('country')}, {shipping_info.get('zip_code')}"
            cursor.execute("""
                INSERT INTO orders (user_id, status, total_price, shipping_address)
                VALUES (%s, %s, %s, %s)
            """, (SAMPLE_USER_ID, 'Completed', product['price'], shipping_address))
            order_id = cursor.lastrowid

            # Add order item
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, product['id'], 1, product['price']))

            connection.commit()
            cursor.close()
            connection.close()

            # Clear session data
            session.pop('shipping_info', None)
            session.pop('product_id', None)

            return render_template('order_details.html', order_number=order_number, product=product,
                                   shipping_info=shipping_info)
        except Error as e:
            print(f"Error: {e}")
            return "An error occurred", 500
    else:
        return "Database connection failed", 500