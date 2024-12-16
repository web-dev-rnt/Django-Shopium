from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings



urlpatterns = [

    path('',views.home,name='Home'),
    path('store/',views.store,name='Store'),
    path('store/category/<slug:category_slug>/',views.store,name='products_by_category'),
    path('store/category/<slug:category_slug>/<slug:product_slug>/',views.product_detail,name='product_detail'),
    path('cart/',views.cart,name='Cart'),
    path('addcart/<int:product_id>/',views.add_cart,name='AddCart'),
    path('remove_cart/<int:product_id>/<int:cart_item>/',views.remove_cart,name='RemoveCart'),
    path('remove_cart_item/<int:product_id>/<int:cart_item>/',views.remove_cart_item,name='RemoveCartItem'),
    path('store/search/',views.search,name='Search'),
    path('accounts/login/',views.email_login_or_signup,name='Login'),
    path('accounts/logout/',views.logout,name='Logout'),
    path('dashboard/',views.dashboard,name='Dashboard'),
    path('checkout/',views.checkout,name='Checkout'),

    #OTP Login
    # path('emaillogin/',views.email_login_or_signup,name='email_login'),
    path('emailverification/',views.verify_otp,name='verify_otp'),


    #Orders
    path('orders/',views.order,name='Order'),
    path('payments/',views.payments,name='Payment'),
    path('order_completed/',views.order_completed,name='OrderComplete'),
    path('submit_review/<int:product_id>/',views.submtreview,name='SubmtReview'),
    path('myorders/',views.my_order,name='MyOrder'),
    path('edit_profile/',views.editprofile,name='EditProfile'),
    path('orderdetails/<int:order_id>/',views.orderdetails,name='OrderDetail'),

    path('deletereview/<int:user_id>/',views.deleterev,name='DeleteRev'),
    path('updaterev/<int:user_id>/',views.updaterev,name='UpdateRev'),

    path('contact/',views.contact,name='Contact'),
    path('generate-pdf/<str:order_number>/<str:transID>/',views.generatepdf, name='GenPdf'),
    path('generate-pdf/<str:order_number>/',views.generatepdf, name='GenPdf'),

    #Social media links update
    path('socialmedia/',views.socialmedia,name='Socialmedia'),


]+ static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
