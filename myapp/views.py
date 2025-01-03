from django.shortcuts import render , redirect
from .models import *
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage,PageNotAnInteger,Paginator
from django.shortcuts import HttpResponse
from django.core.exceptions import ValidationError
from django.contrib import messages , auth
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from .models import Account

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode , urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives
import requests
import datetime
from .forms import *
import json
from django.conf import settings


from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle



def cancel_session(request):
    request.session.flush()  # Clear the session
    return redirect('Home')  # Redirect to a home or login page


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        reg = Contact(name=name,email=email,subject=subject,message=message)
        reg.save()
        messages.info(request,'Your form was submitted successfully!')
    return render(request,'myapp/contact.html')

def updaterev(request, user_id):
    next_url = request.GET.get('next', '/')
    try:
        data = ReviewRating.objects.get(id=user_id)
    except ReviewRating.DoesNotExist:
        return redirect(next_url)

    product = data.product
    user = request.user
    ip = request.META.get('HTTP_REFERER')

    if request.method == 'POST':
        form = UpdateRevForm(request.POST, request.FILES, instance=data)

        if form.is_valid():
            img1 = request.FILES.get('img1')
            img2 = request.FILES.get('img2')
            img3 = request.FILES.get('img3')
            img4 = request.FILES.get('img4')
            img5 = request.FILES.get('img5')
            form.img1 = img1
            form.img2 = img2
            form.img3 = img3
            form.img4 = img4
            form.img5 = img5
            form.save()
            referer = next_url
            url_with_anchor = f"{referer}?scroll_to=comments"
            return redirect(url_with_anchor)


    else:
        form = UpdateRevForm(instance=data)

    return render(request, 'myapp/updaterev.html', {'form': form,'r':data})

def deleterev(request, user_id):
    data = ReviewRating.objects.get(id=user_id)
    data.delete()

    messages.info(request, "Your review has been deleted. Thank you.")

    # Get the URL of the previous page and append the anchor as a query parameter
    referer = request.META.get('HTTP_REFERER', '/')
    url_with_anchor = f"{referer}?scroll_to=comments"

    return redirect(url_with_anchor)

def submtreview(request, product_id):
    url = request.META.get('HTTP_REFERER')

    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.save(commit=False)
            uploaded_files = request.FILES.getlist('images')

            # Loop through the first 5 files and assign them to the corresponding fields
            for i in range(min(len(uploaded_files), 5)):
                field_name = f'img{i + 1}'
                setattr(data, field_name, uploaded_files[i])
            data.product_id = product_id
            data.user_id = request.user.id
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            messages.success(request, 'Thank you! Your review has been submitted.')
            referer = request.META.get('HTTP_REFERER', '/')
            url_with_anchor = f"{referer}?scroll_to=comments"
            return redirect(url_with_anchor)

def generatepdf(request,order_number=None,transID=None):
    if order_number and transID:
            order_number = order_number
            transID = transID

            try:
                order = Order.objects.get(order_number=order_number,is_ordered=True)
                ordered_products = OrderProduct.objects.filter(order_id=order.id)
                payment = Payment.objects.get(payment_id=transID)
                subtotal = 0
                for i in ordered_products:
                    subtotal += i.product_price * i.quantity
            except:
                pass



            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'filename=order_{order.order_number}.pdf'

            # Create a canvas to draw on the PDF
            p = canvas.Canvas(response, pagesize=letter)

            # Define page size
            width, height = letter

            # Add a header with a heading

            # Draw a black line below the heading spanning the full width
            p.setLineWidth(1)  # Set the line widthS
            p.setStrokeColorRGB(0, 0, 0)  # Set the line color to black
            p.line(0, height - 60, width, height - 60)  # Draw the line across the full width

            # Draw the text "Shop" in orange
            p.setFillColorRGB(255/255, 153/255, 0/255)
            p.setFont("Helvetica-Bold", 33)
            p.drawCentredString(256, 750, "Shop")

            # Draw the text "eum" in grey
            p.setFillColorRGB(128/255, 128/255, 128/255)
            p.setFont("Helvetica-Bold", 33)
            p.drawCentredString(330, 750, "eum")



            # p.drawInlineImage('static/myapp/images/Untitled.png', 130, 400)
            p.setFillColorRGB(0,0,0)
            p.setFont("Helvetica-Bold", 16)
            # Write order details to the PDF
            p.drawString(430, 700, f'Invoiced To')

            p.setFillColorRGB(64/255, 64/255, 64/255)


            p.setFont("Helvetica-Bold", 10)
            p.drawString(430, 680, f'Name:{order.first_name} {order.last_name}')
            p.drawString(430, 670, f'Address:{order.address_line_1} ')
            p.drawString(430, 660, f'City:{order.city},State:{order.state}')
            p.drawString(430, 650, f'Country:{order.country}')

            p.setFont("Helvetica-Bold", 13)
            p.drawString(40, 700, f'Order Number: {order.order_number}')
            p.drawString(40, 680, f'Transaction ID: {payment.payment_id}')

            order_date = order.created_at

            # Format the date as "Jan. 24, 2024, 9:34 p.m."
            formatted_date = order_date.strftime('%b. %d, %Y, %I:%M %p')

            # Draw the formatted date
            p.drawString(40, 660, f'Order Date: {formatted_date}')

            p.drawString(40, 640, f'Status: {payment.status}')

            # Add more details as needed

            # Draw a table for ordered products
            table_data = [['Product', 'Color & Size', 'Quantity', 'Price', 'Total']]

            for order_product in ordered_products:
                product_name = order_product.product.name
                variations = ', '.join([variation.variation_value for variation in order_product.variation.all()])
                quantity = str(order_product.quantity)
                price_per_unit = f'Rs {order_product.product_price}'
                total_price = f'{order_product.product_price * order_product.quantity} Rs'

                table_data.append([f'{product_name}', f'{variations}', quantity, price_per_unit, total_price])


            table = Table(table_data)
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                       ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                       ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                       ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                       ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                       ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                       ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                       ('FONTSIZE', (0, 0), (-1, -1), 12)]))

            table.wrapOn(p, width, height)
            table.drawOn(p, 30, 500)
            # p.showPage()
            # p.save()

            table_data = [['Sub Total', 'Tax', 'Grand Total']]

            table_data.append([
                        str(f'Rs {subtotal}'),
                        str(f'Rs {order.tax}'),
                        str(f'Rs {order.order_total}'),
            ])

            table = Table(table_data)
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                       ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                       ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                       ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                       ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                       ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                       ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                       ('FONTSIZE', (0, 0), (-1, -1), 12)]))

            table.wrapOn(p, width, height)
            table.drawOn(p, 373, 440)

            # Draw a black line below the heading spanning the full width
            line_position = height - 400  # Adjust this value to change the line position

            p.setLineWidth(1)  # Set the line width
            p.setStrokeColorRGB(0, 0, 0)  # Set the line color to black
            p.line(0, line_position, width, line_position)  # Draw the line across the full width


            p.setFillColorRGB(64/255, 64/255, 64/255)  # Dark grey color
            p.setFont("Helvetica-Bold", 20)
            p.drawCentredString(300, 360, "Thank you for shopping with us.")

            p.showPage()
            p.save()
            return response


def order_completed(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number,is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        payment = Payment.objects.get(payment_id=transID)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product.sprice * i.quantity


        context = {
           'order':order,
           'ordered_products':ordered_products,
           'order_number':order.order_number,
           'transID':payment.payment_id,
           'payment':payment,
           'sub_total':subtotal,
           'order_number':order_number,
           'transID':transID,
        }
        return render(request,'myapp/order_complete.html',context)
    except (Payment.DoesNotExist,Order.DoesNotExist):
        return redirect('Home')




def payments(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            # Get the order
            order = get_object_or_404(Order, user=request.user, is_ordered=False, order_number=body['orderID'])

            # Create Payment instance
            payment = Payment.objects.create(
                user=request.user,
                payment_id=body['transID'],
                payment_method=body['payment_method'],
                amount_paid=order.order_total,
                status=body['status'],
            )

            # Update the order
            order.payment = payment
            order.is_ordered = True
            order.save()

            # Move items from cart to OrderProduct
            cart_items = CartItems.objects.filter(user=request.user)
            for item in cart_items:
                orderproduct = OrderProduct.objects.create(
                    order_id=order.id,
                    payment=payment,
                    user=request.user,
                    product=item.product,
                    quantity=item.quantity,
                    product_price=item.product.sprice,
                    ordered=True,
                )
                orderproduct.variation.set(item.variation.all())
                orderproduct.save()

                # Reduce product stock
                item.product.stock -= item.quantity
                item.product.save()

            # Clear the cart
            cart_items.delete()

            # Send order confirmation email
            mail_subject = 'Thank you for your order!'
            message = render_to_string('myapp/order_received.html', {'user': request.user, 'order': order,'payment':payment})
            to_email = request.user.email
            email = EmailMultiAlternatives(mail_subject, message, to=[to_email])
            email.attach_alternative(message, "text/html")
            email.send()

            # Respond with order details
            return JsonResponse({'order_number': order.order_number, 'transID': payment.payment_id})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def order(request,total=0, quantity=0):
    user = request.user
    #if cart item not found redirect to shop
    cart_items = CartItems.objects.filter(user=user)
    cart_count = cart_items.count()
    if cart_count <=0:
        return redirect('Store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.sprice * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total)/100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            #Generate Order Number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            currentdate = d.strftime("%Y%m%d")
            order_number = currentdate + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=user,is_ordered=False,order_number=order_number)
            context = {
            'order':order,
            'cart_items':cart_items,
            'total':total,
            'tax':tax,
            'grand_total':grand_total
            }
            return render(request,'myapp/payments.html',context)
    else:
        return redirect('Checkout')



@login_required(login_url='Login')
def logout(request):
    auth.logout(request)
    messages.info(request,'You are logged out')
    return redirect('Login')

def home(request):
    # Filter products for the specified categories
    men_bottom_wear_category = "men-bottom-wear"  # Replace with the slug or identifier of the category
    women_top_wear_category = "women-top-wear"  # Replace with the slug or identifier for women top wear

    men_bottom_wear_products = Product.objects.filter(
        is_available=True,
        category__slug=men_bottom_wear_category
    )

    # Get the last 4 added products in the "women-top-wear" category
    women_top_wear_products = Product.objects.filter(
        is_available=True,
        category__slug=women_top_wear_category
    ).order_by('-created_at')[:4]  # Limit to 4 latest products

    # Get general products and latest products
    products = Product.objects.filter(is_available=True)[:8]
    latest_products = Product.objects.filter(is_available=True).order_by('-created_at')[:4]

    # Calculate discounts for general products
    product_discounts = []
    for product in products:
        original_price = product.price
        selling_price = product.sprice

        def calculate_percentage_discount(original_price, selling_price):
            if original_price == 0:
                return 0  # Handle the case where the original price is zero to avoid division by zero

            percentage_discount = ((original_price - selling_price) / original_price) * 100
            return round(percentage_discount, 2)  # Round to two decimal places

        percentage_discount = round(calculate_percentage_discount(original_price, selling_price))
        product_discounts.append((product, percentage_discount))

    # Calculate discounts for latest products
    latest_product_discounts = []
    for product in latest_products:
        original_price = product.price
        selling_price = product.sprice

        def calculate_percentage_discount(original_price, selling_price):
            if original_price == 0:
                return 0  # Handle the case where the original price is zero to avoid division by zero

            percentage_discount = ((original_price - selling_price) / original_price) * 100
            return round(percentage_discount, 2)  # Round to two decimal places

        percentage_discount = round(calculate_percentage_discount(original_price, selling_price))
        latest_product_discounts.append((product, percentage_discount))

    # Calculate discounts for category-specific products (men-bottom-wear)
    men_bottom_wear_discounts = []
    for product in men_bottom_wear_products:
        original_price = product.price
        selling_price = product.sprice

        def calculate_percentage_discount(original_price, selling_price):
            if original_price == 0:
                return 0  # Handle the case where the original price is zero to avoid division by zero

            percentage_discount = ((original_price - selling_price) / original_price) * 100
            return round(percentage_discount, 2)  # Round to two decimal places

        percentage_discount = round(calculate_percentage_discount(original_price, selling_price))
        men_bottom_wear_discounts.append((product, percentage_discount))

    # Calculate discounts for category-specific products (women-top-wear)
    women_top_wear_discounts = []
    for product in women_top_wear_products:
        original_price = product.price
        selling_price = product.sprice

        def calculate_percentage_discount(original_price, selling_price):
            if original_price == 0:
                return 0  # Handle the case where the original price is zero to avoid division by zero

            percentage_discount = ((original_price - selling_price) / original_price) * 100
            return round(percentage_discount, 2)  # Round to two decimal places

        percentage_discount = round(calculate_percentage_discount(original_price, selling_price))
        women_top_wear_discounts.append((product, percentage_discount))

    context = {
        'product_discounts': product_discounts,
        'latest_product_discounts': latest_product_discounts,
        'men_bottom_wear_discounts': men_bottom_wear_discounts,
        'women_top_wear_discounts': women_top_wear_discounts,  # Pass the last 4 added women-top-wear products with discounts
    }
    return render(request, 'myapp/index.html', context)





def store(request, category_slug=None):
    size = request.GET.get('size')
    price = request.GET.get('price')
    price2 = request.GET.get('price2')

    if category_slug is not None:
        cat = get_object_or_404(category, slug=category_slug)
        data = Product.objects.filter(category=cat, is_available=True).order_by('id')
    else:
        data = Product.objects.filter(is_available=True).order_by('-created_at')

    # Apply size filter
    if size:
        data = data.filter(variation__variation_value=size)

    # Apply price filter
    if price is not None and price2 is not None:
        data = data.filter(sprice__gte=price, sprice__lte=price2)

    paginator = Paginator(data, 10)
    page = request.GET.get('page')
    page_products = paginator.get_page(page)
    data1 = data.count()

    context = {'data': page_products, 'data1': data1}
    return render(request, 'myapp/store.html', context)

def product_detail(request,category_slug,product_slug):
    try:
        data = Product.objects.get(category__slug=category_slug,slug=product_slug)
        in_cart = CartItems.objects.filter(cart__cart_id=_cart_id(request),product=data).exists()
    except Exception as e:
        raise e
    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user,product_id=data.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None


    reviews = ReviewRating.objects.filter(product_id=data.id,status=True).order_by('-created_at')
    average_rating = ReviewRating.objects.filter(product_id=data.id,status=True).aggregate(Avg('rating'))['rating__avg']
    original_price = data.price
    selling_price = data.sprice

    def calculate_percentage_discount(original_price, selling_price):
        if original_price == 0:
            return 0  # Handle the case where the original price is zero to avoid division by zero

        percentage_discount = ((original_price - selling_price) / original_price) * 100
        return round(percentage_discount, 2)  # Round to two decimal places

    percentage_discount = calculate_percentage_discount(original_price, selling_price)
    product_gallery = ProductGallery.objects.filter(product_id=data.id)
    aval_offer = AvailableOffers.objects.filter(prod_id=data)
    context = {
    'data':data,
    'in_cart':in_cart,
    'orderproduct':orderproduct,
    'reviews':reviews,
    'product_gallery':product_gallery,
    'average_rating':average_rating,
    'percentage_discount':percentage_discount,
    'aval_offer':aval_offer
    }
    return render(request,'myapp/product-detail.html',context)



def add_cart(request,product_id):
    current_user = request.user
    data = Product.objects.get(pk=product_id)
    if current_user.is_authenticated:
        list1 = []
        if request.method == 'POST':
            for key,value in request.POST.items():
                try:
                    prod = Variation.objects.get(product=data,variation_cat__iexact=key,variation_value__iexact=value)
                    list1.append(prod)
                except:
                    pass



        is_cart_item_exists = CartItems.objects.filter(product=data,user=current_user).exists()
        if is_cart_item_exists:
            cart_items = CartItems.objects.filter(product=data,user=current_user)
            ex_var_list = []
            id = []
            for item in cart_items:
                existing_variation = item.variation.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)


            if list1 in ex_var_list:
                index = ex_var_list.index(list1)
                item_id = id[index]
                item = CartItems.objects.get(product=data,id=item_id)
                item.quantity +=1
                item.save()


            else:
                item = CartItems.objects.create(product=data, quantity=1, user=current_user)
                if len(list1) > 0:
                    item.variation.clear()
                    item.variation.add(*list1)
                item.save()



        else:
            cart_items = CartItems.objects.create(
            product = data,
            quantity = 1,
            user = current_user,
            )
            if len(list1) > 0:
                cart_items.variation.clear()
                # cart_items.variation.add(*list1)
                for item in list1:
                    cart_items.variation.add(item)
            cart_items.save()
        return redirect('/cart/')

    else:

        list1 = []
        if request.method == 'POST':
            for key,value in request.POST.items():
                try:
                    prod = Variation.objects.get(product=data,variation_cat__iexact=key,variation_value__iexact=value)
                    list1.append(prod)
                except:
                    pass
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
            cart_id = _cart_id(request)
            )
        cart.save()


        is_cart_item_exists = CartItems.objects.filter(product=data,cart=cart).exists()
        if is_cart_item_exists:
            cart_items = CartItems.objects.filter(product=data,cart=cart)
            ex_var_list = []
            id = []
            for item in cart_items:
                existing_variation = item.variation.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)
            if list1 in ex_var_list:
                index = ex_var_list.index(list1)
                item_id = id[index]
                item = CartItems.objects.get(product=data,id=item_id)
                item.quantity +=1
                item.save()
            else:
                item = CartItems.objects.create(product=data, quantity=1, cart=cart)
                if len(list1) > 0:
                    item.variation.clear()
                    item.variation.add(*list1)
                item.save()
        else:
            cart_items = CartItems.objects.create(
            product = data,
            quantity = 1,
            cart = cart,
            )
            if len(list1) > 0:
                cart_items.variation.clear()
                for item in list1:
                    cart_items.variation.add(item)
            cart_items.save()
        return redirect('/cart/')


def remove_cart(request,product_id,cart_item):
    product = get_object_or_404(Product,id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItems.objects.get(product=product,user=request.user,id=cart_item)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItems.objects.get(product=product,cart=cart,id=cart_item)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('/cart/')



def remove_cart_item(request,product_id,cart_item):
    product = get_object_or_404(Product,id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItems.objects.get(product=product,user=request.user,id=cart_item)

    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItems.objects.get(product=product,cart=cart,id=cart_item)
    cart_item.delete()
    return redirect('/cart/')



def cart(request,total=0,quantity=0,cart_items=None):
    try:
        tax= 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItems.objects.filter(user=request.user,is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItems.objects.filter(cart=cart,is_active=True)
        for cart_item in cart_items:
            total+= (cart_item.product.sprice*cart_item.quantity)
            quantity+=cart_item.quantity
        tax = (2*total)/100
        grand_total = total+tax
    except ObjectDoesNotExist:
        pass
    context = {
    'total':total,
    'quantity':quantity,
    'cart_items':cart_items,
    'tax':tax,
    'grand_total':grand_total
    }
    return render(request,'myapp/cart.html',context)

def search(request):
    data = None
    data1=0
    if 'keyword' in request.GET:
        key = request.GET['keyword']
        if key:
            data = Product.objects.order_by('-created_at').filter(description__icontains=key) | Product.objects.filter(name__icontains=key)
            data1 = data.count()


    context = {'data': data,'data1':data1,'key':key}
    return render(request, 'myapp/store.html', context)





@login_required(login_url='Login')
def dashboard(request):
    # Fetch orders by the logged-in user
    orders = Order.objects.order_by('-created_at').filter(user=request.user, is_ordered=True)
    orders_count = orders.count()

    try:
        # Fetch user profile using the logged-in user (no need for user_id directly)
        userprofile = Account.objects.get(email=request.user)
    except Account.DoesNotExist:
        userprofile = None
    print(request.user)
    context = {
        'orders_count': orders_count,
        'userprofile': userprofile
    }

    return render(request, 'myapp/dashboard.html', context)


@login_required(login_url='Login')
def checkout(request, total=0, quantity=0, cart_items=None):
    # Initialize variables to avoid UnboundLocalError
    user_profile = None
    account = None

    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItems.objects.filter(user=request.user, is_active=True)
            # Retrieve the user's profile and account details
            user_profile = Account.objects.get(email=request.user.email)  # Assuming Account model has email field
            account = request.user  # The 'user' instance is linked with the Account model
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItems.objects.filter(cart=cart, is_active=True)

        # Calculate the total and quantity for cart items
        for cart_item in cart_items:
            total += (cart_item.product.sprice * cart_item.quantity)
            quantity += cart_item.quantity

        # Calculate tax (example: 2% tax)
        tax = (2 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        # Handle cases where user or cart does not exist
        pass

    # Prepare context with all the necessary data, including user profile details
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'user_profile': user_profile,
        'account': account,
        'first_name': user_profile.first_name if user_profile else '',
        'last_name': user_profile.last_name if user_profile else '',
        'phone_number': user_profile.phone_number if user_profile else '',
        'address_line_1': user_profile.address_line_1 if user_profile else '',
        'address_line_2': user_profile.address_line_2 if user_profile else '',
        'city': user_profile.city if user_profile else '',
        'state': user_profile.state if user_profile else '',
        'country': user_profile.country if user_profile else '',
    }

    return render(request, 'myapp/checkout.html', context)



def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def my_order(request):
    orders = Order.objects.filter(user=request.user,is_ordered=True).order_by('-created_at')
    context = {
    'orders':orders
    }
    return render(request,'myapp/my_order.html',context)


@login_required
def editprofile(request):
    if request.method == 'POST':
        # Get the current user instance
        user = request.user

        # Manually get data from request.POST (text inputs)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        address_line_1 = request.POST.get('address_line_1')
        address_line_2 = request.POST.get('address_line_2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')

        # Handle image upload from request.FILES (if there is a new image)
        img = request.FILES.get('img')

        # Update the user's attributes manually
        user.first_name = first_name
        user.last_name = last_name
        user.phone_number = phone
        user.address_line_1 = address_line_1
        user.address_line_2 = address_line_2
        user.city = city
        user.state = state
        user.country = country

        # If an image was uploaded, update the image field
        if img:
            user.img = img

        try:
            user.full_clean()  # Optional: Perform full model validation
        except ValidationError as e:
            # Handle validation errors and display them in a message
            messages.error(request, f"Error in saving profile: {', '.join(e.messages)}")
            return redirect('editprofile')  # Redirect back to the edit profile page

        # Save the updated user instance to the database
        user.save()

        # Show success message
        messages.success(request, 'Your profile has been updated successfully.')

        # Redirect to the profile edit page (or another page of your choice)
        return redirect('EditProfile')

    else:
        # If GET request, render the form with the current user's data pre-filled
        return render(request, 'myapp/editprofile.html', {'user': request.user})





def orderdetails(request,order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    payment = order_detail.first().payment if order_detail.exists() else None
    subtotal = 0
    for i in order_detail:
        subtotal += i.product.sprice * i.quantity

    context = {
    'order_detail':order_detail,
    'order':order,
    'subtotal': subtotal,
    'payment':payment
    }


    return render(request,'myapp/orderdetails.html',context)



#OTP
import random
from django.core.mail import send_mail

def generate_otp():
    return random.randint(100000, 999999)


from django.utils.html import strip_tags

from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

def send_otp(email, otp):
    subject = 'Your OTP Code - Shopium'
    # HTML email content with logo and additional details
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 20px auto; background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h2 style="color: #333333; text-align: center;">Your OTP Code</h2>
            <p style="color: #555555; text-align: center; font-size: 16px; line-height: 1.6;">
                Dear User,<br><br>
                Thank you for using Shopium! Your OTP code is:
            </p>
            <h3 style="text-align: center; color: #ff9017; font-size: 24px; margin: 10px 0;">{otp}</h3>
            <p style="color: #555555; text-align: center; font-size: 14px; line-height: 1.6;">
                Please enter this code to verify your identity. The OTP is valid for 10 minutes.
            </p>
            <hr style="border: none; border-top: 1px solid #dddddd; margin: 20px 0;">
            <p style="color: #555555; text-align: center; font-size: 14px; line-height: 1.6;">
                If you have any issues or need further assistance, feel free to contact our support team:
            </p>
            <p style="text-align: center; font-size: 14px;">
                <strong>Developer Details:</strong><br>
                Name: Rudra Narayan Tiwari<br>
                LinkedIn: <a href="https://linkedin.com/in/rrnntt" style="color: #ff9017;">linkedin.com/in/rrnntt</a><br>
                Email: <a href="mailto:webdevrnt@gmail.com" style="color: #ff9017;">webdevrnt@gmail.com</a><br>
                Phone: +91 7905817391
            </p>
            <div style="text-align: center; margin-top: 20px;">
                <a href="https://yourwebsite.com" style="display: inline-block; padding: 10px 20px; background-color: #ff9017; color: #ffffff; text-decoration: none; border-radius: 5px;">Visit Shopium</a>
            </div>
            <p style="text-align: center; font-size: 12px; color: #999999; margin-top: 20px;">
                © 2024 Shopium. All rights reserved.
            </p>
        </div>
    </body>
    </html>
    """

    # Plain text fallback for email clients that don't support HTML
    plain_message = strip_tags(html_content)

    # Creating the email
    email_from = 'webdevrnt@gmail.com'  # Replace with your email
    msg = EmailMultiAlternatives(subject, plain_message, email_from, [email])
    msg.attach_alternative(html_content, "text/html")

    # Send the email
    msg.send()





def email_login_or_signup(request):
    # Step 1: Ask for email and send OTP
    if 'otp_verified' not in request.session:  # OTP not yet verified
        if request.method == 'POST':
            form = EmailLoginForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                request.session['email'] = email  # Store email in session for later use

                # Check if user exists
                if Account.objects.filter(email=email).exists():
                    request.session['existing_user'] = True  # Mark as existing user
                else:
                    request.session['existing_user'] = False  # Mark as new user

                # Generate and send OTP
                otp = generate_otp()
                request.session['otp'] = otp  # Store OTP in session for verification
                send_otp(email, otp)  # Send OTP to the provided email

                return redirect('verify_otp')  # Redirect to OTP verification page
        else:
            form = EmailLoginForm()

        return render(request, 'myapp/login.html', {'form': form})

    else:
        # Step 2: After OTP verification, handle the next steps (user creation or login)
        return redirect('verify_otp')  # Redirect to OTP verification page if OTP already sent


def verify_otp(request):
    if request.method == 'POST':
        otp_form = OTPForm(request.POST)
        if otp_form.is_valid():
            input_otp = otp_form.cleaned_data['otp']
            session_otp = request.session.get('otp')

            if session_otp is None:
                return redirect('email_login')

            if input_otp == str(session_otp):
                # OTP is correct, set session flag and redirect
                request.session['otp_verified'] = True

                # Clean unnecessary session data
                del request.session['otp']

                email = request.session.get('email', '')

                # For existing users, log them in
                if request.session.get('existing_user'):
                    try:
                        user = Account.objects.get(email=email)
                        login(request, user)  # Log the user in

                        # Clean session data
                        del request.session['otp_verified']
                        del request.session['existing_user']

                        # Redirect to home page after successful login
                        return redirect('Home')
                    except Account.DoesNotExist:  # Fixed 'User' to 'Account'
                        messages.error(request, "User does not exist.")
                        return redirect('email_login')
                else:
                    # For new user, create a user with blank values for profile fields
                    first_name = ""  # Blank first name
                    last_name = ""    # Blank last name

                    user = Account.objects.create_user(
                        email=email,
                        first_name=first_name,  # Blank first name
                        last_name=last_name,    # Blank last name
                    )
                    user.is_active = True  # Set the user as active
                    user.save()  # Save the new user

                    # Log the new user in
                    login(request, user)

                    # Redirect to home page after successful registration
                    return redirect('Home')
            else:
                # Invalid OTP, retry OTP verification
                messages.error(request, 'Invalid OTP, please try again.')
                return redirect('verify_otp')

    else:
        otp_form = OTPForm()

    # Display the OTP verification form
    email = request.session.get('email', '')  # Get email from session if available
    return render(request, 'myapp/verifyotp.html', {'form': otp_form, 'email': email})


def socialmedia(request):
    return render(request,'myapp/socialmedia.html')
