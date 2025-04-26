from flask import Flask, render_template, request, redirect, url_for, flash, session, flash, send_from_directory
from functools import wraps
from flask_bootstrap import Bootstrap5
from flask.views import MethodView
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, EmailField, PasswordField, RadioField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Regexp, Length, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from db import Database
from dotenv import load_dotenv
from pdf import generate_invoice_pdf
from datetime import datetime, date
import os


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
Bootstrap5(app)


db = Database("localhost", "root", "", "pharmacy_management")
TODAY = date.today()


class ProductForm(FlaskForm):
    pd_name = StringField("Name", validators=[DataRequired()])
    pd_brand = StringField("Brand", validators=[DataRequired()])
    pd_category = SelectField("Category", choices=["Medication", "Health & Wellness", "Baby Care", "Medical Equipment", "Hygiene Products", "Dietary Needs"], validators=[DataRequired()])
    pd_price = StringField("Price (₵)", validators=[DataRequired()])
    pd_quantity = StringField("Quantity", validators=[DataRequired()])
    pd_expiry_date = DateField("Expiry Date", format='%Y-%m-%d', validators=[DataRequired()])
    pd_manufacturer = StringField("Manufacturer", validators=[DataRequired()])
    submit = SubmitField("Submit")


class UsersForm(FlaskForm):
    user_name = StringField("Name", validators=[DataRequired()])
    user_email = EmailField("Email", validators=[DataRequired()],  render_kw={"placeholder": "example@example.com"})
    user_pwd = PasswordField("Password", validators=[DataRequired(), Length(min=7, message="Password must be at least 7 characters long")])
    user_c_pwd = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('user_pwd', message="Passwords must match")])
    user_role = SelectField("Role", choices=[("Admin", "Admin"), ("Pharmacist", "Pharmacist"), ("Cashier", "Cashier")], validators=[DataRequired()])
    user_contact = StringField("Contact Info", validators=[DataRequired(), Regexp(r'^\+?\d{10,15}$', message="Invalid phone number format.")], render_kw={"placeholder": "(000) 000-0000"})
    submit = SubmitField("Register")


class EditUserForm(FlaskForm):
    user_name = StringField("Name", validators=[DataRequired()])
    user_email = EmailField("Email", validators=[DataRequired()],  render_kw={"placeholder": "example@example.com"})
    user_contact = StringField("Contact Info", validators=[DataRequired(), Regexp(r'^\+?\d{10,15}$', message="Invalid phone number format.")])
    submit = SubmitField("Update")


class UserInfoForm(FlaskForm):
    ui_fname = StringField("First Name", validators=[DataRequired()])
    ui_lname = StringField("Last Name", validators=[DataRequired()])
    ui_mname = StringField("Middle Name", validators=[DataRequired()])
    ui_dob = DateField("Date Of Birth", format='%Y-%m-%d', validators=[DataRequired()])
    ui_email = EmailField("Email", validators=[DataRequired()], render_kw={"placeholder": "example@example.com"})
    ui_gender = SelectField("Gender", choices=[("Male", "Male"), ("Female", "Female")], validators=[DataRequired()])
    ui_home_address = StringField("Home Address", validators=[DataRequired()])
    ui_marital_status = SelectField("Marital Status", choices=[("Single", "Single"), ("Married", "Married"), ("Divorced", "Divorced"), ("Separated", "Separated")], validators=[DataRequired()])
    submit = SubmitField("Add Information")


class CustomerForm(FlaskForm):
    c_fullname = StringField("Full Name", validators=[DataRequired()])
    c_phone = StringField("Contact Info", validators=[DataRequired(), Regexp(r'^\+?\d{10,15}$', message="Invalid phone number format.")], render_kw={"placeholder": "(000) 000-0000"})
    c_email = EmailField("Email", validators=[Optional()], render_kw={"placeholder": "example@example.com"})
    c_address = StringField("Home Address (optional)", validators=[Optional()])
    c_payment_method = RadioField("Preferred Payment Method", choices=[("insurance","Insurance"), ("cash","Cash"), ("mobile_money","Mobile Money"), ("bank_transfer", "Bank Transfer")], validators=[DataRequired()])
    c_comments = TextAreaField("Additional Instruction or Comments", validators=[DataRequired()], render_kw={"class": "form-control", "rows": 5})
    submit = SubmitField("Confirm Order")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("You must log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get("role") not in roles:
                flash("You do not have permission to access that page.", "danger")
                return redirect(request.referrer or url_for("dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def get_name_role():
    name = session.get("name", "User")
    role = session.get("role", "Admin")
    return name, role


class LoginView(MethodView):
    def get(self):
        return render_template("login.html")
    
    def post(self):
        email = request.form["email"]
        password = request.form["password"]

        result = db.read("users", clause={"email": email}, columns=["password", "name", "role"])
        
        if result:
            stored_password, name, role = result[0]
            
            if check_password_hash(stored_password, password):
                session['logged_in'] = True
                session['name'] = name
                session['role'] = role
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid email or password, please try again.", "danger")
        else:
            flash("User not found. Please register.", "danger")
    
        return render_template("login.html")


class DashboardView(MethodView):
    decorators = [login_required]

    def get(self):
        total_products = db.count_rows("products")
        if not session.get('logged_in'):
            return redirect(url_for("login"))
        name, role = get_name_role()

        daily_sales = db.read("sales", [("DATE(date)", str(TODAY))])
        daily_sales_total = sum(float(sale[6]) for sale in daily_sales)

        # products = db.read("products", [("DATE(date)", str(today))])
        # expired_product = [for product in products if product]

        return render_template("dashboard.html", name=name, role=role, total_products=total_products, daily_sales_total=daily_sales_total)
    

class AddView(MethodView):
    decorators = [login_required, role_required(["Admin", "Pharmacist"])]

    def get(self):
        form = ProductForm()
        name, role = get_name_role()
        return render_template("add.html", form=form, name=name, role=role)
    
    def post(self):
        form = ProductForm()
        if form.validate_on_submit():
            columns = ["name", "brand", "category", "price", "quantity_in_stock", "expiry_date", "manufacturer"]  
            values = [
                form.pd_name.data,
                form.pd_brand.data,
                form.pd_category.data,
                form.pd_price.data,
                form.pd_quantity.data,
                form.pd_expiry_date.data.strftime('%Y-%m-%d'),
                form.pd_manufacturer.data   
            ]
            db.insert("products", columns, values)

            flash("Product added successfully.", "info")
            return redirect(url_for("add"))
        return render_template("add.html", form=form)
    

class EditProductView(MethodView):
    decorators = [login_required, role_required(["Admin", "Pharmacist"])]

    def get(self, product_id):
        name, role = get_name_role()
        form = ProductForm()
        product = db.read("products", {"product_id": product_id})

        if product:
            form.pd_name.data = product[0][1]
            form.pd_brand.data = product[0][2]
            form.pd_category.data = product[0][3]
            form.pd_price.data = product[0][4]
            form.pd_quantity.data = product[0][5]
            form.pd_expiry_date.data = product[0][6]
            form.pd_manufacturer.data = product[0][7]
        else:
            flash("Product not found.", "danger")
            return redirect(url_for("products"))
        return render_template("edit_product.html", form=form, name=name, role=role)
    
    def post(self, product_id):
        name, role = get_name_role()
        form = ProductForm()

        if form.validate_on_submit():
            db.update(
                "products", 
                {
                "name": form.pd_name.data,
                "brand": form.pd_brand.data,
                "category": form.pd_category.data,
                "price": form.pd_price.data,
                "quantity_in_stock": form.pd_quantity.data,
                "expiry_date": form.pd_expiry_date.data.strftime('%Y-%m-%d'),
                "manufacturer": form.pd_manufacturer.data
                }, 
                {"product_id": product_id}
            )
            flash("Product updated successfully.", "success")
            return redirect(url_for("products"))
        return render_template("edit_product.html", form=form, name=name, role=role)


class ProductView(MethodView):
    decorators = [login_required, role_required(["Admin", "Pharmacist"])]

    def get(self):
        search_query = request.args.get("search", "").strip()
        name, role = get_name_role()
        if search_query:
            products = db.read("products", {"name": f"%{search_query}%"}, like=True)
        else:
            products = db.read("products")

        # notify expired products with red column bg
        # processed_products = []
        # for product in products:
        #     expiry_date = product[6]
        #     is_expired = expiry_date <= TODAY
        #     processed_products.append(list(product) + [is_expired])

        return render_template("products.html", products=products, name=name, role=role, search_query=search_query)


class OrdersView(MethodView):
    decorators = [login_required, role_required(["Admin", "Pharmacist"])]

    def get(self):
        name, role = get_name_role()
        form = CustomerForm()
        cart_items = session.get("cart", [])
        
        if not cart_items:
            flash("Your cart is empty. Please add items before proceeding.", "danger")
            return redirect(url_for("cart"))

        return render_template("orders.html", name=name, role=role, form=form, cart_items=cart_items)

    def post(self):
        name, role = get_name_role()
        form = CustomerForm()

        if form.validate_on_submit():
            cart_items = session.get("cart", [])
            if not cart_items:
                flash("Your cart is empty. Please add items before proceeding.", "danger")
                return redirect(url_for("cart"))

            customer = {
                "fullname": form.c_fullname.data,
                "contact_info": form.c_phone.data,
                "email": form.c_email.data,
                "address": form.c_address.data,
                "payment_method": form.c_payment_method.data,
            }

            invoice_number = f"INV{int(datetime.now().timestamp())}"
            total = sum(item["total_price"] for item in cart_items)
            comments = form.c_comments.data

            user = db.read("users", {"name": name})
            if not user:
                flash("User not found")
                return redirect(url_for("orders"))
            user_id = user[0][0]

            try:
                for item in cart_items:
                    product_id = item["id"]
                    quantity_purchased = item["quantity"]
                    
                    product = db.read("products", {"product_id": product_id})
                    if product:
                        current_stock = product[0][5]                
                        new_stock = max(0, current_stock - quantity_purchased) 
                        db.update("products", {"quantity_in_stock": new_stock}, {"product_id": product_id})

                pdf_path = generate_invoice_pdf(customer, cart_items, invoice_number, comments)

                db.insert("customers", list(customer.keys()), list(customer.values()))

                columns = ["user_id", "attendant", "customer_name", "invoice_number", "date", "total"]
                values = [user_id, name, form.c_fullname.data, invoice_number, datetime.now(), float(total)]
                db.insert("sales", columns, values)

                session.pop("cart", None)

                flash("Order confirmed! Invoice generated.", "success")
                return redirect(url_for("cart"))

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Full error details:\n{error_details}")
                flash(f"Error processing order: {str(e)}", "danger")

        cart_items = session.get("cart", [])
        return render_template("orders.html", name=name, role=role, form=form, cart_items=cart_items, user_id=user_id)   


class CartView(MethodView):
    decorators = [login_required, role_required(["Admin", "Pharmacist"])]

    def get(self):
        name, role = get_name_role()
        cart_items = session.get("cart", [])
        grand_total = sum(item["total_price"] for item in cart_items)
        search_query = request.args.get("search", "").strip()
        product_details = None

        if search_query:
            products = db.read("products", {"name": f"%{search_query}%"}, like=True)

            if products:
                product = products[0]
                product_details = {
                    "name": product[0],
                    "price": float(product[4]),
                    "manufacturer": product[6],
                    "expiry_date": product[5]
                }

        product_names = db.read("products", columns=["name"])
        product_names = [p[0] for p in product_names] if product_names else []

        return render_template(
            "cart.html", 
            product_details=product_details, 
            product_names=product_names, 
            cart_items=cart_items,
            grand_total=grand_total,
            name=name, 
            role=role, 
            search_query=search_query
            )


class AddToCartView(MethodView):
    decorators = [login_required, role_required(["Admin", "Pharmacist"])]

    def post(self):
        product_name = request.form.get("product_name")
        quantity = int(request.form.get("quantity", 1))

        if not product_name:
            flash("Please select a product", "danger")
            return redirect(url_for("cart"))
        
        product = db.read("products", {"name": product_name})
        if not product:
            flash("Product not found", "danger")
            return redirect(url_for("cart"))
        
        product_data = product[0]
        current_stock = product_data[5]  
        price = float(product_data[4]) 
        
        # not done
        if quantity > current_stock:
            flash(f"Not enough stock for {product_name}. Only {current_stock} available", "warning")
            return redirect(url_for("cart"))
        
        total_price = price * quantity

        cart_items = session.get("cart", [])
        cart_items.append({
            "id": product_data[0],
            "name": product_name, 
            "price": price, 
            "quantity": quantity, 
            "total_price": total_price
        })
        session["cart"] = cart_items
        flash("Item added to cart successfully", "success")

        return redirect(url_for("cart"))


class RemoveFromCart(MethodView):
    decorators = [login_required, role_required(["Admin", "Pharmacist"])]

    def post(self):
        product_name = request.form.get("product_name")
        cart_items = session.get("cart", [])
        cart_items = [item for item in cart_items if item["name"] != product_name]
        session["cart"] = cart_items
        return redirect(url_for("cart"))   


class SalesView(MethodView):
    decorators = [login_required, role_required(["Admin", "Cashier"])]

    def get(self):
        name, role = get_name_role()
        sales_data = db.read("sales")
        return render_template("sales.html", name=name, role=role, sales_data=sales_data)

  
@app.route('/invoices/<filename>')
def serve_invoice(filename):
    invoice_path = os.path.join('static', 'invoices')
    return send_from_directory(invoice_path, filename)
    

@app.route("/reports")
@login_required
@role_required(["Admin", "Cashier"])
def reports():
    name, role = get_name_role()
    return render_template("reports.html", name=name, role=role)


class SettingsView(MethodView):
    decorators = [login_required, role_required(["Admin"])]

    def get(self):
        return redirect(url_for("edit_users"))


class EditUsersView(MethodView):
    decorators = [login_required, role_required(["Admin"])]

    def get(self, user_id=None):
        name, role = get_name_role()

        if user_id:
            form = EditUserForm()
            user = db.read("users", {"user_id": user_id})

            if user:
                form.user_name.data = user[0][1]
                form.user_email.data = user[0][2]
                form.user_contact.data = user[0][5]
            else:
                flash("User not found.", "danger")
                return redirect(url_for("edit_users"))
            return render_template("edit_user.html", form=form, name=name, role=role)

        else:
            users = db.read("users")
            return render_template("settings.html", active_section="edit_users", users=users, name=name, role=role)
        
    def post(self, user_id):
        form = EditUserForm()

        if form.validate_on_submit():
            db.update(
                "users", 
                {
                    "name": form.user_name.data,
                    "email": form.user_email.data,
                    "contact_info": form.user_contact.data
                }, 
                {"user_id": user_id}
            )
            flash("User updated successfully.", "success")
            return redirect(url_for("edit_users"))
        return render_template("edit_user.html", form=form)


@app.route("/delete-user/<int:user_id>")
@login_required
@role_required(["Admin"])
def delete_user(user_id):
    name, role = get_name_role()
    user = db.read("users", {"user_id": user_id})
    if user:
        db.delete("users", {"user_id": user_id})
        flash("User deleted successfully", "success")
    else:
        flash("User not found", "danger")
        return redirect(url_for("settings"))
    form = EditUserForm()
    users = db.read("users")
    return render_template("settings.html", active_section="edit_users", form=form, users=users, name=name, role=role)



class SetupProfileView(MethodView):
    decorators = [login_required, role_required(["Admin"])]

    def get(self):
        name, role = get_name_role()
        form = UsersForm()
        return render_template("settings.html", active_section="setup_profile", form=form, name=name, role=role)
    
    def post(self):
        name, role = get_name_role()
        form = UsersForm()

        role = form.user_role.data if form.user_role.data in ["Admin", "Pharmacist", "Cashier"] else "Admin"

        if form.validate_on_submit():
            existing_user = db.read("users", {"email": form.user_email.data})
            if existing_user:
                flash("This email address is already in use. Please choose a different email", "danger")
            else:
                hashed_password = generate_password_hash(form.user_pwd.data, method='pbkdf2:sha256', salt_length=16)
                columns = ["name", "email", "password", "role", "contact_info"]
                values = [
                    form.user_name.data,
                    form.user_email.data,
                    hashed_password,
                    role,
                    form.user_contact.data
                ]
                db.insert("users", columns, values)

                flash("User added successfully.", "info")
                return redirect(url_for("settings"))
        return render_template("settings.html", active_section="setup_profile", form=form, name=name, role=role)


class UserInfoView(MethodView):
    decorators = [login_required, role_required(["Admin"])]

    def get(self):
        name, role = get_name_role()
        users = db.read("users")
        return render_template("settings.html", active_section="user_info", name=name, role=role, users=users)


class SingleInfoView(MethodView):
    decorators = [login_required, role_required(["Admin"])]

    def get(self, user_id):
        name, role = get_name_role()
        user_info = db.read("user_info", {"user_id": user_id})
        if not user_info:
            flash("User information not found.", "danger")
            return redirect(url_for("user_info"))
        
        user_data = user_info[0]

        return render_template("view_user_info.html", user_data=user_data, name=name, role=role)


class AddUserInfoView(MethodView):
    decorators = [login_required, role_required(["Admin"])]

    def get(self, user_id):
        form = UserInfoForm()
        name, role = get_name_role()
        user_info = db.read("user_info", {"user_id": user_id})
        if user_info:
            flash("You have already added your information. You can only edit it.", "warning")
            return redirect(url_for("edit_user_info", user_id=user_id))
        return render_template("add_user_info.html", form=form, user_id=user_id, name=name, role=role)
    
    def post(self, user_id):
        form = UserInfoForm()
        name, role = get_name_role()

        if form.validate_on_submit():
            columns = ["user_id", "first_name", "last_name", "middle_name", "dob", "email_address", "gender", "home_address", "marital_status"]
            values = [
                user_id,
                form.ui_fname.data,
                form.ui_lname.data,
                form.ui_mname.data,
                form.ui_dob.data.strftime('%Y-%m-%d'),
                form.ui_email.data,
                form.ui_gender.data,
                form.ui_home_address.data,
                form.ui_marital_status.data
            ]
            db.insert("user_info", columns, values)

            flash("User information added successfully.", "info")
            return redirect(url_for("user_info"))
        return render_template("add_user_info.html", form=form, user_id=user_id, name=name, role=role)


class EditUserInfoView(MethodView):
    decorators = [login_required, role_required(["Admin"])]

    def get(self, user_id):
        name, role = get_name_role()
        form = UserInfoForm()
        if request.method == "GET":
            users_info = db.read("user_info", {"user_id": user_id})
            if users_info:
                form.ui_fname.data = users_info[0][2]
                form.ui_lname.data = users_info[0][3]
                form.ui_mname.data = users_info[0][4]
                form.ui_dob.data = users_info[0][5]
                form.ui_email.data = users_info[0][6]
                form.ui_gender.data = users_info[0][7]
                form.ui_home_address.data = users_info[0][8]
                form.ui_marital_status.data = users_info[0][9]
            else:
                flash("User information not found! You can add it by clicking on the update button.", "danger")
                return redirect(url_for("user_info"))
            return render_template("edit_user_info.html", form=form, name=name, role=role)
            
    def post(self, user_id):
        name, role = get_name_role()
        form = UserInfoForm()

        if form.validate_on_submit():
            db.update(
                "user_info", 
                {
                "first_name": form.ui_fname.data,
                "last_name": form.ui_lname.data,
                "middle_name": form.ui_mname.data,
                "dob": form.ui_dob.data.strftime('%Y-%m-%d'),
                "email_address": form.ui_email.data,
                "gender": form.ui_gender.data,
                "home_address": form.ui_home_address.data,
                "marital_status": form.ui_marital_status.data
                }, 
                {"user_id": user_id}
            )
            flash("User info updated successfully.", "success")
            return redirect(url_for("user_info"))
        return render_template("edit_user_info.html", form=form, name=name, role=role)


@app.route("/settings/update-profile", methods=["GET", "POST"])
@login_required
@role_required(["Admin"])
def update_profile():
    pass


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))



# Class based views registering
app.add_url_rule("/", view_func=LoginView.as_view("login"))
app.add_url_rule("/dashboard", view_func=DashboardView.as_view("dashboard"))
app.add_url_rule("/add", view_func=AddView.as_view("add"))
app.add_url_rule("/edit-product/<int:product_id>", view_func=EditProductView.as_view("edit_product"))
app.add_url_rule("/products", view_func=ProductView.as_view("products"))
app.add_url_rule("/orders", view_func=OrdersView.as_view("orders"))
app.add_url_rule("/cart", view_func=CartView.as_view("cart"))
app.add_url_rule("/add_to_cart", view_func=AddToCartView.as_view("add_to_cart"))
app.add_url_rule("/remove_from_cart", view_func=RemoveFromCart.as_view("remove_from_cart"))
app.add_url_rule("/sales", view_func=SalesView.as_view("sales"))
app.add_url_rule("/settings", view_func=SettingsView.as_view("settings"))
app.add_url_rule("/settings/edit-users", view_func=EditUsersView.as_view("edit_users"))
app.add_url_rule("/edit-user/<int:user_id>", view_func=EditUsersView.as_view("edit_user"))
app.add_url_rule("/settings/setup-profile", view_func=SetupProfileView.as_view("setup_profile"))
app.add_url_rule("/settings/user_info", view_func=UserInfoView.as_view("user_info"))
app.add_url_rule("/view_user_info/<int:user_id>", view_func=SingleInfoView.as_view("view_user_info"))
app.add_url_rule("/add_user_info/<int:user_id>", view_func=AddUserInfoView.as_view("add_user_info"))
app.add_url_rule("/edit_user_info/<int:user_id>", view_func=EditUserInfoView.as_view("edit_user_info"))



if __name__ == "__main__":
    app.run(debug=True)
