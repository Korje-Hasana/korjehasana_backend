from django.db import models

# Create your models here.

class LoanReason(models.Model):
    reason = models.TextField()
    
    def __str__(self):
        return self.reason
