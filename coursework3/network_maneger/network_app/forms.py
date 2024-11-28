from django import forms

class DeviceConfigForm(forms.Form):
    ip = forms.GenericIPAddressField(label='Device IP Address')
    username = forms.CharField(max_length=100, label='Username')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')
    secret = forms.CharField(widget=forms.PasswordInput, label='Enable Secret')
    interface = forms.CharField(max_length=100, label='Interface (e.g., Loopback0)')
    ip_addr = forms.GenericIPAddressField(label='Interface IP Address')
    mask = forms.GenericIPAddressField(label='Subnet Mask')