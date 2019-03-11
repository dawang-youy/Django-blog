import json
import logging
from datetime import datetime
import qiniu
from collections import OrderedDict
from django.shortcuts import render
from django.http import HttpResponse,JsonResponse,Http404
from django.views import View
from django.contrib.auth.models import Group,Permission
from django.db.models import Count
from django.contrib.auth.mixins import PermissionRequiredMixin,LoginRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator,EmptyPage
from django.utils.http import urlencode

from . import forms
from news import models
from doc.models import Doc
from users.models import Users,UsersProfile
from course.models import Course,Teacher,CourseCategory
from utils.json_fun import to_json_data
from utils.res_code import Code, error_map
from . import constants
from utils import paginator_script
from utils.secrets import qiniu_secret_info
from news.constants import SHOW_HOTNEWS_COUNT

logger = logging.getLogger('django')
# Create your views here.

#@my_decorator
#@method_decorator(my_decorator,name='dispatch')# 只是对dispatch方法装饰 get等方法 都被装饰
class IndexView(LoginRequiredMixin,View):
    """
    create admin index view
    route:'/admin/'
    """
    login_url = 'users:login'#推荐这种写法 可以settings 里面指定
    #login_url = '/users/login/'#这种写法不推荐
    redirect_field_name = 'next'

    # @method_decorator(my_decorator)
    # def dispatch(self, request, *args, **kwargs):
    #     return super().dispatch(request,*args,**kwargs)

    # @my_decorator
    #@method_decorator(my_decorator)
    def get(self, request):
        return render(request, 'admin/index/index.html')

#IndexView = my_decorator(IndexView)
#get = my_decorator(get)

class TagsManageView(PermissionRequiredMixin,View):
    """
    tags manage view
    """
    permission_required = ('news.add_tag','news.view_tag')
    #permission_required = ([])
    raise_exception = True
    permission_denied_message = "没有权限访问标签页"
    # def get_permission_required(self):
    #     content_type = ContentType.objects.get_for_model(models.Tag)
    #     permissions = Permission.objects.filter(content_type=content_type)
    #     print(1,permissions)
    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(TagsManageView, self).handle_no_permission()
    def get(self, request):
        """
        get news tags
        route:'/admin/tags'
        """
        tags = models.Tag.objects.values('id', 'name').annotate(num_news=Count('news')). \
            filter(is_delete=False).order_by('-num_news')
        return render(request, 'admin/news/tags_manage.html', locals())

    def post(self, request):
        """
        create new news tags
        add tags name
        route:'/admin/tags/'
        """
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        tag_name = dict_data.get('name')
        if tag_name and tag_name.strip():
            tag_tuple = models.Tag.objects.get_or_create(name=tag_name)
            #print(tag_tuple)
            #tag = models.Tag.objects.only('name').filter(name=tag_name).first()
            if tag_tuple[0]:
                tag_tuple[0].is_delete = False
                tag_tuple[0].save(update_fields=['is_delete'])  # 优化措施 同 only
                #return to_json_data(errmsg="标签添加成功")
            #return to_json_data(errmsg="标签创建成功")
            return to_json_data(errmsg="标签创建成功") if tag_tuple[-1] else \
                to_json_data(errno=Code.DATAEXIST, errmsg="标签名已存在")
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="标签名为空")


# class Test(PermissionRequiredMixin,View):
#     """
#
#     """
#     permission_required = ('news.change_tag','news.delete_tag')
#     raise_exception = True
#     def handle_no_permission(self):
#         return to_json_data()
#     def get(self,request):
#         return to_json_data()

class TagEditView(PermissionRequiredMixin, View):
    """
    edit news tags
        update and delete tags
        route:'/admin/tags/<int:tag_id>/'
    """
    permission_required = ('news.change_tag', 'news.delete_tag')
    raise_exception = True

    def handle_no_permission(self):
        return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
    def put(self, request, tag_id):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))
        tag_name = dict_data.get('name')
        tag = models.Tag.objects.only('id').filter(id=tag_id).first()
        if tag:
            if tag_name and tag_name.strip():
                if not models.Tag.objects.only('id').filter(name=tag_name).exists():
                    tag.name = tag_name
                    tag.save(update_fields=['name'])
                    return to_json_data(errmsg="标签更新成功")
                else:
                    return to_json_data(errno=Code.DATAEXIST, errmsg="标签名已存在")
            else:
                return to_json_data(errno=Code.PARAMERR, errmsg="标签名为空")

        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要更新的标签不存在")

    def delete(self, request, tag_id):
        tag = models.Tag.objects.only('id').filter(id=tag_id).first()
        if tag:
            # 真删
            # tag.delete()
            tag.is_delete = True
            tag.save(update_fields=['is_delete'])# 优化措施 同 only
            return to_json_data(errmsg="标签删除成功")
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要删除的标签不存在")
#@my_decorator
# 写法同 index_fn = my_decorator(index_fn)
#@login_required(login_url='users:register')
@permission_required('news.delete_news',raise_exception=True)
def index_fn(request):
    return HttpResponse('大家是未来的python大牛！')
#index_fn = my_decorator(index_fn)


class NewsManageView(PermissionRequiredMixin, View):
    """
    create news manage view
    route:/admin/news/
    """
    permission_required = ('news.add_news', 'news.view_news')
    raise_exception = True

    def get(self, request):
        #1、获取文章标签
        #2、获取前端参数
        #3、通过条件过滤，去数据库中查询
        #4、分页操作
        #5、模板渲染
        tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)
        #tags = tags.filter()#这次查询--惰性操作 不会去数据库查询 orm 性能强大 链式操作--优化机制
        #tags.filter() #缓存到内存
        newses = models.News.objects.only('id', 'title', 'author__username', 'tag__name', 'update_time').\
            select_related('author', 'tag').filter(is_delete=False)

        # 通过时间进行过滤
        try:
            start_time = request.GET.get('start_time', '')
            #datetime.strftime()#时间转字符串
            start_time = datetime.strptime(start_time, '%Y/%m/%d') if start_time else ''

            end_time = request.GET.get('end_time', '')
            end_time = datetime.strptime(end_time, '%Y/%m/%d') if end_time else ''
        except Exception as e:
            logger.info("用户输入的时间有误：\n{}".format(e))
            start_time = end_time = ''

        if start_time and not end_time:
            newses = newses.filter(update_time__gte=start_time)
        if end_time and not start_time:
            newses = newses.filter(update_time__lte=end_time)

        if start_time and end_time:
            newses = newses.filter(update_time__range=(start_time, end_time))

        # 通过title进行过滤
        title = request.GET.get('title', '')
        if title:
            newses = newses.filter(title__icontains=title)#模糊查询%link i 忽略大小写

        # 通过作者名进行过滤
        author_name = request.GET.get('author_name', '')
        if author_name:
            newses = newses.filter(author__username__icontains=author_name)

        # 通过标签id进行过滤
        try:
            tag_id = int(request.GET.get('tag_id', 0))
        except Exception as e:
            logger.info("标签错误：\n{}".format(e))
            tag_id = 0
        newses = newses.filter(is_delete=False, tag_id=tag_id) or \
               newses.filter(is_delete=False)

        # 获取第几页内容
        try:
            page = int(request.GET.get('page', 1))
        except Exception as e:
            logger.info("当前页数错误：\n{}".format(e))
            page = 1
        paginator = Paginator(newses, constants.PER_PAGE_NEWS_COUNT)
        try:
            news_info = paginator.page(page)
        except EmptyPage:
            # 若用户访问的页数大于实际页数，则返回最后一页数据
            logging.info("用户访问的页数大于总页数。")
            news_info = paginator.page(paginator.num_pages)

        paginator_data = paginator_script.get_paginator_data(paginator, news_info)

        start_time = start_time.strftime('%Y/%m/%d') if start_time else ''
        end_time = end_time.strftime('%Y/%m/%d') if end_time else ''
        context = {
            'news_info': news_info,
            'tags': tags,
            'paginator': paginator,
            'start_time': start_time,
            "end_time": end_time,
            "title": title,
            "author_name": author_name,
            "tag_id": tag_id,
            "other_param": urlencode({
                "start_time": start_time,
                "end_time": end_time,
                "title": title,
                "author_name": author_name,
                "tag_id": tag_id,
            })
        }
        #print(type(news_info),dir(news_info))
        #print(news_info.has_previous(),news_info.has_next())
        context.update(paginator_data)
        #print(news_info)
        return render(request, 'admin/news/news_manage.html', context=context)


class NewsEditView(PermissionRequiredMixin, View):
    """
    create news edit view
    route:/admin/news/<int:news_id>/
    """
    permission_required = ('news.change_news', 'news.delete_news')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(NewsEditView, self).handle_no_permission()

    def get(self, request,news_id):
        news = models.News.objects.only('id','title','digest','tag','content').filter(id=news_id).first()
        if news:
            tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)
            context = {
                'tags':tags,
                'news':news
            }
            return render(request, 'admin/news/news_pub.html', context=context)
        else:
            raise Http404('需要更新的文章不存在！')
    def delete(self, request, news_id):
        """
        删除文章
        """
        news = models.News.objects.only('id').filter(id=news_id).first()
        if news:
            news.is_delete = True
            news.save(update_fields=['is_delete'])
            return to_json_data(errmsg="文章删除成功")
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要删除的文章不存在")

    def put(self, request, news_id):
        """
        更新文章
        """
        news = models.News.objects.filter(is_delete=False, id=news_id).first()
        if not news:
            return to_json_data(errno=Code.NODATA, errmsg='需要更新的文章不存在')

        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        form = forms.NewsPubForm(data=dict_data)
        if form.is_valid():
            news.title = form.cleaned_data.get('title')
            news.digest = form.cleaned_data.get('digest')
            news.content = form.cleaned_data.get('content')
            news.image_url = form.cleaned_data.get('image_url')
            news.tag = form.cleaned_data.get('tag')
            news.save()
            return to_json_data(errmsg='文章更新成功')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串

            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)


class NewsPubView(PermissionRequiredMixin, View):
    """
    public news view
    route:/admin/news/pub/
    """
    permission_required = ('news.add_news', 'news.view_news')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(NewsPubView, self).handle_no_permission()
    def get(self, request):
        """
        获取文章标签
        """
        tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)

        return render(request, 'admin/news/news_pub.html', locals())

    def post(self, request):
        """
        新增文章
        """
        #1、从前端获取参数
        #2、校验
        #3、保存到数据库
        #4、返回执行结果
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        form = forms.NewsPubForm(data=dict_data)
        if form.is_valid():
            #3.
            # n = models.News(title=form.cleaned_data.get('title'))
            # n = models.News(**form.cleaned_data)#字典拆包
            # n.title = form.cleaned_data.get('title')
            # n.save()
            # news_instance = form.save()
            news_instance = form.save(commit=False)#默认commit为true save直接存入mysql当中 false不会
            news_instance.author_id = request.user.id
            # news_instance.author_id = 1     # for test

            news_instance.save()#存入数据库当中
            # news_instance.tag_id = form.cleaned_data.get('tag_id')
            return to_json_data(errmsg='文章创建成功')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串

            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)

from fdfs_client.client import Fdfs_client
from myblog import settings

# 指定fdfs客户端配置文件所在路径
FDFS_Client = Fdfs_client('utils/fastdfs/client.conf')
class NewsUploadImage(PermissionRequiredMixin, View):
    """
    """
    permission_required = ('news.add_news', )

    def handle_no_permission(self):
        return to_json_data(errno=Code.ROLEERR, errmsg='没有上传图片的权限')

    def post(self, request):
        image_file = request.FILES.get('image_file')
        if not image_file:
            logger.info('从前端获取图片失败')
            return to_json_data(errno=Code.NODATA, errmsg='从前端获取图片失败')

        if image_file.content_type not in ('image/jpeg', 'image/png', 'image/gif'):
            return to_json_data(errno=Code.DATAERR, errmsg='不能上传非图片文件')

        try:
            image_ext_name = image_file.name.split('.')[-1]
        except Exception as e:
            logger.info('图片拓展名异常：{}'.format(e))
            image_ext_name = 'jpg'

        try:
            upload_res = FDFS_Client.upload_by_buffer(image_file.read(), file_ext_name=image_ext_name)
        except Exception as e:
            logger.error('图片上传出现异常：{}'.format(e))
            return to_json_data(errno=Code.UNKOWNERR, errmsg='图片上传异常')
        else:
            if upload_res.get('Status') != 'Upload successed.':
                logger.info('图片上传到FastDFS服务器失败')
                return to_json_data(Code.UNKOWNERR, errmsg='图片上传到服务器失败')
            else:
                image_name = upload_res.get('Remote file_id')
                image_url = settings.FASTDFS_SERVER_DOMAIN + image_name
                return to_json_data(data={'image_url': image_url}, errmsg='图片上传成功')


class UploadToken(PermissionRequiredMixin,View):
    """
    """
    permission_required = ('news.add_news','news.view_news')

    def handle_no_permission(self):
        return to_json_data(errno=Code.ROLEERR, errmsg='没有权限')

    def get(self, request):
        access_key = qiniu_secret_info.QI_NIU_ACCESS_KEY
        secret_key = qiniu_secret_info.QI_NIU_SECRET_KEY
        bucket_name = qiniu_secret_info.QI_NIU_BUCKET_NAME
        # 构建鉴权对象
        q = qiniu.Auth(access_key, secret_key)
        token = q.upload_token(bucket_name)

        return JsonResponse({"uptoken": token})


class HotNewsManageView(PermissionRequiredMixin, View):
    """
    """
    permission_required = ('news.view_hotnews', )
    raise_exception = True

    def get(self, request):
        hot_news = models.HotNews.objects.select_related('news__tag'). \
                       only('news_id', 'news__title', 'news__tag__name', 'priority'). \
                       filter(is_delete=False).order_by('priority', '-news__clicks')[0:SHOW_HOTNEWS_COUNT]

        return render(request, 'admin/news/news_hot.html', locals())


class HotNewsEditView(PermissionRequiredMixin, View):
    """
    """
    permission_required = ('news.change_hotnews', 'news.delete_hotnews')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(HotNewsEditView, self).handle_no_permission()

    def delete(self, request, hotnews_id):
        hotnews = models.HotNews.objects.only('id').filter(id=hotnews_id).first()
        if hotnews:
            hotnews.is_delete = True
            hotnews.save(update_fields=['is_delete'])
            return to_json_data(errmsg="热门文章删除成功")
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要删除的热门文章不存在")

    def put(self, request, hotnews_id):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        try:
            priority = int(dict_data.get('priority'))
            priority_list = [i for i, _ in models.HotNews.PRI_CHOICES]#列表推导式 元组拆包成列表 _占位符 表示为空
            if priority not in priority_list:
                return to_json_data(errno=Code.PARAMERR, errmsg='热门文章的优先级设置错误')
        except Exception as e:
            logger.info('热门文章优先级异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='热门文章的优先级设置错误')

        hotnews = models.HotNews.objects.only('id').filter(id=hotnews_id).first()
        if not hotnews:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要更新的热门文章不存在")

        if hotnews.priority == priority:
            return to_json_data(errno=Code.PARAMERR, errmsg="热门文章的优先级未改变")

        hotnews.priority = priority
        hotnews.save(update_fields=['priority'])
        return to_json_data(errmsg="热门文章更新成功")


class HotNewsAddView(PermissionRequiredMixin, View):
    """
    route: /admin/hotnews/add/
    """
    permission_required = ('news.add_hotnews', 'news.view_hotnews')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(HotNewsAddView, self).handle_no_permission()

    def get(self, request):
        tags = models.Tag.objects.values('id', 'name').annotate(num_news=Count('news')). \
            filter(is_delete=False).order_by('-num_news', 'update_time')
        # 优先级列表
        # priority_list = {K: v for k, v in models.HotNews.PRI_CHOICES}
        priority_dict = OrderedDict(models.HotNews.PRI_CHOICES)

        return render(request, 'admin/news/news_hot_add.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        try:
            news_id = int(dict_data.get('news_id'))
        except Exception as e:
            logger.info('前端传过来的文章id参数异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='参数错误')

        if not models.News.objects.filter(id=news_id).exists():
            return to_json_data(errno=Code.PARAMERR, errmsg='文章不存在')

        try:
            priority = int(dict_data.get('priority'))
            priority_list = [i for i, _ in models.HotNews.PRI_CHOICES]
            if priority not in priority_list:
                return to_json_data(errno=Code.PARAMERR, errmsg='热门文章的优先级设置错误')
        except Exception as e:
            logger.info('热门文章优先级异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='热门文章的优先级设置错误')

        # 创建热门新闻
        hotnews_tuple = models.HotNews.objects.get_or_create(news_id=news_id)
        hotnews, is_created = hotnews_tuple
        hotnews.priority = priority  # 修改优先级
        hotnews.save(update_fields=['priority'])
        return to_json_data(errmsg="热门文章创建成功")


class NewsByTagIdView(PermissionRequiredMixin, View):
    """
    route: /admin/tags/<int:tag_id>/news/
    """
    permission_required = ('news.view_news', 'news.add_hotnews')
    # raise_exception = True

    def handle_no_permission(self):
        return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')

    def get(self, request, tag_id):
        newses = models.News.objects.values('id', 'title').filter(is_delete=False, tag_id=tag_id)
        news_list = [i for i in newses]

        return to_json_data(data={
            'news': news_list
        })


class BannerManageView(PermissionRequiredMixin, View):
    permission_required = ('news.view_banner', )
    raise_exception = True

    def get(self, request):
        priority_dict = OrderedDict(models.Banner.PRI_CHOICES)
        banners = models.Banner.objects.only('image_url', 'priority').filter(is_delete=False)
        return render(request, 'admin/news/news_banner.html', locals())


class BannerEditView(PermissionRequiredMixin, View):
    permission_required = ('news.delete_banner', 'news.change_banner')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(BannerEditView, self).handle_no_permission()

    def delete(self, request, banner_id):
        banner = models.Banner.objects.only('id').filter(id=banner_id).first()
        if banner:
            banner.is_delete = True
            banner.save(update_fields=['is_delete'])
            return to_json_data(errmsg="轮播图删除成功")
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要删除的轮播图不存在")

    def put(self, request, banner_id):
        banner = models.Banner.objects.only('id').filter(id=banner_id).first()
        if not banner:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要更新的轮播图不存在")

        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        try:
            priority = int(dict_data.get('priority'))
            priority_list = [i for i, _ in models.Banner.PRI_CHOICES]
            if priority not in priority_list:
                return to_json_data(errno=Code.PARAMERR, errmsg='轮播图的优先级设置错误')
        except Exception as e:
            logger.info('轮播图优先级异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='轮播图的优先级设置错误')

        image_url = dict_data.get('image_url')
        if not image_url:
            return to_json_data(errno=Code.PARAMERR, errmsg='轮播图url为空')

        if banner.priority == priority and banner.image_url == image_url:
            return to_json_data(errno=Code.PARAMERR, errmsg="轮播图的参数未改变")

        banner.priority = priority
        banner.image_url = image_url
        banner.save(update_fields=['priority', 'image_url'])
        return to_json_data(errmsg="轮播图更新成功")


class BannerAddView(PermissionRequiredMixin, View):
    permission_required = ('news.add_banner', 'news.change_banner', 'news.view_banner')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(BannerAddView, self).handle_no_permission()

    def get(self, request):
        tags = models.Tag.objects.values('id', 'name').annotate(num_news=Count('news')). \
            filter(is_delete=False).order_by('-num_news', 'update_time')
        # 优先级列表
        # priority_list = {K: v for k, v in models.Banner.PRI_CHOICES}
        priority_dict = OrderedDict(models.Banner.PRI_CHOICES)

        return render(request, 'admin/news/news_banner_add.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        try:
            news_id = int(dict_data.get('news_id'))
        except Exception as e:
            logger.info('前端传过来的文章id参数异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='参数错误')

        if not models.News.objects.filter(id=news_id).exists():
            return to_json_data(errno=Code.PARAMERR, errmsg='文章不存在')

        try:
            priority = int(dict_data.get('priority'))
            priority_list = [i for i, _ in models.Banner.PRI_CHOICES]
            if priority not in priority_list:
                return to_json_data(errno=Code.PARAMERR, errmsg='轮播图的优先级设置错误')
        except Exception as e:
            logger.info('轮播图优先级异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='轮播图的优先级设置错误')

        # 获取轮播图url
        image_url = dict_data.get('image_url')
        if not image_url:
            return to_json_data(errno=Code.PARAMERR, errmsg='轮播图url为空')

        # 创建轮播图
        banners_tuple = models.Banner.objects.get_or_create(news_id=news_id)
        banner, is_created = banners_tuple

        banner.priority = priority
        banner.image_url = image_url
        banner.save(update_fields=['priority', 'image_url'])
        return to_json_data(errmsg="轮播图创建成功")


class DocsManageView(PermissionRequiredMixin, View):
    """
    route: /admin/docs/
    """
    permission_required = ('doc.view_doc', 'doc.add_doc')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(DocManageView, self).handle_no_permission()

    def get(self, request):
        docs = Doc.objects.only('title', 'create_time').filter(is_delete=False)
        return render(request, 'admin/doc/docs_manage.html', locals())


class DocsEditView(PermissionRequiredMixin, View):
    """
    route: /admin/docs/<int:doc_id>/
    """
    permission_required = ('doc.change_doc', 'doc.delete_doc')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(DocsEditView, self).handle_no_permission()

    def get(self, request, doc_id):
        """
        """
        doc = Doc.objects.filter(is_delete=False, id=doc_id).first()
        if doc:
            tags = Doc.objects.only('id', 'name').filter(is_delete=False)
            context = {
                'doc': doc
            }
            return render(request, 'admin/doc/docs_pub.html', context=context)
        else:
            raise Http404('需要更新的文章不存在！')

    def delete(self, request, doc_id):
        doc = Doc.objects.filter(is_delete=False, id=doc_id).first()
        if doc:
            doc.is_delete = True
            doc.save(update_fields=['is_delete'])
            return to_json_data(errmsg="文档删除成功")
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要删除的文档不存在")

    def put(self, request, doc_id):
        doc = Doc.objects.filter(is_delete=False, id=doc_id).first()
        if not doc:
            return to_json_data(errno=Code.NODATA, errmsg='需要更新的文档不存在')

        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        form = forms.DocsPubForm(data=dict_data)
        if form.is_valid():
            doc.title = form.cleaned_data.get('title')
            doc.desc = form.cleaned_data.get('desc')
            doc.file_url = form.cleaned_data.get('file_url')
            doc.image_url = form.cleaned_data.get('image_url')
            doc.save()
            return to_json_data(errmsg='文档更新成功')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串

            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)


class DocsPubView(PermissionRequiredMixin, View):
    """
    route: /admin/docs/pub/
    """
    permission_required = ('doc.add_doc', 'doc.view_doc')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(DocsPubView, self).handle_no_permission()

    def get(self, request):

        return render(request, 'admin/doc/docs_pub.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        form = forms.DocsPubForm(data=dict_data)
        if form.is_valid():
            docs_instance = form.save(commit=False)
            docs_instance.author_id = request.user.id
            docs_instance.save()
            return to_json_data(errmsg='文档创建成功')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串

            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)


class DocsUploadFile(PermissionRequiredMixin, View):
    """route: /admin/docs/files/
    """
    permission_required = ('doc.add_doc', )

    def handle_no_permission(self):
        return to_json_data(errno=Code.ROLEERR, errmsg='没有上传文件的权限')

    def post(self, request):
        text_file = request.FILES.get('text_file')
        if not text_file:
            logger.info('从前端获取文件失败')
            return to_json_data(errno=Code.NODATA, errmsg='从前端获取文件失败')

        if text_file.content_type not in ('application/msword', 'application/octet-stream', 'application/pdf',
                                          'application/zip', 'text/plain', 'application/x-rar'):
            return to_json_data(errno=Code.DATAERR, errmsg='不能上传非文本文件')

        try:
            text_ext_name = text_file.name.split('.')[-1]
        except Exception as e:
            logger.info('文件拓展名异常：{}'.format(e))
            text_ext_name = 'pdf'

        try:
            upload_res = FDFS_Client.upload_by_buffer(text_file.read(), file_ext_name=text_ext_name)
        except Exception as e:
            logger.error('文件上传出现异常：{}'.format(e))
            return to_json_data(errno=Code.UNKOWNERR, errmsg='文件上传异常')
        else:
            if upload_res.get('Status') != 'Upload successed.':
                logger.info('文件上传到FastDFS服务器失败')
                return to_json_data(Code.UNKOWNERR, errmsg='文件上传到服务器失败')
            else:
                text_name = upload_res.get('Remote file_id')
                text_url = settings.FASTDFS_SERVER_DOMAIN + text_name
                return to_json_data(data={'text_file': text_url}, errmsg='文件上传成功')

class CoursesManageView(PermissionRequiredMixin, View):
    """
    route: /admin/courses/
    """
    permission_required = ('course.add_course', 'course.view_course')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(CoursesManageView, self).handle_no_permission()

    def get(self, request):
        courses = Course.objects.select_related('category', 'teacher').\
            only('title', 'category__name', 'teacher__name').filter(is_delete=False)
        return render(request, 'admin/course/courses_manage.html', locals())


class CoursesEditView(PermissionRequiredMixin, View):
    """
    route: /admin/courses/<int:course_id>/
    """
    permission_required = ('course.change_course', 'course.delete_course')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(CoursesEditView, self).handle_no_permission()

    def get(self, request, course_id):
        """
        """
        course = Course.objects.filter(is_delete=False, id=course_id).first()
        if course:
            teachers = Teacher.objects.only('name').filter(is_delete=False)
            categories = CourseCategory.objects.only('name').filter(is_delete=False)
            return render(request, 'admin/course/courses_pub.html', locals())
        else:
            raise Http404('需要更新的课程不存在！')

    def delete(self, request, course_id):
        course = Course.objects.filter(is_delete=False, id=course_id).first()
        if course:
            course.is_delete = True
            course.save(update_fields=['is_delete'])
            return to_json_data(errmsg="课程删除成功")
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要删除的课程不存在")

    def put(self, request, course_id):
        course = Course.objects.filter(is_delete=False, id=course_id).first()
        if not course:
            return to_json_data(errno=Code.NODATA, errmsg='需要更新的课程不存在')

        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        form = forms.CoursesPubForm(data=dict_data)
        if form.is_valid():
            for attr, value in form.cleaned_data.items():
                setattr(course, attr, value)

            course.save()
            return to_json_data(errmsg='课程更新成功')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串

            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)


class CoursesPubView(PermissionRequiredMixin, View):
    """
    route: /admin/courses/pub/
    """
    permission_required = ('course.add_course', 'course.view_course')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(CoursesPubView, self).handle_no_permission()

    def get(self, request):
        teachers = Teacher.objects.only('name').filter(is_delete=False)
        categories = CourseCategory.objects.only('name').filter(is_delete=False)
        return render(request, 'admin/course/courses_pub.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))

        form = forms.CoursesPubForm(data=dict_data)
        if form.is_valid():
            courses_instance = form.save()
            return to_json_data(errmsg='课程发布成功')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串

            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)


class GroupsManageView(PermissionRequiredMixin, View):
    """
    route: /admin/groups/
    """
    permission_required = ('auth.add_group', 'auth.view_group')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(GroupsManageView, self).handle_no_permission()

    def get(self, request):

        groups = Group.objects.values('id', 'name').annotate(num_users=Count('user')).\
            order_by('-num_users', 'id')
        return render(request, 'admin/user/groups_manage.html', locals())


class GroupsEditView(PermissionRequiredMixin, View):
    """
    route: /admin/groups/<int:group_id>/
    """
    permission_required = ('auth.change_group', 'auth.delete_group')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(GroupsEditView, self).handle_no_permission()

    def get(self, request, group_id):
        """
        """
        group = Group.objects.filter(id=group_id).first()
        if group:
            permissions = Permission.objects.only('id').all()
            return render(request, 'admin/user/groups_add.html', locals())
        else:
            raise Http404('需要更新的组不存在！')

    def delete(self, request, group_id):
        group = Group.objects.filter(id=group_id).first()
        if group:
            group.permissions.clear()   # 清空权限
            group.delete()
            return to_json_data(errmsg="用户组删除成功")
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要删除的用户组不存在")

    def put(self, request, group_id):
        group = Group.objects.filter(id=group_id).first()
        if not group:
            return to_json_data(errno=Code.NODATA, errmsg='需要更新的用户组不存在')

        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        # 取出组名，进行判断
        group_name = dict_data.get('name', '').strip()
        if not group_name:
            return to_json_data(errno=Code.PARAMERR, errmsg='组名为空')

        if group_name != group.name and Group.objects.filter(name=group_name).exists():
            return to_json_data(errno=Code.DATAEXIST, errmsg='组名已存在')

        # 取出权限
        group_permissions = dict_data.get('group_permissions')
        if not group_permissions:
            return to_json_data(errno=Code.PARAMERR, errmsg='权限参数为空')

        try:
            permissions_set = set(int(i) for i in group_permissions)
        except Exception as e:
            logger.info('传的权限参数异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='权限参数异常')

        all_permissions_set = set(i.id for i in Permission.objects.only('id'))
        if not permissions_set.issubset(all_permissions_set):
            return to_json_data(errno=Code.PARAMERR, errmsg='有不存在的权限参数')
        #print(type(group))
        #print(type(group.permissions))
        existed_permissions_set = set(i.id for i in group.permissions.all())
        if group_name == group.name and permissions_set == existed_permissions_set:
            return to_json_data(errno=Code.DATAEXIST, errmsg='用户组信息未修改')
        # 设置权限
        for perm_id in permissions_set:
            p = Permission.objects.get(id=perm_id)
            group.permissions.add(p)
        group.name = group_name
        group.save()
        return to_json_data(errmsg='组更新成功！')


class GroupsAddView(PermissionRequiredMixin, View):
    """
    route: /admin/groups/add/
    """
    permission_required = ('auth.add_group', 'auth.view_group')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(GroupsAddView, self).handle_no_permission()

    def get(self, request):
        permissions = Permission.objects.only('id').all()

        return render(request, 'admin/user/groups_add.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))

        # 取出组名，进行判断
        group_name = dict_data.get('name', '').strip()
        if not group_name:
            return to_json_data(errno=Code.PARAMERR, errmsg='组名为空')

        one_group, is_created = Group.objects.get_or_create(name=group_name)
        if not is_created:
            return to_json_data(errno=Code.DATAEXIST, errmsg='组名已存在')

        # 取出权限
        group_permissions = dict_data.get('group_permissions')
        if not group_permissions:
            return to_json_data(errno=Code.PARAMERR, errmsg='权限参数为空')

        try:
            permissions_set = set(int(i) for i in group_permissions)
        except Exception as e:
            logger.info('传的权限参数异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='权限参数异常')

        all_permissions_set = set(i.id for i in Permission.objects.only('id'))
        if not permissions_set.issubset(all_permissions_set):
            return to_json_data(errno=Code.PARAMERR, errmsg='有不存在的权限参数')

        # 设置权限
        for perm_id in permissions_set:
            p = Permission.objects.get(id=perm_id)
            one_group.permissions.add(p)

        one_group.save()
        return to_json_data(errmsg='组创建成功！')


class UsersManageView(PermissionRequiredMixin, View):
    """
    route: /admin/users/
    """
    permission_required = ('users.add_users', 'users.view_users')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(UsersManageView, self).handle_no_permission()

    def get(self, request):
        users = Users.objects.only('username', 'is_staff', 'is_superuser').filter(is_active=True)
        return render(request, 'admin/user/users_manage.html', locals())


class UsersEditView(PermissionRequiredMixin, View):
    """
    route: /admin/users/<int:user_id>/
    """
    permission_required = ('users.change_users', 'users.delete_users')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(UsersEditView, self).handle_no_permission()

    def get(self, request, user_id):
        user_instance = Users.objects.filter(id=user_id).first()
        if user_instance:
            groups = Group.objects.only('name').all()
            return render(request, 'admin/user/users_edit.html', locals())
        else:
            raise Http404('需要更新的用户不存在！')

    def delete(self, request, user_id):
        user_instance = Users.objects.filter(id=user_id).first()
        if user_instance:
            user_instance.groups.clear()    # 清除用户组
            user_instance.user_permissions.clear()  # 清除用户权限
            user_instance.is_active = False  # 设置为不激活状态
            user_instance.save()
            return to_json_data(errmsg="用户删除成功")
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要删除的用户不存在")

    def put(self, request, user_id):
        user_instance = Users.objects.filter(id=user_id).first()
        if not user_instance:
            return to_json_data(errno=Code.NODATA, errmsg='需要更新的用户不存在')

        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        # 取出参数，进行判断
        try:
            groups = dict_data.get('groups')    # 取出用户组列表

            is_staff = int(dict_data.get('is_staff'))
            is_superuser = int(dict_data.get('is_superuser'))
            is_active = int(dict_data.get('is_active'))
            params = (is_staff, is_superuser, is_active)
            if not all([p in (0, 1) for p in params]):
                return to_json_data(errno=Code.PARAMERR, errmsg='参数错误')
        except Exception as e:
            logger.info('从前端获取参数出现异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='参数错误')

        try:
            groups_set = set(int(i) for i in groups) if groups else set()
        except Exception as e:
            logger.info('传的用户组参数异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='用户组参数异常')

        all_groups_set = set(i.id for i in Group.objects.only('id'))
        if not groups_set.issubset(all_groups_set):
            return to_json_data(errno=Code.PARAMERR, errmsg='有不存在的用户组参数')

        gs = Group.objects.filter(id__in=groups_set)#id 在 group_set 范围内的所有组取出来
        # 先清除组
        user_instance.groups.clear()
        # 设置组
        user_instance.groups.set(gs)

        user_instance.is_staff = bool(is_staff)
        user_instance.is_superuser = bool(is_superuser)
        user_instance.is_active = bool(is_active)
        user_instance.save()
        return to_json_data(errmsg='用户信息更新成功！')


class UserProfileManageView(PermissionRequiredMixin,View):
    """
    route:/admin/usersprofile/
    """
    permission_required = ('users.view_users','users.view_usersprofile')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR,errmsg='没有操作权限')
        else:
            return super(UserProfileManageView,self).handle_no_permission()

    def get(self,request):
        users = Users.objects.only('username','is_staff','is_superuser','date_joined','last_login').filter(is_active=True)
        return render(request,'admin/user/usersprofile_manage.html',locals())


class UsersProfileEditView(PermissionRequiredMixin, View):
    """
    route: /admin/usersprofile/<int:user_id>/
    """
    permission_required = ('users.change_usersprofile', 'users.delete_usersprofile')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method.lower() != 'get':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(UsersProfileEditView, self).handle_no_permission()

    def get(self, request, user_id):
        user_profile = UsersProfile.objects.filter(user_id=user_id).first()
        users = Users.objects.only('id','username').filter(id=user_id).first()
        return render(request, 'admin/user/usersprofile_edit.html', locals())
        #raise Http404('需要更新的用户不存在！')

    def delete(self, request, user_id):
        user_instance = UsersProfile.objects.filter(id=user_id).first()
        if user_instance:
            user_instance.nickname = None  # 清除用户组
            user_instance.born_date = None  # 清除用户权限
            user_instance.motto = None  # 设置为不激活状态
            user_instance.save()
            return to_json_data(errmsg="用户信息删除成功")
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要删除的用户不存在")

    def put(self, request, user_id):
        if user_id:
            user_instance = UsersProfile.objects.filter(user_id=user_id).first()
            if not user_instance:
                return to_json_data(errno=Code.NODATA, errmsg='需要更新的用户不存在')

            json_data = request.body
            if not json_data:
                return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
            # 将json转化为dict
            dict_data = json.loads(json_data.decode('utf8'))
            #print(dict_data['born_date'])
            born_date = datetime.strptime(dict_data['born_date'],'%Y/%m/%d') or datetime.strptime(dict_data['born_date'],'%Y年%m月%d日')
            #print(born_date)
            user_instance.nickname = dict_data.get('nickname')
            user_instance.born_date = born_date
            user_instance.gender = dict_data.get('gender')
            user_instance.motto = dict_data.get('motto')
            user_instance.save()
            return to_json_data(errmsg='用户信息更新成功！')

    def post(self,request,user_id):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        born_date = datetime.strptime(dict_data['born_date'], '%Y/%m/%d')
        # print(born_date)
        dict_data.update({'born_date':born_date})
        #print(dict_data)
        form = forms.UsersprofileAddForm(data=dict_data)
        #print(form.__str__())
        if form.is_valid():
            # 3.
            # n = models.News(title=form.cleaned_data.get('title'))
            # n = models.News(**form.cleaned_data)#字典拆包
            # n.title = form.cleaned_data.get('title')
            # n.save()
            # news_instance = form.save()
            users_instance = form.save(commit=False)  # 默认commit为true save直接存入mysql当中 false不会
            #users_instance.user_id = user_id
            users_instance.save()  # 存入数据库当中
            # news_instance.tag_id = form.cleaned_data.get('tag_id')
            return to_json_data(errmsg='用户信息创建成功')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串

            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)