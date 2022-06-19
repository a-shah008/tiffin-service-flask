from datetime import datetime

from sqlalchemy import true
from app import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    admin_orders = db.relationship('AdminOrder', backref="admin")
    user_comments = db.relationship('Comment', backref="author")
    carts = db.relationship("Cart", backref="buyer")

    def __repr__(self):
        return f"\nUser {self.id}: {self.email}\n"

class AdminOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(200), default="default2.jpg")
    name = db.Column(db.String(200), nullable=False, unique=True)
    contents = db.Column(db.String(100), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    currently_active_order = db.Column(db.Boolean, default=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship('Comment', backref="order")

    def __repr__(self):
        return f"{self.name}\nCurrently Active: {self.currently_active_order}\nAdmin ID: {self.admin_id}\n--------\n"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    author_display_name = db.Column(db.String(50), nullable=False, unique=True)
    order_id = db.Column(db.Integer, db.ForeignKey('admin_order.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"{self.title} - User {self.author_id}"

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_price = db.Column(db.Float, default=0.0)
    active = db.Column(db.Boolean, nullable=False, default=False)
    purchase_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    purchase_confirmed_date = db.Column(db.String(200))
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    lineitems = db.relationship("Lineitem", backref="all_lineitems")

    def __repr__(self):
        return f"Cart: {self.id}"

class Lineitem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    cart_id = db.Column(db.Integer, db.ForeignKey("cart.id"))
    order_id = db.Column(db.Integer, db.ForeignKey("admin_order.id"))

    def __repr__(self):
        return f"{self.name} with a quantity of {self.quantity}"