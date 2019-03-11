import logging
import json
from django.shortcuts import render,HttpResponse
from django.http import Http404
from django.views import View
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from . import models
from . import constants
from utils.json_fun import to_json_data
from utils.res_code import Code,error_map
from myblog import settings
# Create your views here.
# 导入日志器
logger = logging.getLogger('django')
# def index(request):
#     """
#     index page
#     :param request:
#     :return:
#     """
#     return render(request,'news/index.html')
# def detail(request):
#     return render(request,'news/news_detail.html')
# def search(request):
#     return render(request,'news/search.html')
class IndexView(View):
    """
    create news view
    render tags hot_news
    """
    def get(self, request):
        """
        create index page view
        """
        tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)
        hot_news = models.HotNews.objects.select_related('news').only('news__title', 'news__image_url',
                                                                      'news__id').filter(is_delete=False).order_by(
            'priority', '-news__clicks')[0:constants.SHOW_HOTNEWS_COUNT]
        context = {
            'tags':tags,
            'hot_news':hot_news,
            'navId' : 0
        }
        navId = 0
        return render(request, 'news/index.html', locals())
#1.创建类视图
#2.校验参数
#3.从数据库中查询新闻列表数据
#4.序列化数据
#5.返回给前端
class NewsListView(View):
    """
    create news list view
    route :/news/
    """
    def get(self, request):
        print(request)
        try:
            tag_id = int(request.GET.get('tag_id', 0))
        except Exception as e:
            logger.error("标签错误：\n{}".format(e))
            tag_id = 0
        try:
            page = int(request.GET.get('page', 1))
        except Exception as e:
            logger.error("当前页数错误：\n{}".format(e))
            page = 1

        news_queryset = models.News.objects.select_related('tag', 'author'). \
            only('id','title', 'digest', 'image_url', 'update_time', 'tag__name', 'author__username')

        # if models.Tag.objects.only('id').filter(is_delete=False, id=tag_id).exists():
        # news = news_queryset.filter(is_delete=False, tag_id=tag_id)
        # else:
        # news = news_queryset.filter(is_delete=False)
        news = news_queryset.filter(is_delete=False, tag_id=tag_id) or \
               news_queryset.filter(is_delete=False)
        paginator = Paginator(news, constants.PER_PAGE_NEWS_COUNT)
        try:
            news_info = paginator.page(page)
        except EmptyPage:
            # 若用户访问的页数大于实际页数，则返回最后一页数据
            logging.info("用户访问的页数大于总页数。")
            news_info = paginator.page(paginator.num_pages)

        # 4.序列化输出
        news_info_list = []
        for n in news_info:
            news_info_list.append({
                'id': n.id,
                'title': n.title,
                'digest': n.digest,
                'image_url': n.image_url,
                'tag_name': n.tag.name,
                'author': n.author.username,
                'update_time': n.update_time.strftime('%Y年%m月%d日 %H:%M'),

            })

        # 5.创建返回给前端的数据
        data = {
            'total_pages': paginator.num_pages,
            'news': news_info_list
        }
        # print(data)
        return to_json_data(data=data)

class NewsBanner(View):
    """
    create news banner model
    router:/news/banners/
    """
    def get(self, request):
        banners = models.Banner.objects.select_related('news').only('image_url', 'news__id', 'news__title').\
            filter(is_delete=False)[0:constants.SHOW_BANNER_COUNT]

        # 序列化输出
        banners_info_list = []
        for b in banners:
            banners_info_list.append({
                'image_url': b.image_url,
                'news_id': b.news.id,
                'news_title': b.news.title,
            })

        # 创建返回给前端的数据
        data = {
            'banners': banners_info_list
        }

        return to_json_data(data=data)

class NewsDetailView(View):
    """
    create news detail view
    router：/news/<int:news_id>/
    """
    # /* 为文章内容添加样式 */
    # 在templates/news1/news_detail.html文件中需要添加如下内容：
    # .news-content p {
    # 	font-size: 16px;
    # 	line-height: 26px;
    # 	text-align: justify;
    # 	word-wrap: break-word;
    # 	padding: 3px 0
    # }
    def get(self, request, news_id):
        news = models.News.objects.select_related('tag', 'author'). \
            only('title', 'content', 'update_time', 'tag__name', 'author__username').\
            filter(is_delete=False, id=news_id).first()
        if news:
            comments = models.Comments.objects.select_related('author', 'parents').\
                only('content', 'author__username', 'update_time',
                     'parents__author__username', 'parents__content', 'parents__update_time').\
                filter(is_delete=False, news_id=news_id)

            # 序列化输出
            comments_list = []
            # 迭代之后开始去数据库查
            for comm in comments:
                comments_list.append(comm.to_dict_data())
            comments_count = len(comments_list)
            return render(request, 'news/news_detail.html', locals())
        else:
            raise Http404("<新闻{}>不存在😢".format(news_id))
            # return Http404('<h1>Page not found</h1>')
            #return HttpResponseNotFound('<h1>Page not found</h1>')
class NewsCommentView(View):
    """
     create newscomments detail view
        router：news/<int:news_id>/comments/
    """
    # print('2222')
    def post(self, request, news_id):
        # print('111111', request)
        if not request.user.is_authenticated:
            return to_json_data(errno=Code.SESSIONERR, errmsg=error_map[Code.SESSIONERR])

        if not models.News.objects.only('id').filter(is_delete=False, id=news_id).exists():
            return to_json_data(errno=Code.PARAMERR, errmsg="新闻不存在！")

        # 从前端获取参数
        try:
            json_data = request.body
            # print('111111',json_data)
            if not json_data:
                return to_json_data(errno=Code.PARAMERR, errmsg="参数为空，请重新输入！")
            # 将json转化为dict
            dict_data = json.loads(json_data.decode('utf8'))
        except Exception as e:
            logger.info('错误信息：\n{}'.format(e))
            return to_json_data(errno=Code.UNKOWNERR,errmsg=error_map[Code.UNKOWNERR])
        content = dict_data.get('content')
        if not content:
            return to_json_data(errno=Code.PARAMERR, errmsg="评论内容不能为空！")

        parents_id = dict_data.get('parents_id')
        try:
            if parents_id:
                parent_id = int(parents_id)
                if not models.Comments.objects.only('id'). \
                        filter(is_delete=False, id=parents_id, news_id=news_id).exists():
                    return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])

        except Exception as e:
            logging.info("前端传过来的parents_id异常：\n{}".format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg="未知异常")

        # 保存到数据库
        new_content = models.Comments()
        new_content.content = content
        new_content.news_id = news_id
        new_content.author = request.user
        new_content.parents_id = parents_id if parents_id else None
        new_content.save()

        return to_json_data(data=new_content.to_dict_data())
from haystack.views import SearchView as _SearchView


class SearchView(_SearchView):
    # 模版文件
    template = 'news/search.html'

    # 重写响应方式，如果请求参数q为空，返回模型News的热门新闻数据，否则根据参数q搜索相关数据
    def create_response(self):
        kw = self.request.GET.get('q', '')
        if not kw:
            show_all = True
            hot_news = models.HotNews.objects.select_related('news'). \
                only('news__title', 'news__image_url', 'news__id'). \
                filter(is_delete=False).order_by('priority', '-news__clicks')

            paginator = Paginator(hot_news, settings.HAYSTACK_SEARCH_RESULTS_PER_PAGE)
            try:
                page = paginator.page(int(self.request.GET.get('page', 1)))
            except PageNotAnInteger:
                # 如果参数page的数据类型不是整型，则返回第一页数据
                page = paginator.page(1)
            except EmptyPage:
                # 用户访问的页数大于实际页数，则返回最后一页的数据
                page = paginator.page(paginator.num_pages)
            navId = 3
            return render(self.request, self.template, locals())
        else:
            show_all = False
            qs = super(SearchView, self).create_response()
            return qs