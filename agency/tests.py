from django.test import TestCase
from agency.models import Category, Product
# Create your tests here.

class InventoryModelTests(TestCase):
    def setUp(self):
        #setting up baseline data for tests
        self.category = Category.objects.create(
            name="Digital Billboards",
            slug="digital-billboards"
        )
    
    def test_product_creation(self):
        #verify that product can be created using valid fields
        product = Product.objects.create(
            category = self.category,
            name="Prime High street location",
            description="A high-visibility hoarding near the main junction.",
            is_active=True
        )

        #Assertions check if the actual value matches the expected value
        self.assertEqual(product.name, "Prime High street location")
        self.assertEqual(product.category.name, "Digital Billboards")
        self.assertTrue(product.is_active)

    def test_product_string_representation(self):
        # verifying that the __str__ method returns the product name.
        product = Product.objects.create(
            category = self.category,
            name = "Moshi Highway Board"
        )
        self.assertEqual(str(product), "Moshi Highway Board")