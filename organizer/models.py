from django.db import models

class Job(models.Model):
    input_path = models.CharField(max_length=255)
    output_path = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
