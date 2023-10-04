import peewee
from peewee import fn
from flask import flash
from playhouse.shortcuts import model_to_dict
from models import User, Product, ProductImage, Tag


def create_user(user_name, user_full_name, user_address, user_password):
    '''adds a user to database'''
    try:
        return User.create(
            username=user_name, full_name=user_full_name, address=user_address, password=user_password
        )
    except peewee.PeeweeException:
        return False


def get_user(user_name):
    '''finds and returns a user dictionary from database'''
    try:
        user = User.get(User.username == user_name)
        return model_to_dict(user)  # converts DB user to dictionary
    except peewee.DoesNotExist:
        return False


def get_user_password(user_name):
    '''finds a username and returns a user password from database'''
    try:
        user = User.get(User.username == user_name)
        return user.password
    except peewee.DoesNotExist:
        return False

def add_seller_info(seller_info):
    '''Adds seller information to user's profile'''
    try:
        user = User.get(User.username == seller_info['user']['username'])
        user.seller_description = seller_info['description']
        user.contact_info = seller_info['contact']
        user.is_seller = True  # Set user as a seller
        user.save()
        return model_to_dict(user)
    except peewee.DoesNotExist:
        return False

    
def add_product_to_catalog(product_info):
    '''creates and adds a product to user's profile'''
    try:
        user = User.get(User.username == product_info['vendor']['username'])

        product = Product.create(title=product_info["title"], description=product_info['description'],
                                 price=product_info['price'], qty=product_info['qty'], contact=product_info['contact'], vendor=user)
        # product.save()
        return product.prod_id
    except peewee.PeeweeException:
        return False


def add_images_to_product(product_id, image_list):
    '''Adds list of images to a product'''

    product = Product.get_by_id(product_id)

    # set first image as product thumbnail
    product.thumbnail = image_list[0]
    product.save()

    for image_url in image_list:
        if image_url:  # If image path isn't empty
            prod_image = ProductImage(product=product, image_url=image_url)
            prod_image.save()



def add_product_tags(product_id, tag_list):
    '''adds tags to a product'''
    product = Product.get_by_id(product_id)

    for tag in tag_list:
        if tag:
            Tag.get_or_create(name=tag.lower())
            product.tags.add(Tag.get(Tag.name == tag.lower()))

def edit_product(product_id, title, description, price, qty, thumbnail):
    '''modifies and updates a product info'''
    # note to docent: this function replaces the update_stock function from the Winc assignment
    try:
        product = Product.get_by_id(product_id)

        if title:
            product.title = title
        if description:
            product.description = description
        if price:
            product.price = int(price)
        if qty:
            product.qty = int(qty)
        if thumbnail:
            product.thumbnail = thumbnail

        product.save()
        return model_to_dict(product)
    except peewee.PeeweeException:
        return False
    
def remove_product(user_name, product_id):
    '''removes a product from database'''
    try:
        user = User.get(User.username == user_name)
        product = Product.get_by_id(product_id)

        # ensure user deleting product is product's vendor
        if user == product.vendor:
            product_deleted = product.delete_instance()
            return product_deleted
        else:
            return False
    except peewee.IntegrityError:
        flash("Could not remove product.", 'error')
        return False


def get_product(product_id):
    '''finds and returns a product dictionary from database'''
    try:
        product = Product.get_by_id(product_id)
        return model_to_dict(product, backrefs=True)
    except peewee.DoesNotExist:
        return False


def get_product_images(product_id):
    '''returns a list of product_images if any'''
    product = Product.get_by_id(product_id)
    images = [image.image_url for image in product.images]
    return images


def get_product_tags(product_id):
    '''returns a list of tags associated to a product if any'''
    product = Product.get_by_id(product_id)
    tags = [tag.name for tag in product.tags]
    return tags


def get_newest_products():
    '''returns 12 products in database sorted by date added'''
    query = (Product
             .select()
             .order_by(Product.date_added.desc())
             .limit(12))
    products = [model_to_dict(product) for product in query]
    return products

def get_all_products():
    '''returns all products from database'''
    query = Product.select()
    products = [model_to_dict(product, backrefs=True) for product in query]
    return products


def list_user_products(user_name):
    '''returns a list of products a user is selling'''
    user = User.get(User.username == user_name)
    products = [model_to_dict(product, backrefs=True)
                for product in user.products]
    return products


def list_products_per_tag(tag_name):
    '''returns a list of products associated with a given tag'''
    tag = Tag.get(Tag.name == tag_name)
    products = [model_to_dict(product) for product in tag.products]
    return products


def search(term, user_address=None):
    '''returns a list of products whose name or description contains a given term'''
    search_term = term.lower()
    query = Product.select().where(
        (fn.Lower(Product.title).contains(search_term) | fn.Lower(Product.description).contains(search_term))
    )
    if user_address:
        query = query.join(User).where(User.address == user_address)

    products = [model_to_dict(product) for product in query]
    return products



def get_products_with_same_address(user_address):
    '''returns a list of products from sellers with the same address as the user'''
    try:
        query = (Product
                 .select()
                 .join(User)
                 .where(User.address == user_address))
        products = [model_to_dict(product, backrefs=True) for product in query]
        return products
    except peewee.DoesNotExist:
        return False
    
def get_newest_products_with_address(user_address):
    query = (Product
             .select()
             .join(User)
             .where(User.address == user_address)
             .order_by(Product.date_added.desc())
             .limit(12))
    products = [model_to_dict(product) for product in query]
    return products

def search_with_address(term, user_address):
    '''returns a list of products whose name or description contains a given term 
       and are from sellers with the same address as the user'''
    search_term = term.lower()
    query = (Product
             .select()
             .join(User)
             .where((fn.Lower(Product.title).contains(search_term) |
                     fn.Lower(Product.description).contains(search_term)) &
                    (User.address == user_address)))
    products = [model_to_dict(product) for product in query]
    return products
