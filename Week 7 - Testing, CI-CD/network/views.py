import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required 
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator

from .models import User, Post


def index(request):
    """ Displays all posts plus button to add new post. """
    
    # get list of all posts and paginate (10 posts / page)
    post_list = Post.get_all_posts()
    paginator = Paginator(post_list, 10)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "network/index.html", {
        'page_obj': page_obj
    })


@login_required
def following(request):
    """ Displays posts of followed people plus button to add new post. """
    
    # get list of filtered posts and paginate (10 posts / page)
    post_list = request.user.get_posts_of_followed_people()
    paginator = Paginator(post_list, 10)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "network/index.html", {
        'page_obj': page_obj
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


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
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


def profiles(request, user_id):
    """ Shows a profile page specific to the user given as parameter. """
    
    # get user
    p_user = User.objects.get(pk=user_id) 

    # get list of all posts of the user and paginate (10 posts / page)
    post_list = Post.objects.filter(created_by=p_user).order_by('-created_time')
    paginator = Paginator(post_list, 10)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "network/profile.html", {
        'p_user': p_user,
        'page_obj': page_obj
    })


##############
# API ROUTES #
##############

@login_required
def post(request, post_id):
    # Query for requested post
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found."}, status=404)

    # Return post contents
    if request.method == "GET":
        return JsonResponse(post.serialize())

    # Update post data
    elif request.method == "PUT":
        data = json.loads(request.body)
        
        if data.get("post_content") is not None:
            # if request user is not the creator of the post then deny access
            if post.created_by != request.user:
                return HttpResponse(status=403)
            else:
                post.content = data["post_content"]
                post.save()
        
        if data.get("liking") is not None:
            liking = data["liking"]
            if liking:
                post.liked_by.add(request.user)
            else:
                post.liked_by.remove(request.user)
            post.save()
        
        return HttpResponse(status=204)

    # post must be via GET or PUT
    else:
        return JsonResponse({
            "error": "GET or PUT request required."
        }, status=400)
 

@login_required
def create_post(request):
    
    # creating a new post must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    # Check post content
    data = json.loads(request.body)
    post_content = data.get("post_content")
    if len(post_content) == 0:
        return JsonResponse({
            "error": "At least one character required."
        }, status=400)

    # add post
    post = Post(
        created_by = request.user,
        content = post_content
    )
    post.save()

    return JsonResponse({"message": "Post created successfully."}, status=201) 


@login_required
def follow(request, user_id):

    # Query for requested user
    try:
        p_user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

    # Return follow status: True if logged in user is following profile user
    if request.method == "GET":
        
        return JsonResponse({
            'isfollowing': request.user.is_following(p_user)
        })

    # Update following: if True then logged in user will follow profile user
    elif request.method == "PUT":
        data = json.loads(request.body)
        if data.get('isfollowing') is not None:
            # follow
            if data['isfollowing']:
                request.user.follow(p_user)
                # print('follow successful')
            else:
                request.user.unfollow(p_user)
                # print('unfollow successful')
        else:
            print('no data')
        return HttpResponse(status=204) 

    # follow must be via GET or PUT 
    else:
        return JsonResponse({
            "error": "GET or PUT request required."
        }, status=400)