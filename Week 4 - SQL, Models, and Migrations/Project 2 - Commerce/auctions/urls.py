from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create_listing, name="create_listing"),
    path("listings/<int:listing_id>", views.show_listing, name="show_listing"),
    path("watch", views.add_to_watchlist, name="add_to_watchlist"),
    path("unwatch", views.remove_from_watchlist, name="remove_from_watchlist"),
    path("bid", views.make_bid, name="make_bid"),
    path("close", views.close_auction, name="close_auction"),
    path("myauctions", views.my_auctions, name="my_auctions"),
    path("mybids", views.my_bids, name="my_bids"),
    path("mywatchlist", views.my_watchlist, name="my_watchlist"),
    path("comment", views.make_comment, name="make_comment"),
    path("categories", views.list_categories, name="list_categories"),
    path("categories/<int:category_id>", views.show_category, name="show_category"),
]