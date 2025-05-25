from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify,send_file
from models import db, User, Product, Certification, Promotion, promotion_products, Wishlist, Order, Negotiation, Message, Announcement, Review
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
print("Current working directory:", os.getcwd())
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'FEDE11RAl!'
print("DATABASE URI:", app.config['SQLALCHEMY_DATABASE_URI'])

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/download-db')
def download_db():
    try:
        db_path = '/tmp/market.db'
        if os.path.exists(db_path):
            return send_file(db_path, as_attachment=True)
        else:
            return f"Database file not found at {db_path}", 404
    except Exception as e:
        return f"Internal Error: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        # Check if user already exists
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists')
            return redirect(url_for('signup'))

        user = User(
            username=username,
            name=name,
            phone=phone,
            email=email,
            role=role
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Login successful!')
            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('simple_admin_dashboard'))
            elif user.role == 'farmer':
                return redirect(url_for('farmer_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid email or password')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/simple_admin_dashboard')
def simple_admin_dashboard():
    return render_template('simple_admin_dashboard.html')

@app.route('/farmer_dashboard')
def farmer_dashboard():
    return render_template('farmer_dashboard.html')

@app.route('/farmer_products')
def farmer_products():
    return render_template('farmer_products.html')

@app.route('/farmer_orders')
def farmer_orders():
    return render_template('farmer_orders.html')

@app.route('/farmer_promotions')
def farmer_promotions():
    return render_template('farmer_promotions.html')

@app.route('/farmer_negotiation')
def farmer_negotiation():
    if 'user_id' not in session or session.get('role') != 'farmer':
        flash('Unauthorized access.')
        return redirect(url_for('login'))
    return render_template('farmer_negotiation.html', user_id=session['user_id'])

@app.route('/farmer_profile', methods=['GET', 'POST'])
def farmer_profile():
    if 'user_id' not in session or session.get('role') != 'farmer':
        flash('Unauthorized access.')
        return redirect(url_for('login'))

    farmer = User.query.get(session['user_id'])
    # Get the latest certification
    certification = Certification.query.filter_by(farmer_id=farmer.id).order_by(Certification.id.desc()).first()
    cert_status = certification.status if certification else None

    # Handle certification upload
    if request.method == 'POST':
        cert_type = request.form.get('certification_type')
        cert_file = request.files.get('certification')
        if cert_file and cert_type:
            filename = secure_filename(cert_file.filename)
            cert_path = os.path.join('static', 'certifications', filename)
            os.makedirs(os.path.dirname(cert_path), exist_ok=True)
            cert_file.save(cert_path)
            # Save certification record in DB
            certification = Certification(
                farmer_id=farmer.id,
                type=cert_type,
                file_path=cert_path,
                status='pending'
            )
            db.session.add(certification)
            db.session.commit()
            flash('Certification uploaded and submitted for verification!')
        else:
            flash('Please select a certification type and file.')

    return render_template('farmer_profile.html', farmer=farmer, cert_status=cert_status)

@app.route('/customer_dashboard')
def customer_dashboard():
    return render_template('customer_dashboard.html')

@app.route('/customer_products')
def customer_products():
    return render_template('customer_products.html')

@app.route('/customer_wishlist')
def customer_wishlist():
    return render_template('customer_wishlist.html')

@app.route('/customer_orders')
def customer_orders():
    return render_template('customer_orders.html')

@app.route('/customer_negotiation')
def customer_negotiation():
    if 'user_id' not in session or session.get('role') != 'customer':
        flash('Unauthorized access.')
        return redirect(url_for('login'))
    return render_template('customer_negotiation.html', user_id=session['user_id'])

@app.route('/customer_ratings')
def customer_ratings():
    return render_template('customer_ratings.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('index'))

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/farmer/products', methods=['POST'])
def add_product():
    if 'user_id' not in session or session.get('role') != 'farmer':
        return jsonify({'error': 'Unauthorized'}), 401

    name = request.form.get('name')
    price = request.form.get('price')
    quantity = request.form.get('quantity')
    image = request.files.get('image')
    farmer_id = session['user_id']

    # Save image if present
    image_filename = None
    if image:
        filename = secure_filename(image.filename)
        image_path = os.path.join('static', 'images', filename)
        image.save(image_path)
        image_filename = '/' + image_path  # For use in <img src="...">

    # Create and save product
    product = Product(
        name=name,
        price=float(price),
        quantity=int(quantity),
        image=image_filename,
        farmer_id=farmer_id,
        created_at=datetime.utcnow()
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Product added!'})

@app.route('/api/farmer/products', methods=['GET'])
def get_farmer_products():
    if 'user_id' not in session or session.get('role') != 'farmer':
        return jsonify([])

    farmer_id = session['user_id']
    products = Product.query.filter_by(farmer_id=farmer_id).all()
    return jsonify([
        {
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'discounted_price': get_discounted_price(p),
            'quantity': p.quantity,
            'image': p.image,
            'dateAdded': p.created_at.isoformat() if p.created_at else ""
        }
        for p in products
    ])

@app.route('/api/farmer/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    if 'user_id' not in session or session.get('role') != 'farmer':
        return jsonify({'error': 'Unauthorized'}), 401

    product = Product.query.filter_by(id=product_id, farmer_id=session['user_id']).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    data = request.form if request.form else request.get_json()
    if 'quantity' in data:
        product.quantity = int(data['quantity'])
    if 'price' in data:
        product.price = float(data['price'])
    db.session.commit()
    return jsonify({'success': True, 'message': 'Product updated!'})

@app.route('/api/farmer/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if 'user_id' not in session or session.get('role') != 'farmer':
        return jsonify({'error': 'Unauthorized'}), 401

    product = Product.query.filter_by(id=product_id, farmer_id=session['user_id']).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Product deleted!'})

@app.route('/api/farmer/promotions', methods=['POST'])
def add_promotion():
    if 'user_id' not in session or session.get('role') != 'farmer':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    title = data.get('title')
    promo_type = data.get('type')
    discount_value = float(data.get('discountValue'))
    description = data.get('description')
    start_date = datetime.fromisoformat(data.get('startDate'))
    end_date = datetime.fromisoformat(data.get('endDate'))
    product_ids = data.get('productIds', [])
    farmer_id = session['user_id']

    # Create promotion
    promotion = Promotion(
        title=title,
        type=promo_type,
        discount_value=discount_value,
        description=description,
        start_date=start_date,
        end_date=end_date,
        farmer_id=farmer_id
    )
    # Link products
    products = Product.query.filter(Product.id.in_(product_ids), Product.farmer_id == farmer_id).all()
    promotion.products = products

    db.session.add(promotion)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Promotion created!'})

@app.route('/api/farmer/promotions', methods=['GET'])
def get_promotions():
    if 'user_id' not in session or session.get('role') != 'farmer':
        return jsonify([])

    farmer_id = session['user_id']
    promotions = Promotion.query.filter_by(farmer_id=farmer_id).all()
    return jsonify([
        {
            'id': p.id,
            'title': p.title,
            'type': p.type,
            'discountValue': p.discount_value,
            'description': p.description,
            'startDate': p.start_date.isoformat(),
            'endDate': p.end_date.isoformat(),
            'products': [{'id': prod.id, 'name': prod.name} for prod in p.products]
        }
        for p in promotions
    ])

@app.route('/api/farmer/promotions/<int:promotion_id>', methods=['PUT'])
def update_promotion(promotion_id):
    if 'user_id' not in session or session.get('role') != 'farmer':
        return jsonify({'error': 'Unauthorized'}), 401

    promotion = Promotion.query.filter_by(id=promotion_id, farmer_id=session['user_id']).first()
    if not promotion:
        return jsonify({'error': 'Promotion not found'}), 404

    data = request.get_json()
    if 'discountValue' in data:
        promotion.discount_value = float(data['discountValue'])
    # ... handle other fields if needed ...
    db.session.commit()
    return jsonify({'success': True, 'message': 'Promotion updated!'})

@app.route('/api/farmer/promotions/<int:promotion_id>', methods=['DELETE'])
def delete_promotion(promotion_id):
    if 'user_id' not in session or session.get('role') != 'farmer':
        return jsonify({'error': 'Unauthorized'}), 401

    promotion = Promotion.query.filter_by(id=promotion_id, farmer_id=session['user_id']).first()
    if not promotion:
        return jsonify({'error': 'Promotion not found'}), 404

    try:
        db.session.delete(promotion)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Promotion deleted successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def get_discounted_price(product):
    now = datetime.utcnow()
    for promo in product.promotions:
        print(promo.title, promo.discount_value, promo.start_date, promo.end_date)
        if promo.start_date <= now <= promo.end_date:
            return product.price * (1 - promo.discount_value / 100)
    return product.price

@app.route('/api/customer/profile')
def api_customer_profile():
    if 'user_id' not in session or session.get('role') != 'customer':
        return jsonify({'error': 'Unauthorized'}), 401
    customer = User.query.get(session['user_id'])
    return jsonify({
        'name': customer.name,
        'username': customer.username,
        'email': customer.email,
        'phone': customer.phone,
        'created_at': customer.created_at.strftime('%B %d, %Y')
    })

@app.route('/api/products')
def api_all_products():
    # Get all products and their farmers
    products = Product.query.all()
    result = []
    for p in products:
        farmer = User.query.get(p.farmer_id)
        # Get latest certification status (if any)
        cert = Certification.query.filter_by(farmer_id=farmer.id).order_by(Certification.id.desc()).first()
        cert_status = cert.status if cert else "Not Uploaded"
        # Get discounted price if any promotion is active
        discounted_price = get_discounted_price(p)
        result.append({
            'id': p.id,
            'name': p.name,
            'category': getattr(p, 'category', 'General'),  # Adjust if you have a category field
            'price': p.price,
            'discounted_price': discounted_price,
            'img': p.image if p.image else '/static/images/default.png',
            'farmer': {
                'name': farmer.name,
                'phone': farmer.phone,
                'email': farmer.email
            },
            'certification_status': cert_status
        })
    return jsonify(result)

@app.route('/api/wishlist', methods=['POST'])
def add_to_wishlist():
    if 'user_id' not in session or session.get('role') != 'customer':
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    product_id = data.get('product_id')
    customer_id = session['user_id']
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(customer_id=customer_id, product_id=product_id).first()
    if existing:
        return jsonify({'message': 'Already in wishlist'})
    wishlist_item = Wishlist(customer_id=customer_id, product_id=product_id)
    db.session.add(wishlist_item)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/wishlist')
def get_wishlist():
    if 'user_id' not in session or session.get('role') != 'customer':
        return jsonify([])  # or 401
    customer_id = session['user_id']
    wishlist_items = Wishlist.query.filter_by(customer_id=customer_id).all()
    result = []
    for item in wishlist_items:
        product = Product.query.get(item.product_id)
        # Add product details as needed
        result.append({
            'id': product.id,
            'name': product.name,
            'category': getattr(product, 'category', 'General'),
            'price': product.price,
            'discounted_price': get_discounted_price(product),
            'img': product.image if product.image else '/static/images/default.png'
        })
    return jsonify(result)

@app.route('/api/wishlist/<int:product_id>', methods=['DELETE'])
def remove_from_wishlist(product_id):
    if 'user_id' not in session or session.get('role') != 'customer':
        return jsonify({'error': 'Unauthorized'}), 401
    customer_id = session['user_id']
    item = Wishlist.query.filter_by(customer_id=customer_id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/orders', methods=['POST'])
def create_order():
    if 'user_id' not in session or session.get('role') != 'customer':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    print("Received order request:", data)  # Debug log
    negotiation_id = data.get('negotiation_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id:
        return jsonify({'error': 'Missing product ID'}), 400
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if product.quantity < quantity:
        return jsonify({'error': 'Product out of stock'}), 400
    
    try:
        # If this is a negotiated order
        if negotiation_id:
            negotiation = Negotiation.query.get(negotiation_id)
            print("Found negotiation:", negotiation.id if negotiation else None)  # Debug log
            if not negotiation:
                return jsonify({'error': 'Negotiation not found'}), 404
            
            print("Negotiation status:", negotiation.status)  # Debug log
            if negotiation.status != 'agreed':
                return jsonify({'error': f'Price not agreed upon. Current status: {negotiation.status}'}), 400
            
            if negotiation.customer_id != session['user_id']:
                return jsonify({'error': 'Unauthorized'}), 401
            
            total_price = negotiation.agreed_price * quantity
            print("Calculated total price:", total_price)  # Debug log
            
            # Update negotiation status to ordered
            negotiation.status = 'ordered'
            db.session.add(negotiation)
            
            # Add a system message about the order
            system_message = Message(
                negotiation_id=negotiation_id,
                sender_id=session['user_id'],
                content=f"Order placed at ₹{total_price}",
                is_price_proposal=False
            )
            db.session.add(system_message)
        else:
            # Direct order - use product's current price
            total_price = product.price * quantity
        
        # Create order
        order = Order(
            customer_id=session['user_id'],
            product_id=product_id,
            quantity=quantity,
            total_price=total_price,
            status='pending',
            negotiation_id=negotiation_id
        )
        db.session.add(order)
        
        # Update product quantity
        product.quantity -= quantity
        
        db.session.commit()
        print("Order created successfully:", order.id)  # Debug log
        return jsonify({
            'success': True,
            'order_id': order.id,
            'total_price': total_price
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error creating order: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@app.route('/api/customer/orders')
def get_customer_orders():
    if 'user_id' not in session or session.get('role') != 'customer':
        return jsonify({'error': 'Unauthorized'}), 401
    
    orders = Order.query.filter_by(customer_id=session['user_id']).all()
    return jsonify([{
        'id': order.id,
        'product': order.product.name,
        'quantity': order.quantity,
        'total_price': order.total_price,
        'status': order.status,
        'created_at': order.created_at.isoformat()
    } for order in orders])

@app.route('/api/farmer/orders')
def get_farmer_orders():
    if 'user_id' not in session:
        print("No user_id in session")
        return jsonify({'error': 'Not logged in'}), 401
    
    if session.get('role') != 'farmer':
        print(f"Invalid role: {session.get('role')}")
        return jsonify({'error': 'Not authorized as farmer'}), 401
    
    try:
        # Get all products belonging to this farmer
        farmer_products = Product.query.filter_by(farmer_id=session['user_id']).all()
        product_ids = [p.id for p in farmer_products]
        
        if not product_ids:
            print(f"No products found for farmer {session['user_id']}")
            return jsonify([])
        
        # Get all orders for these products
        orders = Order.query.filter(Order.product_id.in_(product_ids)).all()
        
        result = [{
            'id': order.id,
            'product': order.product.name,
            'customer': order.customer.name,
            'quantity': order.quantity,
            'total_price': order.total_price,
            'status': order.status,
            'created_at': order.created_at.isoformat()
        } for order in orders]
        
        print(f"Found {len(result)} orders for farmer {session['user_id']}")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in get_farmer_orders: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/farmer/orders/<int:order_id>', methods=['PUT'])
def update_farmer_order_status(order_id):
    if 'user_id' not in session or session.get('role') != 'farmer':
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get the order
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # Verify that the order is for one of the farmer's products
    product = Product.query.get(order.product_id)
    if not product or product.farmer_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Update the status
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ['pending', 'confirmed', 'delivered', 'cancelled']:
        return jsonify({'error': 'Invalid status'}), 400
    
    order.status = new_status
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Order status updated successfully',
        'order': {
            'id': order.id,
            'status': order.status
        }
    })

@app.route('/api/negotiations', methods=['POST'])
def start_or_get_negotiation():
    if 'user_id' not in session or session.get('role') != 'customer':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    product_id = data.get('product_id')
    customer_id = session['user_id']

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    farmer_id = product.farmer_id

    # Only return open or agreed negotiations
    negotiation = Negotiation.query.filter_by(
        product_id=product_id,
        customer_id=customer_id,
        farmer_id=farmer_id
    ).filter(Negotiation.status.in_(['open', 'agreed'])).first()

    if not negotiation:
        negotiation = Negotiation(
            product_id=product_id,
            customer_id=customer_id,
            farmer_id=farmer_id,
            status='open'
        )
        db.session.add(negotiation)
        db.session.commit()

    return jsonify({
        'id': negotiation.id,
        'status': negotiation.status,
        'agreed_price': negotiation.agreed_price
    })

@app.route('/api/negotiations/<int:negotiation_id>')
def get_negotiation(negotiation_id):
    negotiation = Negotiation.query.get(negotiation_id)
    if not negotiation:
        return jsonify({'error': 'Negotiation not found'}), 404

    return jsonify({
        'id': negotiation.id,
        'product_id': negotiation.product_id,
        'customer_id': negotiation.customer_id,
        'farmer_id': negotiation.farmer_id,
        'status': negotiation.status,
        'agreed_price': negotiation.agreed_price
    })

@app.route('/api/negotiations/<int:negotiation_id>/messages')
def get_negotiation_messages(negotiation_id):
    messages = Message.query.filter_by(negotiation_id=negotiation_id).order_by(Message.created_at).all()
    return jsonify([
        {
            'id': m.id,
            'sender_id': m.sender_id,
            'content': m.content,
            'is_price_proposal': m.is_price_proposal,
            'proposed_price': m.proposed_price,
            'created_at': m.created_at.isoformat()
        }
        for m in messages
    ])

@app.route('/api/negotiations/messages', methods=['POST'])
def send_negotiation_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    negotiation_id = data.get('negotiation_id')
    content = data.get('content')
    is_price_proposal = data.get('is_price_proposal', False)
    proposed_price = data.get('proposed_price')

    # Get the negotiation and verify the user is part of it
    negotiation = Negotiation.query.get(negotiation_id)
    if not negotiation:
        return jsonify({'error': 'Negotiation not found'}), 404

    # Check if the user is either the farmer or customer in this negotiation
    if session['user_id'] not in [negotiation.farmer_id, negotiation.customer_id]:
        return jsonify({'error': 'Unauthorized - not part of this negotiation'}), 401

    message = Message(
        negotiation_id=negotiation_id,
        sender_id=session['user_id'],
        content=content,
        is_price_proposal=is_price_proposal,
        proposed_price=proposed_price
    )
    db.session.add(message)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/negotiations/price', methods=['POST'])
def propose_price():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    negotiation_id = data.get('negotiation_id')
    price = data.get('price')
    content = data.get('content', f"Proposed price: ₹{price}")  # Use provided content or default

    negotiation = Negotiation.query.get(negotiation_id)
    if not negotiation or negotiation.status != 'open':
        return jsonify({'error': 'Negotiation not open'}), 400

    # Add a price proposal message
    message = Message(
        negotiation_id=negotiation_id,
        sender_id=session['user_id'],
        content=content,
        is_price_proposal=True,
        proposed_price=price
    )
    db.session.add(message)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/negotiations/<int:negotiation_id>/accept', methods=['POST'])
def accept_price(negotiation_id):
    if 'user_id' not in session or session.get('role') != 'farmer':
        return jsonify({'error': 'Unauthorized'}), 401

    negotiation = Negotiation.query.get(negotiation_id)
    if not negotiation:
        return jsonify({'error': 'Negotiation not found'}), 404
    
    if negotiation.status != 'open':
        return jsonify({'error': 'Negotiation is already closed'}), 400

    # Find the latest price proposal
    latest_price_message = Message.query.filter_by(
        negotiation_id=negotiation_id,
        is_price_proposal=True
    ).order_by(Message.created_at.desc()).first()

    if not latest_price_message:
        return jsonify({'error': 'No price proposal to accept'}), 400

    # Update negotiation status
    negotiation.status = 'agreed'
    negotiation.agreed_price = latest_price_message.proposed_price
    
    # Add a system message about the accepted price
    system_message = Message(
        negotiation_id=negotiation_id,
        sender_id=session['user_id'],
        content=f"Price accepted: ₹{negotiation.agreed_price}",
        is_price_proposal=False
    )
    
    db.session.add(system_message)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'agreed_price': negotiation.agreed_price,
        'message': 'Price accepted successfully'
    })

@app.route('/api/products/negotiable')
def get_negotiable_products():
    products = Product.query.filter_by(is_negotiable=True).all()
    result = []
    for p in products:
        farmer = User.query.get(p.farmer_id)
        result.append({
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'farmerName': farmer.name if farmer else '',
            # add other fields as needed
        })
    return jsonify(result)

@app.route('/api/farmer/negotiations')
def get_farmer_negotiations():
    if 'user_id' not in session or session.get('role') != 'farmer':
        return jsonify({'error': 'Unauthorized'}), 401

    # Only show negotiations that are not 'ordered'
    negotiations = Negotiation.query.filter_by(farmer_id=session['user_id']).filter(Negotiation.status != 'ordered').all()
    result = []
    for n in negotiations:
        customer = User.query.get(n.customer_id)
        product = Product.query.get(n.product_id)
        # Get the latest price proposal message (from customer)
        latest_price_message = Message.query.filter_by(
            negotiation_id=n.id,
            is_price_proposal=True
        ).order_by(Message.created_at.desc()).first()
        latest_price = latest_price_message.proposed_price if latest_price_message else None
        result.append({
            'id': n.id,
            'product_name': product.name if product else '',
            'customer_name': customer.name if customer else '',
            'status': n.status,
            'agreed_price': n.agreed_price,
            'latest_price': latest_price
        })
    return jsonify(result)

# Create announcement (admin)
@app.route('/api/admin/announcements', methods=['POST'])
def create_announcement():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    if not title or not content:
        return jsonify({'error': 'Title and content required'}), 400
    announcement = Announcement(
        title=title,
        content=content,
        created_by=session['user_id'],
        created_at=datetime.utcnow()
    )
    db.session.add(announcement)
    db.session.commit()
    return jsonify({
        'id': announcement.id,
        'title': announcement.title,
        'content': announcement.content,
        'createdAt': announcement.created_at.isoformat(),
        'createdBy': announcement.created_by
    })

# List all announcements (admin)
@app.route('/api/admin/announcements')
def admin_list_announcements():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return jsonify([
        {
            'id': a.id,
            'title': a.title,
            'content': a.content,
            'createdAt': a.created_at.isoformat(),
            'createdBy': a.created_by
        } for a in announcements
    ])

# Delete announcement (admin)
@app.route('/api/admin/announcements/<int:announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(announcement)
    db.session.commit()
    return jsonify({'success': True})

# Public: List all announcements
@app.route('/api/announcements')
def public_announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return jsonify([
        {
            'id': a.id,
            'title': a.title,
            'content': a.content,
            'createdAt': a.created_at.isoformat(),
            'createdBy': a.created_by
        } for a in announcements
    ])

@app.route('/api/users', methods=['GET'])
def get_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    users = User.query.all()
    print(session)
    return jsonify([{
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'username': user.username,
        'role': user.role,
        'status': 'active' if user.is_active else 'inactive',
        'created_at': user.created_at.isoformat() if user.created_at else None
    } for user in users])

@app.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({'success': True, 'status': 'active' if user.is_active else 'inactive'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>/deactivate', methods=['POST'])
def deactivate_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.is_active = False
    db.session.commit()
    return jsonify({'success': True, 'status': 'inactive'})

@app.route('/api/admin/certifications')
def admin_list_certifications():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    certs = Certification.query.order_by(Certification.requested_at.desc()).all()
    return jsonify([
        {
            'id': c.id,
            'farmer_id': c.farmer_id,
            'type': c.type,
            'file_path': c.file_path,
            'status': c.status,
            'requested_at': c.requested_at.isoformat() if c.requested_at else None,
            'verified_at': c.verified_at.isoformat() if c.verified_at else None,
            'verified_by': c.verified_by
        } for c in certs
    ])

@app.route('/api/admin/certifications/<int:cert_id>/verify', methods=['POST'])
def verify_certification(cert_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    cert = Certification.query.get(cert_id)
    if not cert:
        return jsonify({'error': 'Not found'}), 404
    cert.status = 'certified'
    cert.verified_at = datetime.utcnow()
    cert.verified_by = session['user_id']
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/certifications/<int:cert_id>/reject', methods=['POST'])
def reject_certification(cert_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    cert = Certification.query.get(cert_id)
    if not cert:
        return jsonify({'error': 'Not found'}), 404
    cert.status = 'rejected'
    cert.verified_at = datetime.utcnow()
    cert.verified_by = session['user_id']
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/customer/id', methods=['GET'])
def get_customer_id():
    if 'user_id' not in session or session.get('role') != 'customer':
        return jsonify({'error': 'User not authenticated'}), 401
    customer_id = session.get('user_id')
    return jsonify({'customer_id': customer_id})

@app.route('/api/reviews', methods=['POST'])
def create_review():
    data = request.get_json()
    product_id = data.get('product_id')
    rating = data.get('rating')
    customer_id = data.get('customer_id')
    review_text = data.get('review_text', '')
    
    if not product_id or not rating or not customer_id:
        return jsonify({'error': 'Product ID, rating, and customer ID are required'}), 400
    
    try:
        rating = int(rating)
        if not 1 <= rating <= 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    except ValueError:
        return jsonify({'error': 'Rating must be a number'}), 400
    
    if not Product.query.get(product_id):
        return jsonify({'error': 'Product not found'}), 404

    new_review = Review(
        product_id=product_id,
        customer_id=customer_id,
        rating=rating,
        review_text=review_text,
        created_at=datetime.utcnow()
    )
    
    try:
        db.session.add(new_review)
        db.session.commit()
        return jsonify({
            'message': 'Review submitted successfully',
            'review_id': new_review.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to submit review: ' + str(e)}), 500
@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    result = []
    for review in reviews:
        product = Product.query.get(review.product_id)
        customer = User.query.get(review.customer_id)
        result.append({
            'id': review.id,
            'product_name': product.name if product else 'Unknown Product',
            'customer_name': customer.name if customer else 'Anonymous',
            'rating': review.rating,
            'review_text': review.review_text,
            'created_at': review.created_at.isoformat()
        })
    return jsonify(result)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
