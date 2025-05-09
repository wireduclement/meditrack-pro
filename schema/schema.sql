CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255),
    password VARCHAR(255),
    role ENUM('Admin', 'Pharmacist', 'Cashier'),
    contact_info VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_info (
    user_info_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    middle_name VARCHAR(100),
    dob DATE,
    email_address VARCHAR(100),
    gender VARCHAR(10),
    home_address VARCHAR(100),
    marital_status VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    brand VARCHAR(100),
    category VARCHAR(100),
    price DECIMAL(10, 2),
    quantity_in_stock INT,
    expiry_date DATE,
    manufacturer VARCHAR(100)
);

CREATE TABLE sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    attendant VARCHAR(100),
    customer_name VARCHAR(100),
    invoice_number VARCHAR(100),
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(10, 2),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    fullname VARCHAR(100),
    contact_info VARCHAR(100),
    email VARCHAR(100),
    address VARCHAR(100),
    payment_method VARCHAR(50),
);
