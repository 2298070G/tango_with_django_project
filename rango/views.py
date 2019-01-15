from django.shortcuts import render

from django.http import HttpResponse


def index(request):
    # Construct a dictionary to pass to the template engine as its context.
    # Note the key boldmessage is the same as {{ boldmessage }} in the template!
    context_dict = {'boldmessage': "Crunchy, creamy, cookie, candy, cupcake!"}

    # Return a rendered response to send to te clientself.
    # We make use of the shortcut function to make our live easier.
    # Note that the first parameter is the template we wish to use.
    return render(request, 'rango/index.html', context=context_dict)


def about(request):
    # A context dictionary for the about page
    context_dict = {'cat': "star wars, cute, small"}

    # Use the render function to generate rendered response
    return render(request, 'rango/about.html', context=context_dict)