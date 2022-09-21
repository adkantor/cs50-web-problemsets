from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.forms.widgets import NumberInput
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django import forms
from django.contrib import messages

from .models import User, Listing, Bid, Comment, Category


class ListingForm(forms.ModelForm):
    """ Form to create a new listing. """
    class Meta:
        model = Listing
        fields = ['title', 'description', 'starting_bid', 'image_url', 'category']


def index(request):
    # get list of active listings
    listings = Listing.objects.filter(is_active=True)
    return render(request, "auctions/index.html", {
        "listings": listings
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        next = request.POST["next"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            if next:
                return HttpResponseRedirect(next)
            else:
                return HttpResponseRedirect(reverse("index"))
        else:
            messages.error(request, "Invalid username and/or password.")
            return render(request, "auctions/login.html")
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            messages.error(request, "Passwords must match.")
            return render(request, "auctions/register.html")

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            messages.error(request, "Username already taken.")
            return render(request, "auctions/register.html")
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def create_listing(request):
    """ Records a new listing to the database """
    
    if request.method == 'POST':
        # load the contents of the posted form into a variable
        form = ListingForm(request.POST)
        
        # validate by server
        if form.is_valid():
            listing = form.save(commit=False)
            listing.created_by = request.user
            listing.save()
            return HttpResponseRedirect(reverse("index"))
        else:
            # return the filled-in form with error message
            messages.error(request, "Invalid form data.")
            return render(request, "auctions/createlisting.html", {
                "form": form
            })
    
    else:
        return render(request, "auctions/createlisting.html", {
            "form": ListingForm()
        })


def show_listing(request, listing_id):
    """ Shows a page specific to the listing given as parameter. """

    # get listing
    listing = Listing.objects.get(pk=listing_id)
    # check if user is winner - if so, prepare message
    if request.user == listing.winner():
        messages.info(request, 'You have win the auction!') 
    # show the page
    return render(request, "auctions/showlisting.html", {
        "listing": listing,
    })


@login_required(login_url='login')
def add_to_watchlist(request):
    """ Adds the listing to the user's watchlist. """
    
    # get listing
    listing_id = int(request.POST.get('listingId'))
    listing = Listing.objects.get(pk=listing_id)
    # add to user's watchlist
    request.user.watchlisted_items.add(listing)
    
    # return to the page
    return HttpResponseRedirect(reverse("show_listing", args=[listing_id]))


@login_required(login_url='login')
def remove_from_watchlist(request):
    """ Removes the listing from the user's watchlist. """

    # get listing
    listing_id = int(request.POST.get('listingId'))
    listing = Listing.objects.get(pk=listing_id)
    # remove from user's watchlist
    request.user.watchlisted_items.remove(listing)
    
    # return to the page
    return HttpResponseRedirect(reverse("show_listing", args=[listing_id]))


@login_required(login_url='login')
def make_bid(request):
    """ Records a new bid to the database. """
    
    # get listing
    listing_id = int(request.POST.get('listingId'))
    listing = Listing.objects.get(pk=listing_id)
    # get bid price
    bid_price = float(request.POST.get('bidPrice'))

    # if there is a bid and bid price not higher then current bid -> error
    if listing.current_bid() and bid_price <= listing.current_bid().price:
        # show error message
        messages.error(request, "Invalid bid (new bid price must be higher than current bid)")
        return render(request, "auctions/showlisting.html", {
            "listing": listing,
        })
    
    elif bid_price <= listing.starting_bid:
        # show error message
        messages.error(request, "Invalid bid (bid price must be higher than starting bid)")
        return render(request, "auctions/showlisting.html", {
            "listing": listing,
        })

    else:       
        # create the new bid
        bid = Bid(
            bidder=request.user, 
            listing=listing,
            price=bid_price
        )
        bid.save()
        
        # return to the page
        return HttpResponseRedirect(reverse("show_listing", args=[listing_id]))


@login_required
def close_auction(request):
    
    # get listing
    listing_id = int(request.POST.get('listingId'))
    listing = Listing.objects.get(pk=listing_id)

    # check if user is the one who created the listing
    if listing.created_by.id != request.user.id:
        # show error message
        messages.error(request, "You have no permission to perform this operation!")
        return render(request, "auctions/showlisting.html", {
            "listing": listing,
        })

    # close listing
    listing.is_active = False
    listing.save()

    messages.warning(request, "Auction has been closed.")
    return render(request, "auctions/showlisting.html", {
        "listing": listing,
    })


@login_required
def my_auctions(request):
    # get list of auctions created by current user
    listings = Listing.objects.filter(created_by=request.user)
    return render(request, "auctions/myauctions.html", {
        "listings": listings
    })


@login_required
def my_bids(request):
    # get list of auctions where current user placed a bid
    listings = Listing.objects.filter(bids__bidder=request.user).distinct()
    return render(request, "auctions/mybids.html", {
        "listings": listings
    })

@login_required
def my_watchlist(request):
    # get list of auctions where current user placed a bid
    listings = Listing.objects.filter(watchlisted_by=request.user)
    return render(request, "auctions/mywatchlist.html", {
        "listings": listings
    })

@login_required
def make_comment(request):
    
    # get listing
    listing_id = int(request.POST.get('listingId'))
    listing = Listing.objects.get(pk=listing_id)
    # get bid price
    text = request.POST.get('commentText')

    # create the new comment
    comment = Comment(
        created_by=request.user, 
        listing=listing,
        text=text
    )
    comment.save()
    
    # return to the page
    return HttpResponseRedirect(reverse("show_listing", args=[listing_id])) 


def list_categories(request):
    """ Page that displays a list of all listing categories """
    
    # get category counts
    categories = Listing.category_counts()

    return render(request, "auctions/categories.html", {
        "categories": categories
    })


def show_category(request, category_id):
    """ Shows a list of active listings filtered by category. """
    
    # get list of filtered active listings
    listings = Listing.objects.filter(is_active=True, category=category_id)
    category = Category.objects.get(pk=category_id)
    
    return render(request, "auctions/category.html", {
        "listings": listings,
        "category": category
    })