<h1>⚖️ Disclaimer & Intellectual Property</h1>

ShopSphere is a 7th Semester academic project developed for educational and learning purposes only. It is a demonstration e-commerce application and is not a real online store.The project may contain references to real-world brand names, product names, logos, trademarks, and other intellectual property belonging to their respective owners, including but not limited to Myntra, HP, Dell, Pigeon, Levi's, and other brands. Such references are used solely for identification, demonstration, and educational purposes.ShopSphere is not affiliated with, sponsored by, endorsed by, or officially associated with any of the mentioned companies or brands.All product prices, specifications, descriptions, inventory information, and other product data displayed in the application are demonstration data and should not be considered actual commercial information.The product images used in ShopSphere are AI-generated images created for this educational project and are used for demonstration purposes.This project is not intended to represent an official store or commercial service of any brand.

<h1>ShopSphere 🛒</h1>

ShopSphere is a full-stack e-commerce web application developed as a 7th Semester academic project using Python, Django, PostgreSQL, and Django REST Framework.

The project demonstrates the design and implementation of a complete e-commerce workflow, including product management, authentication, shopping cart, wishlist, coupons, checkout, orders, demo payments, reviews, inventory management, REST APIs, security practices, and automated testing.

<h1>📌 Project Overview</h1>

ShopSphere is designed to simulate the core functionality of a modern e-commerce platform.

The application provides separate functionality for customers and administrators. Customers can browse products, manage their accounts, add products to a cart or wishlist, apply coupons, place orders, make demo/test payments or select Cash on Delivery, and submit reviews for products they have purchased.

The backend is powered by Django and PostgreSQL, while Django REST Framework provides a dedicated REST API layer.

<h1>✨ Key Features</h1>
<h2>Product Catalog</h2>
Product listing and product detail pages

Categories and brands

Product variants

Product images

SKU management

Product search

Category and brand filtering

Price sorting

Pagination

Product availability and inventory information

<h2>User Accounts</h2>

User registration and login

Logout

User profiles

Phone number management

Shipping and billing addresses

Default address support

Authentication-protected features

<h2>Shopping Cart</h2>

Add product variants to cart

Increase/decrease quantities

Remove cart items

Stock validation

Automatic subtotal calculation

Discount calculation

Final order total

<h2>Wishlist</h2>

Add products to wishlist

Remove products from wishlist

Prevent duplicate wishlist items

Authentication-protected wishlist

<h2>Coupons & Discounts</h2>

Percentage-based discounts

Fixed-amount discounts

Minimum order amount

Coupon validity period

Usage limits

Per-user usage limits

Coupon application and removal

Coupon usage tracking

<h2>Checkout & Orders</h2>

Checkout workflow

Shipping and billing information

Order creation

Order item snapshots

Order confirmation

Order history

Order detail pages

Order status management

<h2>Payment Simulation</h2>
ShopSphere includes a Demo/Test Payment workflow rather than a real payment gateway.
It supports:
Demo Card success

Demo Card failure

Payment retry after failure

Cash on Delivery

Payment status tracking

Payment reference tracking

Inventory finalization after successful payment/order confirmation

**No real financial transactions are processed by the application.**

<h2>Inventory Management</h2>

Variant-level inventory

Stock quantity tracking

Low-stock threshold

Stock validation during cart and checkout operations

Inventory deduction during order finalization

Protection against duplicate inventory deduction

<h2>Reviews & Ratings</h2>

Product ratings from 1–5

Review title and comments

Verified-purchase review eligibility

One review per user per product

Review editing and deletion

Average rating calculation

Rating distribution

<h2>REST API</h2>

ShopSphere provides REST APIs using Django REST Framework for:

Products

Product details

Categories

Brands

Cart

Wishlist

Coupons

Orders

Product reviews

The API also applies authentication and permission controls to protected resources.

<h2>Security</h2>
The project includes:

Environment-based configuration

Password validation

CSRF protection

Session authentication

Authentication-protected views

Authorization checks for user-owned data

Secure cookie configuration for production

MIME-sniffing protection

Clickjacking protection

Referrer policy

Conditional HSTS configuration for production

Automated Testing

ShopSphere includes automated Django tests covering important application functionality.

The current test suite contains 19 automated tests, including tests for:
Product and inventory behavior

Cart calculations

Coupons

Wishlist

Orders

Demo payment success and failure

Cash on Delivery

Inventory deduction

Duplicate payment/inventory protection

Order access control

Reviews

REST API access and authentication

The test suite was successfully executed with:

Found 19 test(s).

System check identified no issues (0 silenced).

Ran 19 tests

OK

<h1>🛠️ Technology Stack</h1>
<h2>Backend</h2>

Python

Django

Django REST Framework
<h2>Database</h2>
PostgreSQL
<h2>Frontend</h2>
HTML5

CSS3

JavaScript

Bootstrap/Django templates
<h2>Development Tools</h2>
Git

GitHub

Visual Studio Code
<h2>Additional Python Packages</h2>
psycopg

python-dotenv

Pillow

<h1>🏗️ Application Architecture</h1>

ShopSphere follows a Django-based full-stack architecture.

                    ┌─────────────────────┐
                    │       Browser       │
                    │   HTML/CSS/JS UI    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       Django        │
                    │ Views / Templates   │
                    │ Authentication      │
                    │ Business Logic      │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
       ┌──────────────────┐        ┌──────────────────┐
       │ Django REST API  │        │     Services     │
       │      (DRF)       │        │ Cart / Orders /  │
       │                  │        │ Coupons / etc.   │
       └────────┬─────────┘        └────────┬─────────┘
                │                           │
                └─────────────┬─────────────┘
                              ▼
                    ┌─────────────────────┐
                    │     PostgreSQL      │
                    │       Database      │
                    └─────────────────────┘
                    
📁 Main Project Structure
ShopSphere/

│
├── accounts/          # User profiles, authentication and addresses

|
├── api/               # Django REST Framework API

|
├── cart/              # Shopping cart

|
├── coupons/           # Coupons and discount logic

|
├── orders/            # Checkout, orders and payment workflow

|
├── products/          # Products, variants and inventory

|
├── reviews/           # Product reviews and ratings

|
├── wishlist/          # Wishlist functionality

│
├── config/            # Django project configuration

│
├── templates/         # HTML templates

|
├── static/            # CSS and static assets

|
├── media/             # Uploaded product media

│
├── manage.py

|
├── requirements.txt

|
├── .env.example

|
├── .gitignore

|
└── README.md


<h1>🔌 REST API</h1>
The API is available under:

/api/

Main API Endpoints

/api/

/api/products/

/api/products/<slug>/

/api/categories/

/api/brands/

/api/cart/

/api/cart/add/

/api/cart/update/

/api/cart/remove/

/api/wishlist/

/api/wishlist/add/

/api/wishlist/remove/

/api/coupons/

/api/cart/coupon/

/api/cart/coupon/remove/

/api/orders/

/api/orders/<order_number>/

/api/products/<product_id>/reviews/

/api/products/<product_id>/reviews/create/

/api/reviews/<id>/

/api/reviews/<id>/delete/

The project uses Django REST Framework's session authentication and permission system.

<h1>💳 Payment Disclaimer</h1>
ShopSphere does not process real payments.

The Demo Card payment option is implemented solely to demonstrate an e-commerce payment workflow, including successful payments, failed payments, retries, payment status handling, and order finalization.

Cash on Delivery is also provided as a simulated order/payment option.

No real financial transactions are performed.


<h1>🎓 Academic Project</h1>

ShopSphere was developed as a 7th Semester academic project to gain practical experience in:

Full-stack web development

Python and Django

Database design

PostgreSQL

REST API development

Authentication and authorization

E-commerce business logic

Transaction handling

Inventory management

Secure application configuration

Automated software testing

Git and GitHub

<h1>🚀 Future Enhancments</h1>

Possible future enhancements include:

Production deployment

Production email service

Advanced frontend frameworks

Additional monitoring and analytics

Adding React to frontend.


<h1>📄 License / Usage</h1>
This repository is intended primarily as an educational and academic portfolio project.

The ShopSphere source code is provided for learning and demonstration purposes. Third-party brand names, trademarks, product references, and other intellectual property remain the property of their respective owners.



<h1>👩‍💻 Developer </h1>

POOJA G

Academic project — 7th Semester

<h1>SCREENSHOTS</h1>
<h2>LOGIN PAGE</h2>
![image alt](https://github.com/poojaagee/ShopSphere/blob/50856149577aefc1fe03d2d4ee0cc2196b181143/Login%20Page.png)






