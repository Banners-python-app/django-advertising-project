from django import forms
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from .models import Inquiry
from agency.models import Product

class ContactForm(forms.ModelForm):
    # This automatically adds the "I am not a robot" checkbox
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)
    
    class Meta:
        model = Inquiry
        fields = ['name', 'email', 'phone_number', 'interested_product', 'message', 'captcha']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show active hoardings in the dropdown!
        self.fields['interested_product'].queryset = Product.objects.filter(is_active=True)
        self.fields['interested_product'].empty_label = "Select a Hoarding (Optional)"

        # Apply modern Tailwind styling to all text inputs automatically
        for field_name, field in self.fields.items():
            if field_name != 'captcha':
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm'
                })
        
        # Make the message box a bit taller
        self.fields['message'].widget.attrs.update({'rows': '4'})