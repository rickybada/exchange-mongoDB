from django.db import models
from django.contrib.auth.models import User
from djongo.models.fields import ObjectIdField
import random

class Profile(models.Model):
    _id = ObjectIdField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ips = models.Field(default=[])
    subprofiles = models.Field(default={})
    usd_balance = models.FloatField(default=0)
    btc_balance = models.FloatField(default=0)
    
    def save(self, *args, **kwargs):
        if not self._id:  # Se il profilo è nuovo e non ha ancora un ID
            self.btc_balance = random.uniform(1, 10) # Assegna un saldo BTC casuale tra 1 e 10
            self.usd_balance = random.uniform(1000, 10000) # Assegna un saldo USD casuale tra 1000 e 10000
        super(Profile, self).save(*args, **kwargs)  # Chiama il metodo save() originale
        
    profit_loss = models.FloatField(default=0)
    average_weighted = models.FloatField(default=0) # media ponderata
    
    def calculate_average_weighted(self):
        orders = Order.objects.filter(profile=self, type='buy')
        total_sum = sum(order.order_price for order in orders)
        total_quantity = sum(order.btc_quantity for order in orders)

        if total_quantity == 0:
            self.average_weighted = 0
        else:
            self.average_weighted = total_sum / total_quantity
        
        self.save()
    

class Order(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]
    TYPE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    _id = ObjectIdField()
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    order_price = models.FloatField() # prezzo dell'ordine
    btc_price = models.FloatField(default=0.0) # prezzo BTC, aggiungere API conimarketcup
    btc_quantity = models.FloatField(default=0)
    status = models.CharField(
        max_length=6,
        choices=STATUS_CHOICES,
        default='open'
    )
    type = models.CharField(
        max_length=4,
        choices=TYPE_CHOICES,
        default='buy'
    )
    buyer = models.ForeignKey(User, related_name='buy_orders', on_delete=models.SET_NULL, null=True, blank=True)
    seller = models.ForeignKey(User, related_name='sell_orders', on_delete=models.SET_NULL, null=True, blank=True)
    executed_price = models.FloatField(null=True, blank=True)
