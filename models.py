import os
from peewee import *
from datetime import date

# Ensure database "marketplace.db" is created in current folder
full_path = os.path.realpath(__file__)
file_dir = os.path.dirname(full_path)
db_path = os.path.join(file_dir, 'marketplace.db')

db = SqliteDatabase(db_path, pragmas={'foreign_keys': 1})
# Pragmas ensure foreign-key constraints are enforced.


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = CharField(unique=True, max_length=100)
    password = CharField()
    full_name = CharField()
    address = CharField()
    seller_description = TextField(null=True) 
    contact_info = CharField(null=True)


class Product(BaseModel):
    prod_id = AutoField()
    vendor = ForeignKeyField(User, backref='products', on_delete='CASCADE')
    title = CharField(max_length=100)
    qty = IntegerField(constraints=[Check('qty >= 0')])
    price = IntegerField(constraints=[Check('price >= 0')])
    description = TextField(null=True)
    contact = CharField(max_length=100)
    thumbnail = CharField(null=True)
    date_added = DateField(default=date.today())


class ProductImage(BaseModel):
    img_id = AutoField()
    product = ForeignKeyField(Product, backref='images', on_delete='CASCADE')
    image_url = CharField()


class Tag(BaseModel):
    name = CharField(max_length=50, unique=True)
    products = ManyToManyField(Product, backref='tags', on_delete='CASCADE')


ProductTag = Tag.products.get_through_model()


def create_tables():
    with db:
        db.create_tables([User, Product, ProductImage, Tag, ProductTag])