from django.db import models

class FuelStation(models.Model):
    opis_id = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    rack_id = models.IntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=5, decimal_places=3) # e.g., 3.459
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f"{self.name} - ${self.price}"