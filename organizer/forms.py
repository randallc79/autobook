from django import forms

class InputForm(forms.Form):
    input_path = forms.CharField(label='Input Path or Upload', max_length=255)
    output_path = forms.CharField(label='Output Path', max_length=255)
    # Add file upload field if needed: forms.FileField()
