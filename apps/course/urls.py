from django.urls import path
from . import views
# app的名字
app_name = 'course'
urlpatterns = [
    #path('course',views.course,name='course'),
    #path('course_detail',views.course_detail,name='course_detail'),
    path('', views.course_list, name='index'),
    path('<int:course_id>/', views.CourseDetailView.as_view(), name='course_detail'),
]