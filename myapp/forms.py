from django import forms
from .models import *
from django.core.exceptions import ValidationError
import re


class EmailLoginForm(forms.Form):
    email = forms.EmailField(max_length=254,label='',label_suffix='', required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}))



class OTPForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,  # Ensure exactly 6 digits
        label='',  # No label text
        label_suffix='',  # No suffix
        required=True,
        help_text="Enter the 6-digit OTP sent to your email",
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your OTP',
                'maxlength': '6',  # Limit input to 6 characters
                'pattern': r'\d{6}',  # Regex pattern for 6 digits
                'oninput': 'this.value=this.value.replace(/[^0-9]/g,"");'  # Remove non-numeric input
            }
        )
    )

    def clean_otp(self):
        otp = self.cleaned_data.get('otp')

        # Check if the OTP contains only digits
        if not otp.isdigit():
            raise ValidationError("OTP must contain only digits.")

        return otp


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name','email','subject','message']


class UpdateRevForm(forms.ModelForm):
    review = forms.CharField(label='Review',label_suffix='', required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Review'}))
    rating = forms.FloatField(label='Rating', label_suffix='',required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Rating'}))

    def clean_rating(self):
        rating = self.cleaned_data['rating']
        if rating < 0.0 or rating > 5.0:
            raise forms.ValidationError('Rating should be between 0.0 and 5.0.')
        return rating

    class Meta:
        model = ReviewRating
        fields = ['review', 'rating','img1','img2','img3','img4','img5']


class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['review', 'rating','img1','img2','img3','img4','img5']

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name','last_name','phone','email','address_line_1','address_line_2',
        'country','state','city','order_note',]


class UserForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = [
            'first_name', 'last_name', 'phone_number',
            'address_line_1', 'address_line_2',
            'city', 'state', 'country', 'img'
            ]
    COUNTRY_CHOICES = [
        ('IN', 'India'),
        ('PK', 'Pakistan'),
        ('BD', 'Bangladesh')
    ]

    STATE_CHOICES = [
        ('UP', 'Uttar Pradesh'),
        ('MH', 'Maharashtra'),
        ('TN', 'Tamil Nadu'),
        ('KA', 'Karnataka'),
        ('WB', 'West Bengal'),
        ('GJ', 'Gujarat'),
        ('RJ', 'Rajasthan'),
        ('DL', 'Delhi'),
        ('AP', 'Andhra Pradesh'),
        ('HR', 'Haryana')
    ]

    CITY_CHOICES = [
        ('LU', 'Lucknow'),
        ('MU', 'Mumbai'),
        ('BLR', 'Bangalore'),
        ('DEL', 'Delhi'),
        ('KOL', 'Kolkata'),
        ('CHN', 'Chennai'),
        ('HYD', 'Hyderabad'),
        ('PUN', 'Pune'),
        ('CBE', 'Coimbatore'),
        ('SUR', 'Surat')
    ]

    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter First Name'})
    )

    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Last Name'})
    )

    address_line_1 = forms.CharField(
        max_length=100,
        min_length=20,
        label="Address Line 1",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Address Line 1'})
    )

    address_line_2 = forms.CharField(
        max_length=100,
        min_length=20,
        label="Address Line 2",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Address Line 2'})
    )

    city = forms.ChoiceField(
        choices=CITY_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'City'})
    )

    state = forms.ChoiceField(
        choices=STATE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'State'})
    )

    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'Country'})
    )

    phone_number = forms.CharField(
        required=True,
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+919387463744'}),
    )

    img = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'})
    )

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        # Check if the phone number starts with '+91' and is 13 digits long
        if not phone_number.startswith('+91') or len(phone_number) != 13 or not phone_number[1:].isdigit():
            raise forms.ValidationError("Phone number must be in the format +919387463744.")
        return phone_number

    def clean(self):
        cleaned_data = super().clean()

        # Validate all required fields to ensure none are empty
        required_fields = [
            'address_line_1', 'address_line_2',
            'city', 'state', 'country'
        ]
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, f"{field.replace('_', ' ').capitalize()} is required.")

        return cleaned_data
