
from flask import render_template, url_for, flash, redirect, request
from requests import RequestException
from app import app, db, bcrypt
from app.forms import AuthenticateAdminForm, RegistrationForm, LoginForm, CreateNewAdminOrder, NewCommentForm, AddToCartForm
from app.models import User, AdminOrder, Comment, Cart, Lineitem
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
import uuid
from datetime import datetime
from PIL import Image
ADMIN_PIN = 963241

def current_cart():
    if current_user.is_authenticated:
        active_cart = Cart.query.filter_by(active=True, buyer_id=current_user.id).first()
        if active_cart:
            active_cart = active_cart
        else:
            active_cart = Cart(total_price=0, active=True, purchase_confirmed=False, purchase_confirmed_date="Purchase not confirmed yet", buyer_id=current_user.id)
            db.session.add(active_cart)
            db.session.commit()
        return active_cart

def item_count():
    if current_user.is_authenticated:
        item_counter = 0
        active_cart = current_cart()
        items = Lineitem.query.filter_by(cart_id=active_cart.id).all()
        if items:
            for item in items:
                item_counter += item.quantity
        else:
            item_counter = 0
        item_counter = item_counter
        return item_counter

def all_products():
    active_cart = current_cart()
    user_items = Lineitem.query.filter_by(cart_id=active_cart.id).all()
    total_price = 0.0
    products = {}
    for item in user_items:
        item_id = item.order_id
        item_quantity_li = item.quantity
        product = AdminOrder.query.filter_by(id=item_id).first()
        products[product] = item_quantity_li
        db.session.commit()
    for item in products:
        total_price += item.unit_price * products[item]
        active_cart.total_price = total_price
        db.session.commit()
    
    return total_price, products


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
def home():
    admin_orders = AdminOrder.query.filter_by(currently_active_order=True).all()
    addtocart = AddToCartForm()

    if request.method == "POST":
        if request.form.get("addtocart"):
            print(request.form.get("addtocart"))
            print("^ Add To Cart ^")

            active_cart = current_cart()
            order_obj = AdminOrder.query.filter_by(name=request.form.get('addtocart')).first()
            item_quantity = int(addtocart.quantity.data)

            order_total_price = int(order_obj.unit_price) * int(item_quantity)
            active_cart.total_price = active_cart.total_price + order_total_price

            order_exists_in_cart = Lineitem.query.filter_by(name=order_obj.name, cart_id=active_cart.id).first()
            
            if order_exists_in_cart:
                difference = 3 - order_exists_in_cart.quantity
                if item_quantity > difference:
                    flash(f"You have exceeded the maximum quantity of 3 for that item.", "warning")
                    return redirect(url_for("home"))
                elif item_quantity <= difference:
                    order_exists_in_cart.quantity = order_exists_in_cart.quantity + item_quantity
                    flash(f"{order_exists_in_cart.name} (Quantity: +{difference}) has been successfully added to cart.", "success")
                    db.session.commit()
                    return redirect(url_for("home"))
            else:
                new_lineitem = Lineitem(name=order_obj.name, quantity=item_quantity, unit_price=order_obj.unit_price, cart_id=active_cart.id, order_id=order_obj.id)
                db.session.add(new_lineitem)
                db.session.commit()
                flash(f"{new_lineitem.name} (Quantity: +{new_lineitem.quantity}) has been successfully added to cart.", "success")
            return redirect(url_for("home"))

        if request.form.get("view_comments"):
            print(request.form.get("view_comments"))
            print("^  View All Comments ^")
            return redirect(url_for("all_comments", order=request.form.get("view_comments")))
            
        if request.form.get("comment"):
            print(request.form.get("comment"))
            print("^ Create New Comment ^")
            return redirect(url_for("new_comment", order=request.form.get("comment")))

    elif request.method == "GET":
        item_counter = 0
        item_counter = item_count()

        return render_template("home.html", title="Home", admin_orders=admin_orders, addtocart=addtocart, item_counter=item_counter)

@app.route("/my_cart", methods=["GET", "POST"])
@login_required
def my_cart():
    active_cart = current_cart()
    all_lineitems = Lineitem.query.filter_by(cart_id=active_cart.id).all()

    total_price, products = all_products()
    item_counter = 0
    item_counter = item_count()

    if request.method == "POST":
        if request.form.get("deleteallofproduct"):
            removal_item = request.form.get("deleteallofproduct")
            active_cart = current_cart()
            removal_item_obj = AdminOrder.query.filter_by(name=removal_item).first()
            db_removal_item = Lineitem.query.filter_by(cart_id=active_cart.id, order_id=removal_item_obj.id).first()
            db.session.delete(db_removal_item)
            db.session.commit()
            flash(f"All of {removal_item_obj.name} has been removed from your cart.", "success")
            return redirect(url_for("home"))

        if request.form.get('savenewquantitybutton'):
            active_cart = current_cart()
            new_quantity_user = request.form.get("new_quantity_input")
            print(new_quantity_user)
            item_name = request.form.get("savenewquantitybutton")
            print(item_name)
            original_lineitem_obj = Lineitem.query.filter_by(name=item_name).first()
            original_lineitem_obj.quantity = new_quantity_user
            db.session.commit()
            flash(f"Quantity of {item_name} has been successfully changed.", "success")
            return redirect(url_for("home"))

        if request.form.get('empty_cart'):
            active_cart = current_cart()
            print("active cart")
            items_in_cart = Lineitem.query.filter_by(cart_id=active_cart.id).all()
            print("var items_in_cart created")
            for item in items_in_cart:
                db.session.delete(item)
                print("delete item (in for loop)")
                db.session.commit()
                print("commit the deleted item (in for loop)")
            flash(f"Your cart has been successfully emptied.", "success")
            print("flash message (exited the for loop)")
            return redirect(url_for("home"))

    return render_template("my_cart.html", all_lineitems=all_lineitems, total_price=total_price, products=products, item_counter=item_counter)

@app.route("/all_comments/<order>", methods=["GET", "POST"])
@login_required
def all_comments(order):
    order_obj = AdminOrder.query.filter_by(name=order).first()
    all_comments = Comment.query.filter_by(order_id=order_obj.id).all()
    users = User.query.all()

    if request.method == "POST":
        if request.form.get('redirect_to_new_comment'):
            print(request.form.get("redirect_to_new_comment"))
            print("^ Redirecting to Craete a New Comment ^")
            return redirect(url_for("new_comment", order=request.form.get("redirect_to_new_comment")))

    return render_template("all_comments.html", title="All Comments", order_obj=order_obj, all_comments=all_comments, users=users)

@app.route("/new_comment/<order>", methods=["GET", "POST"])
@login_required
def new_comment(order):
    form = NewCommentForm()
    order_obj = AdminOrder.query.filter_by(name=order).first()

    if request.method == "POST":
        if form.validate_on_submit():
            to_be_added_comment = Comment(title=form.title.data, content=form.content.data, author_display_name=form.author_display_name.data, order_id=order_obj.id, author_id=current_user.id)
            db.session.add(to_be_added_comment)
            db.session.commit()
            flash("Your comment has been posted!", "success")
            return redirect(url_for("all_comments", order=order_obj.name))

    return render_template("new_comment.html", title="New Comment", form=form, order_obj=order_obj)

@app.route("/about", methods=["GET", "POST"])
def about():

    return render_template("about.html", title="About")

@app.route("/admin_login", methods=["GET", "POST"])
@login_required
def admin_login():
    if current_user.is_admin == True:
        return redirect(url_for("admin_panel"))
    form = AuthenticateAdminForm()
    extra_margin_above_flash_message = True
    if request.method == "POST":
        if form.validate_on_submit():
            if str(form.admin_pin.data) == str(ADMIN_PIN) and bcrypt.check_password_hash(current_user.password, form.password.data):
                current_user.is_admin = True
                db.session.commit()
                flash("You have been successfully authorized as an admin.", "success")
                return redirect(url_for("admin_panel"))
            else:
                flash("Authentication failed. Please try again.", "danger")
                return redirect(url_for("admin_login"))

    return render_template("admin_login.html", title="Admin Authentication", form=form, extra_margin_above_flash_message=extra_margin_above_flash_message)


@app.route("/admin_panel", methods=["GET", "POST"])
@login_required
def admin_panel():
    extra_margin_above_flash_message= True
    no_regular_styling = True
    if current_user.is_admin == False:
        flash("You are not authorized as an admin.", "danger")
        return redirect(url_for("admin_login"))

    all_orders = AdminOrder.query.filter_by(admin_id=current_user.id).all()
    recent_comments = AdminOrder.query.all()

    if request.method == "POST":
        if request.form.get("make_inactive"):
            print(request.form.get("make_inactive"))
            print("^ Make Inactive ^")
            obj = AdminOrder.query.filter_by(name=request.form.get("make_inactive")).first()
            obj.currently_active_order = False
            db.session.commit()
            flash(f"{obj.name} has been successfully made inactive.", "success")
            return redirect(url_for("admin_panel"))
            
        if request.form.get("edit_order_details"):
            print(request.form.get("edit_order_details"))
            print("^ Edit Order Details ^")
            return redirect(url_for("edit_admin_order", order=request.form.get("edit_order_details")))

        if request.form.get("view_comments"):
            print(request.form.get("view_comments"))
            print("^ View Comments on Order ^")
            return redirect(url_for("all_comments", order=request.form.get("view_comments")))


        if request.form.get("delete_order"):
            print(request.form.get("delete_order"))
            print("^ Delete Order ^")
            obj = AdminOrder.query.filter_by(name=request.form.get("delete_order")).first()
            db.session.delete(obj)
            db.session.commit()
            flash(f"{obj.name} has been successfully deleted.", "success")
            return redirect(url_for("admin_panel"))

        if request.form.get("make_active"):
            print(request.form.get("make_active"))
            print("^ Make Active ^")
            obj = AdminOrder.query.filter_by(name=request.form.get("make_active")).first()
            obj.currently_active_order = True
            db.session.commit()
            flash(f"{obj.name} has been successfully made active.", "success")
            return redirect(url_for("admin_panel"))

    return render_template("admin.html", title="Admin Panel", recent_comments=recent_comments, extra_margin_above_flash_message=extra_margin_above_flash_message, no_regular_styling=no_regular_styling, all_available_orders=all_orders)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/admin_order_images', picture_fn)
    form_picture.save(picture_path)
    filename_for_loading = "/static/admin_order_images/" + picture_fn

    return filename_for_loading

@app.route("/edit_admin_order/<order>", methods=["GET", "POST"])
@login_required
def edit_admin_order(order):
    if current_user.is_admin == False:
        flash("You must be an admin to access this page.", "danger")
        return redirect(url_for("admin_login"))

    order_obj = AdminOrder.query.filter_by(name=order).first()
    extra_margin_above_flash_message = True
    no_regular_styling = True

    if request.method == "POST":
        pass

    return render_template("edit_admin_order.html", title="Edit Admin Order", order_obj=order_obj, extra_margin_above_flash_message=extra_margin_above_flash_message, no_regular_styling=no_regular_styling)

@app.route("/new_admin_order", methods=["GET", "POST"])
@login_required
def new_admin_order():
    form = CreateNewAdminOrder()
    if request.method == "POST":
        if form.validate_on_submit():

            print(form.picture.data)
            picture_file = save_picture(form.picture.data)
            new_admin_order = AdminOrder(image_file=picture_file, name=form.name.data, contents=form.contents.data, unit_price=form.unit_price.data, currently_active_order=True, admin_id=current_user.id)
            db.session.add(new_admin_order)
            db.session.commit()
        
            flash(f"New Admin Order has been created. Name: {form.name.data}.", "success")
            return redirect(url_for("admin_panel"))

    return render_template("new_admin_order.html", title="New Admin Order", form=form)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    if request.method == "POST":
        if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
            user = User(email=form.email.data, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(f"Account has been successfully created for {form.email.data}.", "success")
            return redirect(url_for("home"))

    return render_template("register.html", title="Register", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    extra_margin_above_flash_message = True
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            flash(f"Login successful. You are now logged in as {form.email.data}.", "success")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Login unsuccessful. Please check email and password.", "danger")
            return redirect(url_for("login"))
    
    return render_template("login.html", title="Login", form=form, extra_margin_above_flash_message=extra_margin_above_flash_message)

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    extra_margin_above_flash_message = True

    
    return render_template("account.html", title="Account", extra_margin_above_flash_message=extra_margin_above_flash_message)

@app.route("/logout")
@login_required
def logout():
    flash(f"Successfully logged out {current_user.email}.", "success")
    logout_user()
    return redirect(url_for("home"))

