from django.urls import path, re_path

from . import views

app_name = "verifications"

urlpatterns = [
    #re_path(r'^image_codes/(?P<image_code_id>[\w-]+)/$', view=views.ImageCodeView.as_view(), name="image_code"),
    # image_code_id为uuid格式
    path('image_codes/<uuid:image_code_id>/', views.ImageCode.as_view(), name='image_code'),
    re_path('usernames/(?P<username>\w{5,20})/', views.CheckUsernameView.as_view(), name='check_username'),
    re_path('mobiles/(?P<mobile>1[3-9]\d{9})/', views.CheckMobileView.as_view(), name='check_mobiles'),
    path('sms_codes/<int:route_id>/',views.SmsCodesView.as_view(),name='sms_codes'),
    path('password/',views.PasswordVerifyView.as_view(),name='password_verify')
]