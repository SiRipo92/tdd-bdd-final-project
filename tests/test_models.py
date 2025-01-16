# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        # Fetch it back
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        # Change it and save it
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")

        # Fetch it back & verify ID hasn't changed
        # And that description changed
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

        # Ensure DataValidationError is raised if product has no ID
        product_missing_id = ProductFactory()
        product_missing_id.id = None

        # Check that error is raised when update() is called on product w/o ID
        with self.assertRaises(DataValidationError):
            product_missing_id.update()

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the DB"""
        products = Product.all()
        self.assertEqual(products, [])

        # Create 5 new Products
        for _ in range(5):
            product = ProductFactory()
            product.create()

        # Test if we get back 5 products
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find a Product by name"""
        products = ProductFactory.create_batch(5)

        # Loop through products list to call create method
        for product in products:
            product.create()

        # Retrieve name of first product in list
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)

        # Loop over found products and make assertions that names match
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len({product for product in products if product.available == available})
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_deserialize_with_invalid_data(self):
        """It should raise DatavalidationError for invalid data types"""
        product = Product()

        # Test with None (TypeError)
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(None)
        self.assertIn("Invalid product: body of request contained bad or no data", str(context.exception))

        # Test with non-dictionary (TypeError)
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(["not", "a", "dictionary"])
        self.assertIn("Invalid product: body of request contained bad or no data", str(context.exception))

    def test_deserialize_with_invalid_boolean(self):
        """It should raise DataValidationError for non-boolean available field"""
        product = Product()
        invalid_data = {
            "name": "Widget",
            "description": "A widget",
            "price": "19.99",
            "available": "not_a_boolean",  # Invalid type
            "category": "TOYS",
        }

        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)
        self.assertIn("Invalid type for boolean [available]:", str(context.exception))

    def test_deserialize_with_invalid_attribute(self):
        """It should raise DataValidationError for invalid attributes"""
        product = Product()

        # Provide all required fields and an invalid attribute
        invalid_data = {
            "name": "Test",
            "description": "A test product",
            "price": "19.99",
            "available": True,
            "category": "Books",
            "unknown_field": "value",  # This should trigger exception
            }
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)
        self.assertIn("Invalid attribute:", str(context.exception))

    def test_find_by_price(self):
        """It should find products by price"""
        product = ProductFactory(price=Decimal("19.99"))
        product.create()

        # Test finding by price as Decimal
        products = Product.find_by_price(Decimal("19.99")).all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].price, Decimal("19.99"))

        # Test finding by price as string
        products = Product.find_by_price("19.99").all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].price, Decimal("19.99"))

        # Test no products found
        products = Product.find_by_price(Decimal("9.99")).all()
        self.assertEqual(len(products), 0)
