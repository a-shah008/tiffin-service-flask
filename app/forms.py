from xml.dom import ValidationErr
from flask import Flask
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, IntegerField, FloatField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User, AdminOrder, Comment
from flask_login import current_user

class AuthenticateAdminForm(FlaskForm):
    admin_pin = IntegerField("Admin Pin", validators=[DataRequired("Please input the correct value.")])
    password = StringField("Account Password", validators=[DataRequired("Please input the correct value.")])
    submit = SubmitField("Submit")

class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])

    submit = SubmitField("Register")
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("That email already exists. Please choose a different one.")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")

    submit = SubmitField("Log In")

class CreateNewAdminOrder(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    contents = TextAreaField("Content of Order", validators=[DataRequired()])
    unit_price = FloatField("Unit Price in Float Form (ex. 1.00, do not add dollar sign)", validators=[DataRequired()])
    picture = FileField("Upload Order Image", validators=[FileAllowed(['jpg', 'png'])])

    submit = SubmitField("Create New Order")

    def validate_name(self, name):
        order_obj = AdminOrder.query.filter_by(name=name.data).first()
        if order_obj:
            raise ValidationError("That name already exists in our database.")

class NewCommentForm(FlaskForm):
    author_display_name = StringField("Name", validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired()])
    content = TextAreaField("Content", validators=[DataRequired()])

    submit = SubmitField("Post")

    def validate_author_display_name(self, author_display_name):
        dup_author_dname = Comment.query.filter_by(author_display_name=author_display_name.data).first()
        if dup_author_dname:
            raise ValidationError("That display name already exists in our database.")

class AddToCartForm(FlaskForm):
    quantity = SelectField("Quantity", validators=[DataRequired()], choices=["1", "2", "3"])
    addbtn = SubmitField("Add To Cart")