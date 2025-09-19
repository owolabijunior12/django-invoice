from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings as django_settings
from .forms import *
from .models import *
from .functions import *

from django.contrib.auth.models import User, auth
from random import randint
from uuid import uuid4

from django.http import HttpResponse

import pdfkit
from django.template.loader import get_template
import os
import shutil
import platform


# --- helper: find wkhtmltopdf executable (cross-platform) ---
def find_wkhtmltopdf():
    # 1) explicit setting in settings.py
    cmd_from_settings = getattr(django_settings, "WKHTMLTOPDF_CMD", None)
    if cmd_from_settings:
        if os.path.exists(cmd_from_settings):
            return cmd_from_settings

    # 2) look on PATH
    wk = shutil.which("wkhtmltopdf")
    if wk:
        return wk

    # 3) common windows default
    if platform.system() == "Windows":
        common = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        if os.path.exists(common):
            return common

    # not found
    return None


#Anonymous required
def anonymous_required(function=None, redirect_url=None):

   if not redirect_url:
       redirect_url = 'dashboard'

   actual_decorator = user_passes_test(
       lambda u: u.is_anonymous,
       login_url=redirect_url
   )

   if function:
       return actual_decorator(function)
   return actual_decorator


def index(request):
    context = {}
    return render(request, 'invoice/index.html', context)


@anonymous_required
def login(request):
    context = {}
    if request.method == 'GET':
        form = UserLoginForm()
        context['form'] = form
        return render(request, 'invoice/login.html', context)

    if request.method == 'POST':
        form = UserLoginForm(request.POST)

        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('dashboard')
        else:
            context['form'] = form
            messages.error(request, 'Invalid Credentials')
            return redirect('login')

    return render(request, 'invoice/login.html', context)


@login_required
def dashboard(request):
    clients = Client.objects.all().count()
    invoices = Invoice.objects.all().count()
    paidInvoices = Invoice.objects.filter(status='PAID').count()

    context = {
        'clients': clients,
        'invoices': invoices,
        'paidInvoices': paidInvoices,
    }
    return render(request, 'invoice/dashboard.html', context)


@login_required
def invoices(request):
    invoices = Invoice.objects.all()
    return render(request, 'invoice/invoices.html', {'invoices': invoices})


@login_required
def products(request):
    products = Product.objects.all()
    return render(request, 'invoice/products.html', {'products': products})


@login_required
def clients(request):
    clients = Client.objects.all()
    context = {'clients': clients}

    if request.method == 'GET':
        form = ClientForm()
        context['form'] = form
        return render(request, 'invoice/clients.html', context)

    if request.method == 'POST':
        form = ClientForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'New Client Added')
            return redirect('clients')
        else:
            messages.error(request, 'Problem processing your request')
            return redirect('clients')

    return render(request, 'invoice/clients.html', context)


@login_required
def logout(request):
    auth.logout(request)
    return redirect('login')


###--------------------------- Create Invoice Views Start here --------------------------------------------- ###

@login_required
def createInvoice(request):
    # create a blank invoice ....
    number = 'INV-' + str(uuid4()).split('-')[1]
    newInvoice = Invoice.objects.create(number=number)
    newInvoice.save()

    inv = Invoice.objects.get(number=number)
    return redirect('create-build-invoice', slug=inv.slug)


def createBuildInvoice(request, slug):
    invoice = get_object_or_404(Invoice, slug=slug)

    products = Product.objects.filter(invoice=invoice)

    context = {'invoice': invoice, 'products': products}

    if request.method == 'GET':
        prod_form = ProductForm()
        inv_form = InvoiceForm(instance=invoice)
        client_form = ClientSelectForm(initial_client=invoice.client)
        context.update({'prod_form': prod_form, 'inv_form': inv_form, 'client_form': client_form})
        return render(request, 'invoice/create-invoice.html', context)

    if request.method == 'POST':
        prod_form = ProductForm(request.POST)
        inv_form = InvoiceForm(request.POST, instance=invoice)
        client_form = ClientSelectForm(request.POST, initial_client=invoice.client, instance=invoice)

        if prod_form.is_valid():
            obj = prod_form.save(commit=False)
            obj.invoice = invoice
            obj.save()
            messages.success(request, "Invoice product added succesfully")
            return redirect('create-build-invoice', slug=slug)
        elif inv_form.is_valid() and 'paymentTerms' in request.POST:
            inv_form.save()
            messages.success(request, "Invoice updated succesfully")
            return redirect('create-build-invoice', slug=slug)
        elif client_form.is_valid() and 'client' in request.POST:
            client_form.save()
            messages.success(request, "Client added to invoice succesfully")
            return redirect('create-build-invoice', slug=slug)
        else:
            context.update({'prod_form': prod_form, 'inv_form': inv_form, 'client_form': client_form})
            messages.error(request, "Problem processing your request")
            return render(request, 'invoice/create-invoice.html', context)

    return render(request, 'invoice/create-invoice.html', context)


# --- helper: get settings for an invoice (dynamic) ---
def get_settings_for_invoice(invoice):
    """
    Attempt to find Settings linked to invoice.client.
    Fall back to first Settings row, then None.
    """
    if invoice and hasattr(invoice, 'client') and invoice.client:
        # Use companyName field on Settings model instead of clientName
        client_field = getattr(invoice.client, 'companyName', None)  # <-- adjust if Client model uses companyName
        if client_field:
            p_settings = Settings.objects.filter(companyName=client_field).first()  # <-- updated here
            if p_settings:
                return p_settings

    # fallback to first settings row
    return Settings.objects.first()

def viewPDFInvoice(request, slug):
    invoice = get_object_or_404(Invoice, slug=slug)
    products = Product.objects.filter(invoice=invoice)

    # Get Client Settings dynamically
    p_settings = get_settings_for_invoice(invoice)
    if not p_settings:
        messages.error(request, "Company settings not found. Please add settings in admin.")
        return redirect('invoices')

    # Calculate the Invoice Total
    invoiceCurrency = ''
    invoiceTotal = 0.0
    for x in products:
        y = float(x.quantity) * float(x.price)
        invoiceTotal += y
        if getattr(x, 'currency', None):
            invoiceCurrency = x.currency

    context = {
        'invoice': invoice,
        'products': products,
        'p_settings': p_settings,
        'invoiceTotal': "{:.2f}".format(invoiceTotal),
        'invoiceCurrency': invoiceCurrency,
    }

    return render(request, 'invoice/invoice-template.html', context)


def viewDocumentInvoice(request, slug):
    invoice = get_object_or_404(Invoice, slug=slug)
    products = Product.objects.filter(invoice=invoice)

    # Get Client Settings dynamically
    p_settings = get_settings_for_invoice(invoice)
    if not p_settings:
        messages.error(request, "Company settings not found. Please add settings in admin.")
        return redirect('invoices')

    # Calculate the Invoice Total
    invoiceTotal = sum(float(x.quantity) * float(x.price) for x in products)

    context = {
        'invoice': invoice,
        'products': products,
        'p_settings': p_settings,
        'invoiceTotal': "{:.2f}".format(invoiceTotal),
    }

    # The name of your PDF file
    filename = '{}.pdf'.format(invoice.uniqueId)

    # HTML file to be converted to PDF - inside your Django directory
    template = get_template('invoice/pdf-template.html')

    # Render the HTML
    html = template.render(context)

    # Options - Very Important
    options = {
        'encoding': 'UTF-8',
        'javascript-delay': '10',
        'enable-local-file-access': None,
        'page-size': 'A4',
        'custom-header': [('Accept-Encoding', 'gzip')],
    }

    wk_path = find_wkhtmltopdf()
    if not wk_path:
        messages.error(request,
            "wkhtmltopdf not found. Install wkhtmltopdf and/or set WKHTMLTOPDF_CMD in settings.py.")
        return redirect('invoices')

    try:
        config = pdfkit.configuration(wkhtmltopdf=wk_path)
    except Exception as e:
        messages.error(request, f"Error configuring PDF generator: {e}")
        return redirect('invoices')

    # IF you have CSS to add to template
    css1 = os.path.join(django_settings.CSS_LOCATION, 'assets', 'css', 'bootstrap.min.css')
    css2 = os.path.join(django_settings.CSS_LOCATION, 'assets', 'css', 'dashboard.css')

    # Create the file (in-memory)
    try:
        file_content = pdfkit.from_string(html, False, configuration=config, options=options)
    except Exception as e:
        messages.error(request, f"PDF generation error: {e}")
        return redirect('invoices')

    response = HttpResponse(file_content, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename={}'.format(filename)
    return response


def emailDocumentInvoice(request, slug):
    invoice = get_object_or_404(Invoice, slug=slug)
    products = Product.objects.filter(invoice=invoice)

    # Get Client Settings dynamically
    p_settings = get_settings_for_invoice(invoice)
    if not p_settings:
        messages.error(request, "Company settings not found. Please add settings in admin.")
        return redirect('invoices')

    invoiceTotal = sum(float(x.quantity) * float(x.price) for x in products)

    context = {
        'invoice': invoice,
        'products': products,
        'p_settings': p_settings,
        'invoiceTotal': "{:.2f}".format(invoiceTotal),
    }

    filename = '{}.pdf'.format(invoice.uniqueId)
    template = get_template('invoice/pdf-template.html')
    html = template.render(context)

    options = {
        'encoding': 'UTF-8',
        'javascript-delay': '1000',
        'enable-local-file-access': None,
        'page-size': 'A4',
        'custom-header': [('Accept-Encoding', 'gzip')],
    }

    wk_path = find_wkhtmltopdf()
    if not wk_path:
        messages.error(request,
            "wkhtmltopdf not found. Install wkhtmltopdf and/or set WKHTMLTOPDF_CMD in settings.py.")
        return redirect('invoices')

    try:
        config = pdfkit.configuration(wkhtmltopdf=wk_path)
    except Exception as e:
        messages.error(request, f"Error configuring PDF generator: {e}")
        return redirect('invoices')

    # Save PDF
    filepath = os.path.join(django_settings.MEDIA_ROOT, 'client_invoices')
    os.makedirs(filepath, exist_ok=True)
    pdf_save_path = os.path.join(filepath, filename)

    try:
        pdfkit.from_string(html, pdf_save_path, configuration=config, options=options)
    except Exception as e:
        messages.error(request, f"PDF save error: {e}")
        return redirect('invoices')

    # send the emails to client
    to_email = invoice.client.emailAddress if getattr(invoice.client, 'emailAddress', None) else None
    from_client = p_settings.clientName if getattr(p_settings, 'clientName', None) else None
    if to_email:
        emailInvoiceClient(to_email, from_client, pdf_save_path)

    invoice.status = 'EMAIL_SENT'
    invoice.save()

    messages.success(request, "Email sent to the client succesfully")
    return redirect('create-build-invoice', slug=slug)


def deleteInvoice(request, slug):
    try:
        Invoice.objects.get(slug=slug).delete()
    except Exception:
        messages.error(request, 'Something went wrong')
        return redirect('invoices')

    return redirect('invoices')


def companySettings(request):
    # return the primary settings (first) or redirect with message
    company = Settings.objects.first()
    if not company:
        messages.error(request, "No company settings found. Please add one in admin.")
        return redirect('dashboard')
    return render(request, 'invoice/company-settings.html', {'company': company})
