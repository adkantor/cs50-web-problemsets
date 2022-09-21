import random

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django import forms
from django.contrib import messages

from . import util

import markdown2


class EntryForm(forms.Form):
    """ Class to create or update an entry. """
    title = forms.CharField(
        label='', 
        widget=forms.TextInput(attrs={
            'class' : 'entry-form-title',
            'placeholder': 'Enter title here'
        })
    )
    content = forms.CharField(
        label = '', 
        widget=forms.Textarea(attrs={
            'class' : 'entry-form-content',
            'placeholder': 'Write your article here'
        })
    )


def index(request):
    entries = util.list_entries()
    return render(request, "encyclopedia/index.html", {
        "entries": entries
    })

def entry(request, title):
    entry_content = util.get_entry(title)
    if entry_content is not None:
        entry_content = markdown2.markdown(entry_content)
    return render(request, "encyclopedia/entry.html", {
        "title": title,
        "entry": entry_content
    })

def search(request):
    search_query = request.GET.get('q')
    entries = util.list_entries()
    
    # If the query matches the name of an encyclopedia entry, 
    # the user should be redirected to that entry?s page.
    if search_query.lower() in [entry.lower() for entry in entries]:
        return HttpResponseRedirect(reverse("entry", args=[search_query]))
    
    # otherwise the user should instead be taken to a search results page that 
    # displays a list of all encyclopedia entries that have the query as a substring.
    else:
        search_results = [entry for entry in entries if search_query.lower() in entry.lower()]
        return render(request, "encyclopedia/search.html", {
            "search_results": search_results
        })

def random_page(request):
    title = random.choice(util.list_entries())
    return HttpResponseRedirect(reverse("entry", args=[title]))

def create_new_page(request):
    if request.method == "POST":
        
        # load the contents of the posted form into a variable
        form = EntryForm(request.POST)
        
        # validate by server
        if form.is_valid():
            title = form.cleaned_data["title"]
            content = form.cleaned_data["content"]
            
            # check if title does not exist yet
            if title.lower() not in [entry.lower() for entry in util.list_entries()]:
                # save entry
                util.save_entry(title, content)
                # redirect to the entry's page
                messages.success(request, "The entry was successfully saved.")
                return HttpResponseRedirect(reverse("entry", args=[title]))
            else:
                # if an encyclopedia entry already exists with the provided title, 
                # the user should be presented with an error message
                messages.error(request, "An entry with the same title already exists!")
                # render tasks/add.html page but with existing inputs
                return render(request, "encyclopedia/new.html", {
                    "form": form
                })
        else:
            messages.error(request, "Invalid")
            # render tasks/add.html page but with existing inputs
            return render(request, "encyclopedia/new.html", {
                "form": form
            })

    else:
        return render(request, "encyclopedia/new.html", {
            "form": EntryForm() 
        })

def edit_page(request):
    # edit entry was clicked on an entry's page
    if request.method == 'GET':
        title = request.GET.get('title')
        content = util.get_entry(title)
        form = EntryForm(initial={
            'title' : title,
            'content' : content
        })
        form.fields['title'].widget.attrs['readonly'] = True
        return render(request, "encyclopedia/edit.html", {
            "form": form
        })

    # an entry was updated on the edit page
    if request.method == 'POST':
        # load the contents of the posted form into a variable
        form = EntryForm(request.POST)
        
        # validate by server
        if form.is_valid():
            title = form.cleaned_data["title"]
            content = form.cleaned_data["content"]
        
            # save entry
            util.save_entry(title, content)
            # redirect to the entry's page
            messages.success(request, "The entry was successfully updated.")
            return HttpResponseRedirect(reverse("entry", args=[title]))
        else:
            messages.error(request, "Invalid")
            # render tasks/add.html page but with existing inputs
            return render(request, "encyclopedia/edit.html", {
                "form": form
            })