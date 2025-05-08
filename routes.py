from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
import os
from werkzeug.utils import secure_filename
from models import User, Item, BorrowRequest, CollegeInventory
import functools

# Create Blueprint
bp = Blueprint('routes', __name__)

# Decorator for requiring login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('routes.login'))
        return view(**kwargs)
    return wrapped_view

# Decorator for requiring admin role
def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user['user_type'] != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('routes.dashboard'))
        return view(**kwargs)
    return wrapped_view

# Helper function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Routes
@bp.route('/')
def index():
    items = Item.get_all()
    return render_template('index.html', items=items)

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if g.user:
        return redirect(url_for('routes.dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        full_name = request.form['full_name']
        contact_number = request.form.get('contact_number')
        
        error = None
        
        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif not full_name:
            error = 'Full name is required.'
        elif User.get_by_username(username):
            error = f"User {username} is already registered."
        elif User.get_by_email(email):
            error = f"Email {email} is already registered."
            
        if error is None:
            User.create(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                contact_number=contact_number
            )
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('routes.login'))
            
        flash(error, 'error')
        
    return render_template('register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if g.user:
        return redirect(url_for('routes.dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        error = None
        user = User.verify_password(username, password)
        
        if user is None:
            error = 'Incorrect username or password.'
            
        if error is None:
            session.clear()
            session['user_id'] = user['user_id']
            session.permanent = True
            
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('routes.dashboard'))
            
        flash(error, 'error')
        
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('routes.index'))

@bp.route('/dashboard')
@login_required
def dashboard():
    if g.user['user_type'] == 'admin':
        # Admin dashboard data
        students_count = len(User.get_all_students())
        items_count = len(Item.get_all())
        pending_requests = [req for req in BorrowRequest.get_all() if req['status'] == 'pending']
        
        return render_template('dashboard_admin.html', 
                              students_count=students_count,
                              items_count=items_count,
                              pending_requests=pending_requests)
    else:
        # Student dashboard data
        user_items = Item.get_by_owner(g.user['user_id'])
        user_requests = BorrowRequest.get_by_requester(g.user['user_id'])
        
        # Get incoming requests (requests for items owned by the user)
        incoming_requests = BorrowRequest.get_by_item_owner(g.user['user_id'])
        
        return render_template('dashboard_student.html',
                              user_items=user_items,
                              user_requests=user_requests,
                              incoming_requests=incoming_requests)

@bp.route('/add_item', methods=('GET', 'POST'))
@login_required
def add_item():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        condition_status = request.form['condition_status']
        price = request.form['price']
        
        error = None
        
        if not title:
            error = 'Title is required.'
        elif not category:
            error = 'Category is required.'
        elif not condition_status:
            error = 'Condition is required.'
        elif not price:
            error = 'Price is required.'
            
        if error is None:
            item_id = Item.create(
                title=title,
                description=description,
                category=category,
                condition_status=condition_status,
                price=float(price),
                owner_id=g.user['user_id']
            )
            
            # Handle file upload if provided
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{item_id}_{file.filename}")
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    
                    # Update item with image filename
                    Item.update(item_id, image=filename)
            
            flash('Item added successfully!', 'success')
            return redirect(url_for('routes.dashboard'))
            
        flash(error, 'error')
        
    return render_template('add_item.html')

@bp.route('/edit_item/<int:item_id>', methods=('GET', 'POST'))
@login_required
def edit_item(item_id):
    item = Item.get_by_id(item_id)
    
    # Check if item exists and belongs to the user
    if not item or (item['owner_id'] != g.user['user_id'] and g.user['user_type'] != 'admin'):
        flash('Item not found or you don\'t have permission to edit it.', 'error')
        return redirect(url_for('routes.dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        condition_status = request.form['condition_status']
        price = request.form['price']
        
        error = None
        
        if not title:
            error = 'Title is required.'
        elif not category:
            error = 'Category is required.'
        elif not condition_status:
            error = 'Condition is required.'
        elif not price:
            error = 'Price is required.'
            
        if error is None:
            Item.update(
                item_id=item_id,
                title=title,
                description=description,
                category=category,
                condition_status=condition_status,
                price=float(price)
            )
            
            # Handle file upload if provided
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{item_id}_{file.filename}")
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    
                    # Update item with image filename
                    Item.update(item_id, image=filename)
            
            flash('Item updated successfully!', 'success')
            return redirect(url_for('routes.dashboard'))
            
        flash(error, 'error')
        
    return render_template('edit_item.html', item=item)
@bp.route('/update_preferences', methods=('POST',))
@login_required
def update_preferences():
    # Get form data
    email_notifications = 'email_notifications' in request.form
    request_alerts = 'request_alerts' in request.form
    system_updates = 'system_updates' in request.form
    
    try:
        # Connect to database
        db, cursor = get_db()
        
        # Update notification preferences
        cursor.execute(
            """UPDATE users SET 
                email_notifications = %s,
                request_alerts = %s,
                system_updates = %s
               WHERE user_id = %s""",
            (email_notifications, request_alerts, system_updates, g.user['user_id'])
        )
        db.commit()
        
        # Update session to reflect changes
        g.user = User.get_by_id(g.user['user_id'])
        
        flash('Notification preferences updated successfully!', 'success')
    except Exception as e:
        flash(f"Error updating preferences: {e}", 'error')
    
    return redirect(url_for('routes.user_profile'))

@bp.route('/delete_item/<int:item_id>', methods=('POST',))
@login_required
def delete_item(item_id):
    """
    Delete an item if it belongs to the current user or if the user is an admin.
    This route handles POST requests only for security best practices.
    """
    item = Item.get_by_id(item_id)
    
    # Check if item exists
    if not item:
        flash('Item not found.', 'error')
        return redirect(url_for('routes.dashboard'))
    
    # Check if user has permission to delete
    if item['owner_id'] != g.user['user_id'] and g.user['user_type'] != 'admin':
        flash('You don\'t have permission to delete this item.', 'error')
        return redirect(url_for('routes.dashboard'))
    
    # Check if the item has related borrow requests
    db, cursor = get_db()
    cursor.execute("SELECT COUNT(*) as count FROM borrow_requests WHERE item_id = %s", (item_id,))
    result = cursor.fetchone()
    has_requests = result['count'] > 0
    
    # Optional: Add a flag parameter to force delete even with requests
    force_delete = request.args.get('force', 'false').lower() == 'true'
    
    if has_requests and g.user['user_type'] != 'admin' and not force_delete:
        flash('This item has active borrow requests. Please handle all requests before deleting.', 'warning')
        return redirect(url_for('routes.manage_requests'))
    
    # Delete any associated borrow requests first (to maintain referential integrity)
    if has_requests:
        cursor.execute("DELETE FROM borrow_requests WHERE item_id = %s", (item_id,))
        db.commit()
    
    # Delete the item and any associated images
    if Item.delete(item_id):
        # If there's an image associated with the item, delete it from the filesystem
        if item.get('image'):
            try:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item['image'])
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                # Log the error but continue with the deletion
                print(f"Error deleting image file: {e}")
        
        flash('Item deleted successfully!', 'success')
    else:
        flash('Error deleting item. Please try again.', 'error')
    
    return redirect(url_for('routes.dashboard'))
@login_required
def request_item(item_id):
    item = Item.get_by_id(item_id)
    
    # Check if item exists and is available
    if not item or not item['is_available']:
        flash('Item not found or not available.', 'error')
        return redirect(url_for('routes.index'))
    
    # User cannot request their own item
    if item['owner_id'] == g.user['user_id']:
        flash('You cannot request your own item.', 'error')
        return redirect(url_for('routes.index'))
    
    if request.method == 'POST':
        notes = request.form.get('notes')
        
        # Create borrow request
        BorrowRequest.create(
            item_id=item_id,
            requester_id=g.user['user_id'],
            notes=notes
        )
        
        flash('Request sent successfully!', 'success')
        return redirect(url_for('routes.dashboard'))
    
    return render_template('request_item.html', item=item)

@bp.route('/manage_requests')
@login_required
def manage_requests():
    if g.user['user_type'] == 'admin':
        # Admin sees all requests
        requests = BorrowRequest.get_all()
    else:
        # Students see requests for their items
        requests = BorrowRequest.get_by_item_owner(g.user['user_id'])
    
    return render_template('manage_requests.html', requests=requests)

@bp.route('/respond_request/<int:request_id>', methods=('POST',))
@login_required
def respond_request(request_id):
    borrow_request = BorrowRequest.get_by_id(request_id)
    
    if not borrow_request:
        flash('Request not found.', 'error')
        return redirect(url_for('routes.manage_requests'))
    
    # Get the item
    item = Item.get_by_id(borrow_request['item_id'])
    
    # Check if user owns the item or is admin
    if not item or (item['owner_id'] != g.user['user_id'] and g.user['user_type'] != 'admin'):
        flash('You don\'t have permission to respond to this request.', 'error')
        return redirect(url_for('routes.manage_requests'))
    
    status = request.form['status']
    return_date = request.form.get('return_date')
    
    # Update request status
    BorrowRequest.update_status(request_id, status, return_date)
    
    # If approved, mark item as unavailable
    if status == 'approved':
        Item.update(item['item_id'], is_available=False)
    
    flash(f'Request {status}.', 'success')
    return redirect(url_for('routes.manage_requests'))

@bp.route('/manage_students')
@admin_required
def manage_students():
    students = User.get_all_students()
    return render_template('manage_students.html', students=students)

@bp.route('/inventory')
@login_required
def inventory():
    inventory_items = CollegeInventory.get_all()
    
    # Check if user is admin (for adding/editing inventory)
    is_admin = g.user['user_type'] == 'admin'
    
    return render_template('college_inventory.html', 
                          inventory_items=inventory_items,
                          is_admin=is_admin)

@bp.route('/add_inventory', methods=('GET', 'POST'))
@admin_required
def add_inventory():
    if request.method == 'POST':
        item_name = request.form['item_name']
        quantity = request.form['quantity']
        category = request.form['category']
        location = request.form['location']
        status = request.form['status']
        
        error = None
        
        if not item_name:
            error = 'Item name is required.'
        elif not quantity:
            error = 'Quantity is required.'
        elif not category:
            error = 'Category is required.'
        elif not location:
            error = 'Location is required.'
        elif not status:
            error = 'Status is required.'
            
        if error is None:
            CollegeInventory.create(
                item_name=item_name,
                quantity=int(quantity),
                category=category,
                location=location,
                status=status,
                added_by=g.user['user_id']
            )
            
            flash('Inventory item added successfully!', 'success')
            return redirect(url_for('routes.inventory'))
            
        flash(error, 'error')
        
    return render_template('add_inventory.html')

@bp.route('/edit_inventory/<int:inventory_id>', methods=('GET', 'POST'))
@admin_required
def edit_inventory(inventory_id):
    inventory_item = CollegeInventory.get_by_id(inventory_id)
    
    if not inventory_item:
        flash('Inventory item not found.', 'error')
        return redirect(url_for('routes.inventory'))
    
    if request.method == 'POST':
        item_name = request.form['item_name']
        quantity = request.form['quantity']
        category = request.form['category']
        location = request.form['location']
        status = request.form['status']
        
        error = None
        
        if not item_name:
            error = 'Item name is required.'
        elif not quantity:
            error = 'Quantity is required.'
        elif not category:
            error = 'Category is required.'
        elif not location:
            error = 'Location is required.'
        elif not status:
            error = 'Status is required.'
            
        if error is None:
            CollegeInventory.update(
                inventory_id=inventory_id,
                item_name=item_name,
                quantity=int(quantity),
                category=category,
                location=location,
                status=status
            )
            
            flash('Inventory item updated successfully!', 'success')
            return redirect(url_for('routes.inventory'))
            
        flash(error, 'error')
        
    return render_template('edit_inventory.html', inventory_item=inventory_item)

@bp.route('/delete_inventory/<int:inventory_id>', methods=('POST',))
@admin_required
def delete_inventory(inventory_id):
    inventory_item = CollegeInventory.get_by_id(inventory_id)
    
    if not inventory_item:
        flash('Inventory item not found.', 'error')
    else:
        CollegeInventory.delete(inventory_id)
        flash('Inventory item deleted successfully!', 'success')
    
    return redirect(url_for('routes.inventory'))

@bp.route('/user_profile')
@login_required
def user_profile():
    return render_template('user_profile.html', user=g.user)

@bp.route('/edit_profile', methods=('GET', 'POST'))
@login_required
def edit_profile():
    if request.method == 'POST':
        # Get form data - only use fields we know are in the database
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        contact_number = request.form.get('contact_number')
        
        error = None
        
        # Validate required fields
        if not email:
            error = 'Email is required.'
        elif not full_name:
            error = 'Full name is required.'
        
        # Check if email is already used by another user
        if not error and email != g.user['email']:
            existing_user = User.get_by_email(email)
            if existing_user and existing_user['user_id'] != g.user['user_id']:
                error = f"Email {email} is already registered."
                
        if error is None:
            try:
                # Update user profile with only the fields supported by the model
                # Check the actual implementation of User.update() to see what fields it supports
                success = User.update(
                    user_id=g.user['user_id'],
                    email=email,
                    full_name=full_name,
                    contact_number=contact_number
                )
                
                if success:
                    # Refresh user data in session
                    g.user = User.get_by_id(g.user['user_id'])
                    flash('Profile updated successfully!', 'success')
                else:
                    flash('No changes were made to your profile.', 'info')
                
                return redirect(url_for('routes.user_profile'))
            except Exception as e:
                error = f"Database error: {e}"
                
        flash(error, 'error')
        
    # For GET requests or if form submission fails
    return render_template('edit_profile.html', user=g.user)
@bp.route('/change_password', methods=('GET', 'POST'))
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        error = None
        
        # Verify current password
        user = User.verify_password(g.user['username'], current_password)
        if not user:
            error = 'Current password is incorrect.'
        elif not new_password:
            error = 'New password is required.'
        elif new_password != confirm_password:
            error = 'New passwords do not match.'
        elif current_password == new_password:
            error = 'New password must be different from current password.'
            
        if error is None:
            # Update password
            User.update_password(g.user['user_id'], new_password)
            flash('Password changed successfully!', 'success')
            return redirect(url_for('routes.user_profile'))
            
        flash(error, 'error')
        
    return render_template('change_password.html')
# Register the blueprint to the Flask application
def init_app(app):
    app.register_blueprint(bp)
    
    # Before request handler to load logged-in user
    @app.before_request
    def load_logged_in_user():
        user_id = session.get('user_id')
        
        if user_id is None:
            g.user = None
        else:
            g.user = User.get_by_id(user_id)
