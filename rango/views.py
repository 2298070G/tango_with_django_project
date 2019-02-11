from django.shortcuts import render
from django.http import HttpResponse

# Import the Category model
from rango.models import Category
from rango.models import Page

from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm

from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from datetime import datetime
from rango.webhose_search import run_query
from django.shortcuts import redirect


def index(request):
    request.session.set_test_cookie()
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]
    context_dict = {'categories': category_list, 'pages': page_list}

    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']

    response = render(request, 'rango/index.html', context=context_dict)

    # Render the response and send it back!
    return response


def about(request):
    context_dict = {}
    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']

    # prints out whether the metohd is a GET or a POST
    print(request.method)
    # prints out the user name, if no one is logged in it prints 'AnonymousUser'
    print(request.user)
    return render(request, 'rango/about.html', context_dict)


def show_category(request, category_name_slug):
    # Create a context dictionary which we can pass
    # to the template rendering engine
    context_dict = {}

    try:
        # Can we find a category name slug with the given name?
        # If we can't, the .get() method reises a DoesNotExist exception.
        # So the .get() method returns one model instance or raises an exception
        category = Category.objects.get(slug=category_name_slug)

        # Retrieve all of the associated pages.
        # Note that filter() will return a list of page objects or an empty list
        pages = Page.objects.filter(category=category)

        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        # We also add the category object from
        # the database to the context dictionary
        # We'll use this in the template to verify that the category exists.
        context_dict['category'] = category
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category
        # Don't do anything
        # the template will display the "no category" message for us.
        context_dict['category'] = None
        context_dict['pages'] = None

    # Go render the response and return it to the client
    return render(request, 'rango/category.html', context_dict)


@login_required
def add_category(request):
    form = CategoryForm()

    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            cat = form.save(commit=True)
            # Now that the category is saved
            # We could give a confirmation message
            # But since the most recent category added is on the index page
            # Then we can direct the user back to the index page.
            return index(request)
        else:
            # The supplied form contained errors -
            # just print them to teminal.
            print(form.errors)

    # Will handle the bad form, new form, or no form supplied cases.
    # Render the form with error messages, if any.
    return render(request, 'rango/add_category.html', {'form': form})


@login_required
def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None

    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.category = category
            page.views = 0
            page.save()
            return show_category(request, category_name_slug)
        else:
            print(form.errors)

    context_dict = {'form': form, 'category': category}
    return render(request, 'rango/add_page.html', context_dict)


def register(request):
    # A boolean value for telling the template
    # whether the registration was successful.
    # set to False initially. Code change value to
    # True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're intrested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information
        # Note that we make use of both UserForm and UserProfileForm
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves,
            # we set commit=False. This delays saving the model
            # until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide pic?
            # if so, we need to get it from input form and
            # put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance
            profile.save()

            # Update our variable to indicate that the template
            # registration was successful
            registered = True
        else:
            # Invlaid form or forms
            # print probs
            print(user_form.errors, profile_form.errors)
    else:
        # Not HTTP POST, so we render our form using two modelForm instances
        # THese forms will be blank, ready for user input
        user_form = UserForm()
        profile_form = UserProfileForm()
    # Render the template depending on the context
    return render(request, 'rango/register.html', {'user_form': user_form,
                                                   'profile_form': profile_form, 'registered': registered})


def user_login(request):
    # If request is a HTTP POST, try to pull out the relevant info.
    if request.method == 'POST':
        # Get username and password from user, from login form
        # POST.get will return none if there is none instead of an error like
        # POST[<variable>]
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Django checks if user/pass is valid, oject returned if it is
        user = authenticate(username=username, password=password)

        # If object then details correct, if None then no matching details wre found
        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                return HttpResponse("Your Rango account is disabled.")
        else:
            # bad login
            print("Invalid login details: {0}, {1}".format(username, password))
            return HttpResponse("Invalid login details supplied.")

    # Request isn't POST, so display login form
    else:
        return render(request, 'rango/login.html', {})


@login_required
def restricted(request):
    return render(request, 'rango/restricted.html', {})


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))


def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val


def visitor_cookie_handler(request):
    visits = int(get_server_side_cookie(request, 'visits', '1'))
    last_visit_cookie = get_server_side_cookie(
        request, 'last_visit', str(datetime.now()))

    last_visit_time = datetime.strptime(
        last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')

    if (datetime.now() - last_visit_time).days > 0:
        visits = visits+1
        request.session['last_visit'] = str(datetime.now())
    else:
        request.session['last_visit'] = last_visit_cookie

    request.session['visits'] = visits

def search(request):
    result_list=[]
    query=''
    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            result_list = run_query(query)
    
    return render(request, 'rango/search.html', {'result_list':result_list,'query':query})

def track_url(request):
    id=None
    url='/rango/'
    if request.method=='GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
        try:
            page = Page.objects.get(id=page_id)
            page.views =page.views+1
            page.save()
            url = page.url
        except:
            pass

    return redirect(url)


