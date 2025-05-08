import mysql.connector
from flask import current_app, g
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=current_app.config['MYSQL_HOST'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASSWORD'],
            database=current_app.config['MYSQL_DB']
        )
        g.cursor = g.db.cursor(dictionary=True)
    return g.db, g.cursor

def close_db(e=None):
    db = g.pop('db', None)
    cursor = g.pop('cursor', None)
    
    if cursor is not None:
        cursor.close()
    
    if db is not None:
        db.close()

class User:
    @staticmethod
    def get_by_id(user_id):
        db, cursor = get_db()
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        return user
    
    @staticmethod
    def get_by_username(username):
        db, cursor = get_db()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        return user
    
    @staticmethod
    def get_by_email(email):
        db, cursor = get_db()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        return user
    
    @staticmethod
    def create(username, email, password, full_name, contact_number=None, user_type='student'):
        db, cursor = get_db()
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        cursor.execute(
            "INSERT INTO users (username, email, password, full_name, contact_number, user_type) VALUES (%s, %s, %s, %s, %s, %s)",
            (username, email, hashed_password, full_name, contact_number, user_type)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def verify_password(username, password):
        user = User.get_by_username(username)
        if user and check_password_hash(user['password'], password):
            return user
        return None
    
    @staticmethod
    def get_all_students():
        db, cursor = get_db()
        cursor.execute("SELECT * FROM users WHERE user_type = 'student' ORDER BY created_at DESC")
        return cursor.fetchall()
    
    @staticmethod
    def update(user_id, email=None, full_name=None, contact_number=None):
        db, cursor = get_db()
        updates = []
        params = []
        
        if email:
            updates.append("email = %s")
            params.append(email)
        
        if full_name:
            updates.append("full_name = %s")
            params.append(full_name)
        
        if contact_number:
            updates.append("contact_number = %s")
            params.append(contact_number)
        
        if not updates:
            return False
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
        params.append(user_id)
        
        cursor.execute(query, tuple(params))
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def update_password(user_id, new_password):
        """Update user password"""
        db, cursor = get_db()
        
        # Hash the new password
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        
        # Update the password
        cursor.execute(
            "UPDATE users SET password = %s WHERE user_id = %s",
            (hashed_password, user_id)
        )
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete(user_id):
        db, cursor = get_db()
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        db.commit()
        return cursor.rowcount > 0

class Item:
    @staticmethod
    def create(title, description, category, condition_status, price, owner_id):
        db, cursor = get_db()
        cursor.execute(
            "INSERT INTO items (title, description, category, condition_status, price, owner_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (title, description, category, condition_status, price, owner_id)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_by_id(item_id):
        db, cursor = get_db()
        cursor.execute("""
            SELECT i.*, u.username as owner_name 
            FROM items i
            JOIN users u ON i.owner_id = u.user_id
            WHERE i.item_id = %s
        """, (item_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_all():
        db, cursor = get_db()
        cursor.execute("""
            SELECT i.*, u.username as owner_name 
            FROM items i
            JOIN users u ON i.owner_id = u.user_id
            ORDER BY i.created_at DESC
        """)
        return cursor.fetchall()
    
    @staticmethod
    def get_by_owner(owner_id):
        db, cursor = get_db()
        cursor.execute("""
            SELECT i.*, u.username as owner_name 
            FROM items i
            JOIN users u ON i.owner_id = u.user_id
            WHERE i.owner_id = %s
            ORDER BY i.created_at DESC
        """, (owner_id,))
        return cursor.fetchall()
    
    @staticmethod
    def update(item_id, title=None, description=None, category=None, condition_status=None, price=None, is_available=None):
        db, cursor = get_db()
        updates = []
        params = []
        
        if title:
            updates.append("title = %s")
            params.append(title)
        
        if description:
            updates.append("description = %s")
            params.append(description)
        
        if category:
            updates.append("category = %s")
            params.append(category)
        
        if condition_status:
            updates.append("condition_status = %s")
            params.append(condition_status)
        
        if price is not None:
            updates.append("price = %s")
            params.append(price)
        
        if is_available is not None:
            updates.append("is_available = %s")
            params.append(is_available)
        
        if not updates:
            return False
        
        query = f"UPDATE items SET {', '.join(updates)} WHERE item_id = %s"
        params.append(item_id)
        
        cursor.execute(query, tuple(params))
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete(item_id):
        db, cursor = get_db()
        cursor.execute("DELETE FROM items WHERE item_id = %s", (item_id,))
        db.commit()
        return cursor.rowcount > 0

class BorrowRequest:
    @staticmethod
    def create(item_id, requester_id, notes=None):
        db, cursor = get_db()
        cursor.execute(
            "INSERT INTO borrow_requests (item_id, requester_id, notes) VALUES (%s, %s, %s)",
            (item_id, requester_id, notes)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_by_id(request_id):
        db, cursor = get_db()
        cursor.execute("""
            SELECT br.*, i.title as item_title, u.username as requester_name
            FROM borrow_requests br
            JOIN items i ON br.item_id = i.item_id
            JOIN users u ON br.requester_id = u.user_id
            WHERE br.request_id = %s
        """, (request_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_all():
        db, cursor = get_db()
        cursor.execute("""
            SELECT br.*, i.title as item_title, u.username as requester_name
            FROM borrow_requests br
            JOIN items i ON br.item_id = i.item_id
            JOIN users u ON br.requester_id = u.user_id
            ORDER BY br.request_date DESC
        """)
        return cursor.fetchall()
    
    @staticmethod
    def get_by_requester(requester_id):
        db, cursor = get_db()
        cursor.execute("""
            SELECT br.*, i.title as item_title, u.username as owner_name
            FROM borrow_requests br
            JOIN items i ON br.item_id = i.item_id
            JOIN users u ON i.owner_id = u.user_id
            WHERE br.requester_id = %s
            ORDER BY br.request_date DESC
        """, (requester_id,))
        return cursor.fetchall()
    
    @staticmethod
    def get_by_item_owner(owner_id):
        db, cursor = get_db()
        cursor.execute("""
            SELECT br.*, i.title as item_title, u.username as requester_name
            FROM borrow_requests br
            JOIN items i ON br.item_id = i.item_id
            JOIN users u ON br.requester_id = u.user_id
            WHERE i.owner_id = %s
            ORDER BY br.request_date DESC
        """, (owner_id,))
        return cursor.fetchall()
    
    @staticmethod
    def update_status(request_id, status, return_date=None):
        db, cursor = get_db()
        cursor.execute(
            "UPDATE borrow_requests SET status = %s, response_date = NOW(), return_date = %s WHERE request_id = %s",
            (status, return_date, request_id)
        )
        db.commit()
        return cursor.rowcount > 0

class CollegeInventory:
    @staticmethod
    def create(item_name, quantity, category, location, status, added_by):
        db, cursor = get_db()
        cursor.execute(
            "INSERT INTO college_inventory (item_name, quantity, category, location, status, added_by) VALUES (%s, %s, %s, %s, %s, %s)",
            (item_name, quantity, category, location, status, added_by)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_by_id(inventory_id):
        db, cursor = get_db()
        cursor.execute("""
            SELECT ci.*, u.username as added_by_name 
            FROM college_inventory ci
            JOIN users u ON ci.added_by = u.user_id
            WHERE ci.inventory_id = %s
        """, (inventory_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_all():
        db, cursor = get_db()
        cursor.execute("""
            SELECT ci.*, u.username as added_by_name 
            FROM college_inventory ci
            JOIN users u ON ci.added_by = u.user_id
            ORDER BY ci.created_at DESC
        """)
        return cursor.fetchall()
    
    @staticmethod
    def update(inventory_id, item_name=None, quantity=None, category=None, location=None, status=None):
        db, cursor = get_db()
        updates = []
        params = []
        
        if item_name:
            updates.append("item_name = %s")
            params.append(item_name)
        
        if quantity:
            updates.append("quantity = %s")
            params.append(quantity)
        
        if category:
            updates.append("category = %s")
            params.append(category)
        
        if location:
            updates.append("location = %s")
            params.append(location)
        
        if status:
            updates.append("status = %s")
            params.append(status)
        
        if not updates:
            return False
        
        query = f"UPDATE college_inventory SET {', '.join(updates)} WHERE inventory_id = %s"
        params.append(inventory_id)
        
        cursor.execute(query, tuple(params))
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete(inventory_id):
        db, cursor = get_db()
        cursor.execute("DELETE FROM college_inventory WHERE inventory_id = %s", (inventory_id,))
        db.commit()
        return cursor.rowcount > 0