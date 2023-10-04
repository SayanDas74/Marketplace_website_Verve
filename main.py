import os
import queries
from helpers import verify_signin, verify_signup
from flask import Flask, redirect, render_template, request, session, url_for, flash, abort
from werkzeug.utils import secure_filename
from models import create_tables

create_tables()
app = Flask(__name__)
app.secret_key = os.urandom(16)

# Configuration for file uploads
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def frontpage():
    featured_products = []
    user_address = session["user"].get("address") if "user" in session else None

    if user_address:
        featured_products = queries.get_newest_products_with_address(user_address)
    else:
        featured_products = queries.get_newest_products()

    return render_template("home_page.html", products=featured_products)


@app.route('/home/')
def home():
    return redirect(url_for("frontpage"))


@app.route('/sign_up/', methods=['GET', 'POST'])
def sign_up():
    if request.method == "POST":

        # grab user info from form
        username = request.form["username"]
        fullname = request.form["full_name"]
        address = request.form["address"]
        password = request.form["password"]

        user_is_valid = verify_signup(
            username, fullname, address, password)

        if user_is_valid:
            # set session user
            user = queries.get_user(username)
            session["user"] = user
            return redirect(url_for("frontpage"))
        else:
            return redirect(url_for('sign_up'))

    else:  # request.method == "GET"
        if "user" in session:
            return redirect(url_for("frontpage"))
        return render_template("sign_up.html")


@app.route('/sign_in/', methods=['GET', 'POST'])
def login():
    if request.method == "POST":

        # retrieve user info
        username = request.form["username"]
        password = request.form["password"]

        login_succesfull = verify_signin(username, password)

        if login_succesfull:
            # set session usser
            user = queries.get_user(username)
            session["user"] = user
            return redirect(url_for("frontpage"))
        else:
            return redirect(url_for('login'))

    else:  # request.method == "GET"
        if "user" in session:
            return redirect(url_for("frontpage"))
        return render_template('log_in.html')


@app.route('/sign_out/')
def logout():
    if "user" in session:
        session.pop("user", None)
        flash("You have been signed out", 'info')
    return redirect(url_for("frontpage"))


@app.route('/my_profile/')
def my_profile():
    if "user" in session:
        user = session["user"]
        user_products = queries.list_user_products(user["username"])
        return render_template('my_profile.html', user=user, products=user_products[:7])
    else:  # user must be logged in
        return redirect(url_for('login'))
    
@app.route('/sell_on_verve/')
def sell_on_verve():
    if "user" in session:
        user = session["user"]
        user_products = queries.list_user_products(user["username"])
        if not user_products:
            return redirect(url_for('become_seller'))
        else:
            return redirect(url_for('add_product'))
    else:  # user must be logged in
        return redirect(url_for('login'))



@app.route('/my_profile/add_product/', methods=['GET', 'POST'])
def add_product():
    if "user" in session:
        if request.method == "POST":

            # get product info from form
            title = request.form["title"]
            description = request.form["description"]
            price = request.form["price"]
            qty = request.form["qty"]
            user = session["user"]
            contact = request.form["contact"]

            product = {
                "title": title,
                "description": description,
                "price": price,  
                "qty": int(qty),
                "vendor": user,
                "contact": contact
            }

            product_id = queries.add_product_to_catalog(
                product)  # returns a product id if succesfull

            if product_id:
                # add product images
                image_1 = request.form["image_1"]
                image_2 = request.form["image_2"]
                image_3 = request.form["image_3"]
                image_4 = request.form["image_4"]
                image_5 = request.form["image_5"]
                images = [image_1, image_2, image_3, image_4, image_5]

                if images:  # if image list isn't empty
                    queries.add_images_to_product(product_id, images)

                # add product tags
                tags = request.form["tags"]
                tag_list = tags.split(", ")

                if tag_list:  # if list of tags isn't empty
                    queries.add_product_tags(product_id, tag_list)

                return redirect(url_for("product_page", product_id=product_id, _method='GET'))
            else:
                flash("Could not add product", 'error')
                return redirect(url_for('add_product'))

        else:  # request.method == "GET"
            return render_template("add_product.html")
    else:  # user must be logged in
        return redirect(url_for('login'))
    
@app.route('/my_profile/become_seller/', methods=['GET', 'POST'])
def become_seller():
    if "user" in session:
        if request.method == "POST":

            # get seller info from form
            description = request.form["description"]
            contact = request.form["contact"]
            user = session["user"]

            seller_info = {
                "description": description,
                "contact": contact,
                "user": user
            }

            success = queries.add_seller_info(seller_info) 

            if success:
                user["is_seller"] = True
                flash("You are now a seller!", 'success')
                return redirect(url_for('add_product'))
            else:
                flash("Could not become a seller", 'error')
                return redirect(url_for('become_seller'))

        else:  # request.method == "GET"
            return render_template("become_seller.html")
    else:  # user must be logged in
        return redirect(url_for('login'))


@app.route('/my_profile/edit_product/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if "user" in session:
        if request.method == "POST":

            # get updated product info from form
            title = request.form["title"]
            description = request.form["description"]
            price = request.form["price"]
            qty = request.form["qty"]
            thumbnail = request.form["thumbnail"]

            edit_successful = queries.edit_product(
                product_id, title, description, price, qty, thumbnail)

            if edit_successful:
                return redirect(url_for("my_products"))
            else:
                flash("Something went wrong. Couldn't update product", 'error')
                return redirect(url_for("edit_product", product_id=product_id, _method='GET'))

        else:  # request.method == "GET"
            product = queries.get_product(product_id)
            if product:
                return render_template("edit_product.html", product=product)
            else:
                abort(404)
    else:  # user must be logged in
        return redirect(url_for('login'))
    
@app.route('/my_profile/remove_product/<product_id>')
def remove_product(product_id):
    if "user" in session:
        user = session["user"]

        product_was_removed = queries.remove_product(
            user["username"], product_id)

        if product_was_removed:
            flash("Product has been removed", 'info')
        else:
            flash("Could not remove product", 'error')
        return redirect(url_for("my_products"))
    else:  # user must be logged in
        return redirect(url_for('login'))


@app.route('/my_profile/my_products/')
def my_products():
    if "user" in session:
        user = session["user"]
        products = queries.list_user_products(user["username"])
        return render_template("my_products.html", products=products)
    else:  # user must be logged in
        return redirect(url_for('login'))


@app.route('/user_page/<username>')
def user_page(username):
    verve_user = queries.get_user(username)
    if verve_user:
        user_products = queries.list_user_products(verve_user['username'])
        return render_template("user_page.html", verve_user=verve_user, products=user_products)
    else:
        abort(404)


@app.route('/product_page/<product_id>', methods=['GET', 'POST'])
def product_page(product_id):
    if request.method == "GET":
        product = queries.get_product(product_id)
        if product:  # if product exists
            product_tags = queries.get_product_tags(product_id)
            product_images = queries.get_product_images(product_id)
            return render_template("product_page.html", product=product, product_images=product_images, product_tags=product_tags)
        else:
            abort(404)

    else:  # request.method == "POST"
        flash("Item added to cart", 'info')
        return redirect(url_for("product_page", product_id=product_id))



@app.route('/products/')
def all_products():
    products = queries.get_all_products()
    return render_template("products_page.html", query='All Products', products=products)


@app.route('/products/<tag>')
def search_products_by_tag(tag):
    tagged_products = queries.list_products_per_tag(tag)
    return render_template("products_page.html", query=tag, products=tagged_products)


@app.route('/products/search/')
def search_products():
    query = request.args.get("query")
    user_address = session["user"].get("address") if "user" in session else None

    products = queries.search(query, user_address)

    return render_template("products_page.html", query=query, products=products)


@app.route('/checkout/success/')
def success():
    return render_template('success.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run()