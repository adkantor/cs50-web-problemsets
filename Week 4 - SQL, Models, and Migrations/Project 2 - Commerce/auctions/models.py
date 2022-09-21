from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Max


class User(AbstractUser):
    pass


class Category(models.Model):
    """ Class to represent a category. """

    name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.name}"


class Listing(models.Model):
    """ Class to represent a listing. """    
    title = models.CharField(max_length=100)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    image_url = models.URLField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings', null=True)
    created_time = models.DateTimeField(auto_now_add=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    watchlisted_by = models.ManyToManyField(User, blank=True, related_name='watchlisted_items')

    def __str__(self):
        return f"{self.title} | {self.created_by} | {'Active' if self.is_active else 'Closed'} | {self.created_time}"

    def current_bid(self):
        """ Returns the highest bid for this listing (if has a valid bid). Returns None otherwise. """
        max_bid_price = self.bids.aggregate(max_bid=Max('price'))['max_bid']
        if max_bid_price:
            return Bid.objects.get(listing=self, price=max_bid_price)
        return None

    def winner(self):
        """ Returns the winner of this listing (if closed and has a valid bid). Returns None otherwise. """
        highest_bid = self.current_bid()
        if not self.is_active and highest_bid:
            return highest_bid.bidder
        return None

    @classmethod
    def category_counts(cls):
        """ Returns dictionary mapping {category id : (category name, count)}. """
        d = dict()
        for cat in Category.objects.all():
            cat_id = cat.id
            cat_name = cat.name
            cat_count = cls.objects.filter(category=cat, is_active=True).count()
            d[cat_id] = (cat_name, cat_count)
        return d


class Bid(models.Model):
    """ Class to represent a bid. """
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids', null=True)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bids', null=True)
    time = models.DateTimeField(auto_now_add=True, null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.bidder} | {self.listing.title} | ${self.price} | {self.time}"


class Comment(models.Model):
    """ Class to represent a comment. """
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', null=True)
    created_time = models.DateTimeField(auto_now_add=True, null=True)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='comments', null=True)
    text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.created_by} | {self.listing.title} | ${(self.text)[:30]}[...] | {self.created_time}"
