from flask import render_template, redirect, url_for, session, flash
from app.blueprints.orders import bp
from app.db import get_db_connection
from app.extensions import stripe
from app.utils.unique_ids import generate_order_number
from mysql.connector import Error
from app.blueprints.auth.routes import login_required

@bp.route('/create-checkout-session', methods=['GET'])
@login_required
def create_checkout_session():
    product_id = session.get('product_id')
    if not product_id:
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
    product_id = session.get('product_id')
    user_id = session.get('user_id')

    if not user_id:
        flash('You must be logged in to complete an order.')
        return redirect(url_for('auth.login'))

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
            cursor.execute("""
                INSERT INTO orders (user_id, status, total_price)
                VALUES (%s, %s, %s)
            """, (user_id, 'Completed', product['price']))
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
            session.pop('product_id', None)

            return render_template('order_details.html', order_number=order_number, product=product)
        except Error as e:
            print(f"Error: {e}")
            return "An error occurred", 500
    else:
        return "Database connection failed", 500