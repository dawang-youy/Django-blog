from django.urls import path
from . import views
from django.views import View
from utils.decorators.user_decorators import my_decorator
from django.utils.decorators import method_decorator
# app的名字
app_name = 'admin'

# @method_decorator(my_decorator)
# def as_view(cls, **initkwargs):
#     return super().as_view(cls, **initkwargs)
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),  # 将这条路由命名为index
    path('tags/', views.TagsManageView.as_view(), name='tags'),
    path('index/',views.index_fn,name='index_fn'),
    path('tags/<int:tag_id>/', views.TagEditView.as_view(), name='tag_edit'),

    path('news/', views.NewsManageView.as_view(), name='news_manage'),
    path('news/<int:news_id>/', views.NewsEditView.as_view(), name='news_edit'),
    path('news/pub/', views.NewsPubView.as_view(), name='news_pub'),
    path('news/images/', views.NewsUploadImage.as_view(), name='upload_image'),
    path('token/', views.UploadToken.as_view(), name='upload_token'),  # 七牛云上传图片需要调用token

    path('hotnews/', views.HotNewsManageView.as_view(), name='hotnews_manage'),
    path('hotnews/<int:hotnews_id>/', views.HotNewsEditView.as_view(), name='hotnews_edit'),
    path('hotnews/add/', views.HotNewsAddView.as_view(), name='hotnews_add'),
    path('tags/<int:tag_id>/news/', views.NewsByTagIdView.as_view(), name='news_by_tagid'),

    path('banners/', views.BannerManageView.as_view(), name='banners_manage'),
    path('banners/<int:banner_id>/', views.BannerEditView.as_view(), name='banners_edit'),
    path('banners/add/', views.BannerAddView.as_view(), name='banners_add'),

    path('docs/', views.DocsManageView.as_view(), name='docs_manage'),
    path('docs/<int:doc_id>/', views.DocsEditView.as_view(), name='docs_edit'),
    path('docs/pub/', views.DocsPubView.as_view(), name='docs_pub'),
    path('docs/files/', views.DocsUploadFile.as_view(), name='upload_text'),

    path('courses/', views.CoursesManageView.as_view(), name='courses_manage'),
    path('courses/<int:course_id>/', views.CoursesEditView.as_view(), name='courses_edit'),
    path('courses/pub/', views.CoursesPubView.as_view(), name='courses_pub'),

    path('groups/', views.GroupsManageView.as_view(), name='groups_manage'),
    path('groups/<int:group_id>/', views.GroupsEditView.as_view(), name='groups_edit'),
    path('groups/add/', views.GroupsAddView.as_view(), name='groups_add'),

    path('users/', views.UsersManageView.as_view(), name='users_manage'),
    path('users/<int:user_id>/', views.UsersEditView.as_view(), name='users_edit'),

    path('usersprofile/', views.UserProfileManageView.as_view(), name='usersprofile_manage'),
    path('usersprofile/<int:user_id>/', views.UsersProfileEditView.as_view(), name='usersprofile_edit'),

]