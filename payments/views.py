from django.db import IntegrityError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from payments.forms import SigninForm, CardForm, UserForm
from payments.models import User
import Django_Commerce.settings as settings
import stripe
import datetime
import json
from django.views.decorators.csrf import csrf_exempt


stripe.api_key = settings.STRIPE_SECRET


def soon():
    soon = datetime.date.today() + datetime.timedelta(days=30)
    return {'month': soon.month, 'year': soon.year}


def sign_in(request):
    print "signing in"
    user = None
    if request.method == 'POST':
        form = SigninForm(request.POST)
        if form.is_valid():
            print "form is valid"
            results = User.objects.filter(email=form.cleaned_data['email'])
            if len(results) == 1:

                # if results[0].(form.cleaned_data['password']):
                if results[0].password == form.cleaned_data['password']:
                    request.session['user'] = results[0].pk
                    return HttpResponseRedirect('/')
                else:
                    form.addError('Incorrect email address or password')
                    print "debug 1"
            else:
                print "debug 2"
                form.addError('Incorrect email address or password')
    else:
        form = SigninForm()

    print form.non_field_errors()

    return render_to_response(
        'sign_in.html',
        {
            'form': form,
            'user': user
        },
        context_instance=RequestContext(request)
    )


def sign_out(request):
    try:
        del request.session['user']
    except Exception, e:
        print e
    return HttpResponseRedirect('/')


def register(request):
    user = None
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():

            #update based on your billing method (subscription vs one time)
            # customer = stripe.Customer.create(
            #     email=form.cleaned_data['email'],
            #     description=form.cleaned_data['name'],
            #     card=form.cleaned_data['stripe_token'],
            #     plan="gold",
            # )

            customer = stripe.Charge.create(
                description=form.cleaned_data['email'],
                card=form.cleaned_data['stripe_token'],
                amount="5000",
                currency="usd"
            )

            user = User(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                last_4_digits=form.cleaned_data['last_4_digits'],
                stripe_id=customer.id,
            )

            #ensure encrypted password
            user.set_password(form.cleaned_data['password'])

            try:
                user.save()
            except IntegrityError:
                form.addError(user.email + ' is already a member')
            else:
                request.session['user'] = user.pk
                return HttpResponseRedirect('/')

    else:
        form = UserForm()

    return render_to_response(
        'register.html',
        {
            'form': form,
            'months': range(1, 12),
            'publishable': settings.STRIPE_PUBLISHABLE,
            'soon': soon(),
            'user': user,
            'years': range(2011, 2036),
        },
        context_instance=RequestContext(request)
    )


@csrf_exempt
def edit2(request):

    print "hit 1"
    json_dict = {}

    uid = request.user.id

    if uid is None:
        return HttpResponseRedirect('/')

    user = User.objects.get(pk=uid)

    print "hit 2"
    if request.method == "GET":
        json_dict['error'] = "error"
        print "hit error"
        return HttpResponse(json.dumps(json_dict))

    if request.method == "POST":
        print "hit post"

        new_user = User(name="new", email="new@email.com")

        new_user.save()

        user.last_4_digits = request.POST.get("digits", None)
        user.stripe_id = request.POST.get("token", None)
        user.save()


        json_dict['saved'] = True

    return HttpResponse(json.dumps(json_dict))


def edit(request):
    context = {}
    uid = request.session.get('user')

    if uid is None:
        return HttpResponseRedirect('/')

    user = User.objects.get(pk=uid)

    if request.method == 'POST':
        form = CardForm(request.POST)
        if form.is_valid():

            customer = stripe.Customer.retrieve(user.stripe_id)
            customer.card = form.cleaned_data['stripe_token']
            customer.save()

            user.last_4_digits = form.cleaned_data['last_4_digits']
            user.stripe_id = customer.id
            user.save()

            return HttpResponseRedirect('/')

    else:
        form = CardForm()

    return render_to_response(
        'edit2.html',
        context,
        # {
        #     'form': form,
        #     'publishable': settings.STRIPE_PUBLISHABLE,
        #     'soon': soon(),
        #     'months': range(1, 12),
        #     'years': range(2011, 2036)
        # },
        context_instance=RequestContext(request)
    )