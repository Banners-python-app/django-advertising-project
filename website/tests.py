from django.test import TestCase
from django.urls import reverse
from agency.models import Category, Product
from website.models import Inquiry
from unittest.mock import patch

class ContactPageTests(TestCase):
    def setUp(self):
        """Set up a test product to use in the dropdown selection."""
        self.category = Category.objects.create(name="Traditional Hoarding", slug="traditional")
        self.product = Product.objects.create(
            category=self.category,
            name="Charholi Chowk Board",
            is_active=True
        )
        self.contact_url = reverse('contact')

    def test_contact_page_loads_successfully(self):
        """Verify the contact page URL returns an HTTP 200 status code and loads the right template."""
        response = self.client.get(self.contact_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'website/contact.html')

    # THE MAGIC PATCH: Intercepts the ReCaptcha validation process and forces a success
    @patch('django_recaptcha.fields.ReCaptchaField.clean')
    def test_valid_contact_form_submission(self, mock_captcha_clean):
        # Tell the mock to pretend the captcha was solved perfectly
        mock_captcha_clean.return_value = 'PASSED'
        
        """Verify that submitting valid form data creates an Inquiry record in the database."""
        form_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone_number': '9876543210',
            'interested_product': self.product.id,
            'message': 'Interested in booking this hoarding for July.',
            'g-recaptcha-response': 'PASSED' 
        }
        
        # Simulate a POST request to the form
        response = self.client.post(self.contact_url, data=form_data)
        
        # Verify it redirects back safely (HTTP 302) after a successful submission
        self.assertEqual(response.status_code, 302)
        
        # Verify the record actually exists in the database
        self.assertEqual(Inquiry.objects.count(), 1)
        
        saved_inquiry = Inquiry.objects.first()
        self.assertEqual(saved_inquiry.name, 'John Doe')
        self.assertEqual(saved_inquiry.interested_product, self.product)

    # Apply the same patch here so the captcha passes, allowing us to test the OTHER form fields
    @patch('django_recaptcha.fields.ReCaptchaField.clean')
    def test_invalid_contact_form_submission(self, mock_captcha_clean):
        mock_captcha_clean.return_value = 'PASSED'
        
        """Verify that missing required fields blocks database storage and returns errors."""
        invalid_data = {
            'name': '', # Name is required, leaving it empty
            'email': 'not-an-email', # Invalid email format
            'message': 'Hello',
            'g-recaptcha-response': 'PASSED'
        }
        
        response = self.client.post(self.contact_url, data=invalid_data)
        
        # Should stay on the page (HTTP 200) to display validation errors
        self.assertEqual(response.status_code, 200)
        
        # Database should still be clean
        self.assertEqual(Inquiry.objects.count(), 0)