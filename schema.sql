-- Drop database if exists and create new one
DROP DATABASE IF EXISTS campus_marketplace;
CREATE DATABASE campus_marketplace;
USE campus_marketplace;

-- Users table (both students and admins)
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    user_type ENUM('student', 'admin') NOT NULL DEFAULT 'student',
    contact_number VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Items table
CREATE TABLE items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    condition_status VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2),
    is_available BOOLEAN DEFAULT TRUE,
    owner_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Borrow requests table
CREATE TABLE borrow_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    requester_id INT NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_date TIMESTAMP NULL,
    return_date DATE NULL,
    notes TEXT,
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE,
    FOREIGN KEY (requester_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- College inventory table
CREATE TABLE college_inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    category VARCHAR(50) NOT NULL,
    location VARCHAR(100),
    status VARCHAR(50) DEFAULT 'available',
    added_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (added_by) REFERENCES users(user_id)
);

-- Insert an admin user (password: admin123)
INSERT INTO users (username, email, password, full_name, user_type, contact_number) 
VALUES ('admin', 'admin@campus.edu', 'pbkdf2:sha256:150000$aNUkfD9v$15e5a85de5c955e7c34c61a684cea4db930c95f308d2e042125cb3a80a5a9d92', 'Admin User', 'admin', '9876543210');
