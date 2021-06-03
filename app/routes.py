from flask import render_template, flash, redirect, url_for, jsonify
from app import app, db
from app.forms import LoginForm, SignUpForm, EditUserForm, PostForm, CreatUserForm
from app.models import *
from flask_login import current_user, login_user, logout_user, login_required
from flask import request
from werkzeug.urls import url_parse
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
from sqlalchemy import exc
from werkzeug.security import generate_password_hash
from flask_paginate import Pagination, get_page_parameter


@app.route("/")
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        if user.username == "admin" and user.check_password('1234'):
            return redirect(url_for('dashboard'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)



@app.route("/index", methods=['GET'])
@login_required
def index():
    id = current_user.get_id()
    load_user(id)
    page_size = request.args.get("page_size", 4, type=int)
    page = request.args.get("page", default=1, type=int)
    district = request.args.get("district", default='', type=str)
    if len(district) > 0:
        posts = House.query.filter(House.district.like(district)).paginate(page=page, per_page=page_size, error_out=True)
        return render_template('index.html', data=posts)
    else:
        posts = House.query.paginate(page=page, per_page=page_size, error_out=True)
        return render_template('index.html', data=posts)

@app.route("/demo", methods=['GET'])
def demo():
    page_size = request.args.get("page_size", 4, type=int)
    page = request.args.get("page", default=1, type=int)
    district = request.args.get("district", default='', type=str)
    if len(district) > 0:
        posts = House.query.filter(House.district.like(district)).paginate(page=page, per_page=page_size, error_out=True)
        return render_template('demo.html', data=posts)
    else:
        posts = House.query.paginate(page=page, per_page=page_size, error_out=True)
        return render_template('demo.html', data=posts)



@app.route("/data", methods=['GET', 'POST'])
def data():
    form = PostForm()
    time = datetime.now()
    if form.validate_on_submit():
        img = "/assets/images/"+str(form.image.data)
        house = House(user_id=current_user.id, name=form.name.data, area=form.area.data, price=form.price.data,
                      number_house=form.number_house.data, street=form.street.data, wards=form.wards.data,
                      district=form.district.data, image=img)
        db.session.add(house)
        db.session.commit()
        house_id = House.query.order_by(House.house_id.desc()).first()
        print(house_id)
        post = Post(user_id=current_user.id, house_id=int(str(house_id)[7:(len(str(house_id))-1)]),
                    describe=form.describe.data, phone=form.phone.data,
                    contents=form.contents.data, time=time)
        db.session.add(post)
        db.session.commit()
        flash('Data Up Success!')
        return redirect(url_for('demo'))
    return render_template('data.html', title="Đăng tin" , form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET'])
def admin():
    return render_template('admin.html')

@app.route('/button', methods=['GET'])
def button():
    return render_template('admin/button.html')

@app.route('/icon', methods=['GET'])
def icon():
    return render_template('admin/icon.html')

@app.route('/calendar', methods=['GET'])
def calendar():
    return render_template('admin/calendar.html')

@app.route('/table', methods=['GET'])
def table():
    headings = ("User ID", "Username", "Gender", "Phone", "Email", )
    post=Users.query.all()
    return render_template('admin/table.html', asd=post, headings=headings)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template('admin/dashboard.html')


@app.route('/post', methods=['GET'])
def post():
    head = ("Post ID", "User ID", "House ID", "Content", "Describe", "Phone", "Time")
    post = Post.query.all()
    return render_template('admin/post.html', xyz=post, head=head)

@app.route('/house', methods=['GET'])
def house():
    heading = ("House ID", "User ID", "Type", "Area", "Number", "Street", "Wards", "Price", "District")
    posts = House.query.all()
    return render_template('admin/house.html', abc=posts, heading=heading,)

@app.route('/person', methods=['GET'])
def person():
    heading = ("Type", "Area", "Number", "Street", "Wards", "Price", "District")
    house = House.query.filter_by(user_id=current_user.id)
    return render_template('person.html', house=house, heading=heading)




@app.route('/register', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if request.method == 'GET':
        return render_template('signup.html', title='Sign Up', form=form)
    else:
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        if form.validate_on_submit():
            user = Users(username=form.username.data, email=form.email.data, gender=form.gender.data, phone=form.phone.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            flash('Sign Up Success!')
            return redirect(url_for('login'))


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditUserForm()
    if form.validate_on_submit():
        current_user.username = form.username.data

        current_user.email = form.email.data
        db.session.commit()
        flash('Edit User Success!')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        # lấy data ra
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.route("/create", methods=['GET', 'POST'])
def create():
    form = CreatUserForm()
    if form.validate_on_submit():
        user = Users(username=form.username.data, gender=form.gender.data, phone=form.phone.data,
                      email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Data Up Success!')
        return redirect(url_for('table'))
    return render_template('admin/create.html', form=form)

@app.route("/update/<id>", methods=['GET', 'POST'])
def update(id):
    form = EditUserForm()
    user = Users.query.filter_by(id=id).first()
    if form.validate_on_submit():
        user.username = form.username.data
        user.gender = form.gender.data
        user.phone = form.phone.data
        user.email = form.email.data
        user.password = form.password.data
        db.session.commit()
        flash('Edit User Success!')
        return redirect(url_for('table'))
    elif request.method == 'GET':
        # lấy data ra
        form.username.data = user.username
        form.gender.data = user.gender
        form.phone.data = user.phone
        form.email.data = user.email
        form.password.data = user.password
    return render_template('admin/edit.html', form=form, user_id=id)

@app.route("/delete/<id>", methods=['GET'])
def delete(id):
    user = Users.query.filter_by(id=id).first()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("table"))

@app.route("/creates", methods=['GET', 'POST'])
def creates():
    form = PostForm()
    time = datetime.now()
    if form.validate_on_submit():
        img = "/assets/images/" + str(form.image.data)
        house = House(user_id=current_user.id, name=form.name.data, area=form.area.data, price=form.price.data,
                      number_house=form.number_house.data, street=form.street.data, wards=form.wards.data,
                      district=form.district.data, image=img)
        db.session.add(house)
        db.session.commit()
        house_id = House.query.order_by(House.house_id.desc()).first()
        print(house_id)
        post = Post(user_id=current_user.id, house_id=int(str(house_id)[7:(len(str(house_id)) - 1)]),
                    describe=form.describe.data, phone=form.phone.data,
                    contents=form.contents.data, time=time)
        db.session.add(post)
        db.session.commit()
        flash('Data Up Success!')
        return redirect(url_for('house'))
    return render_template('admin/creates.html', form=form)

@app.route("/edits/<house_id>", methods=['GET', 'POST'])
def edits(house_id):
    form = PostForm()
    house = House.query.filter_by(house_id=house_id).first()
    post = Post.query.filter_by(house_id=house_id).first()
    if form.validate_on_submit():
        house.name = form.name.data
        house.area = form.area.data
        house.price = form.price.data
        house.number_house = form.number_house.data
        house.street = form.street.data
        house.wards = form.wards.data
        house.district = form.district.data
        post.contents = form.contents.data
        post.describe = form.describe.data
        post.phone = form.phone.data
        db.session.commit()
        flash('Edit User Success!')
        return redirect(url_for('house'))
    elif request.method == 'GET':
        # lấy data ra
        form.name.data = house.name
        form.area.data = house.area
        form.price.data = house.price
        form.number_house.data = house.number_house
        form.street.data = house.street
        form.wards.data = house.wards
        form.district.data = house.district
        form.contents.data = post.contents
        form.describe.data = post.describe
        form.phone.data = post.phone
    return render_template('admin/edits.html', form=form, house_id=house_id)

@app.route("/deletes/<house_id>", methods=['GET'])
def deletes(house_id):
    house = House.query.filter_by(house_id=house_id).first()
    db.session.delete(house)
    db.session.commit()
    return redirect(url_for("house"))

@app.route("/back/<house_id>", methods=['GET'])
def back(house_id):
    house = House.query.filter_by(house_id=house_id).first()
    db.session.delete(house)
    db.session.commit()
    return redirect(url_for("person"))

@app.route("/updates/<house_id>", methods=['GET', 'POST'])
def updates(house_id):
    form = PostForm()
    house = House.query.filter_by(house_id=house_id).first()
    post = Post.query.filter_by(house_id=house_id).first()
    if form.validate_on_submit():
        house.name = form.name.data
        house.area = form.area.data
        house.price = form.price.data
        house.number_house = form.number_house.data
        house.street = form.street.data
        house.wards = form.wards.data
        house.district = form.district.data
        post.contents = form.contents.data
        post.describe = form.describe.data
        post.phone = form.phone.data
        db.session.commit()
        flash('Edit User Success!')
        return redirect(url_for('person'))
    elif request.method == 'GET':
        # lấy data ra
        form.name.data = house.name
        form.area.data = house.area
        form.price.data = house.price
        form.number_house.data = house.number_house
        form.street.data = house.street
        form.wards.data = house.wards
        form.district.data = house.district
        form.contents.data = post.contents
        form.describe.data = post.describe
        form.phone.data = post.phone
    return render_template('admin/edits.html', form=form, house_id=house_id)




