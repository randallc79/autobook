from django import forms

class InputForm(forms.Form):
    input_path = forms.CharField(label='Input Path', max_length=255, required=False)
    upload = forms.FileField(label='Upload Zip/Folder', required=False)
    output_path = forms.CharField(label='Output Path', max_length=255)
