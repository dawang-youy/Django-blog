from django.db import models
from utils.models import ModelBase
# Create your models here.

class Tag(ModelBase):
    """
    create news tag model
    """
    name = models.CharField(max_length=64, verbose_name="标签名", help_text="标签名")
    class Meta:
        ordering = ['-update_time', '-id']
        db_table = "tb_tag"  # 指明数据库表名
        verbose_name = "新闻标签"  # 在admin站点中显示的名称
        verbose_name_plural = verbose_name  # 显示的复数名称
    def __str__(self):
        return self.name
class News(ModelBase):
    """
    create news model
    """
    title = models.CharField(max_length=150, verbose_name="标题", help_text="标题")
    digest = models.CharField(max_length=200, verbose_name="摘要", help_text="摘要")
    content = models.TextField(verbose_name="内容", help_text="内容")
    clicks = models.IntegerField(default=0, verbose_name="点击量", help_text="点击量")
    image_url = models.URLField(default="", verbose_name="图片url", help_text="图片url")
    #on_delete 多为子，一为主
    #CASCADE  主表删除 子表跟着删除
    #PROTECT  主表删除  抛 PROTECTerror异常
    #SET_NULL   主表删除字段  子表为null
    #SET_DEFAULT 主表删除字段  子表指定默认设定的
    #SET（） 括号里可以是函数，设置为自己定义的东西
    #DO_NOTHING  字面意思 啥也不干
    tag = models.ForeignKey('Tag', on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey('users.Users', on_delete=models.SET_NULL, null=True)
    class Meta:
        ordering = ['-update_time', '-id']#默认排序 update_time 倒序DESC 正序ASC
        db_table = "tb_news"  # 指明数据库表名
        verbose_name = "新闻"  # 在admin站点中显示的名称
        verbose_name_plural = verbose_name  # 显示的复数名称
    def __str__(self):
        return self.title
class Comments(ModelBase):
    """
    create news comment model
    """
    content = models.TextField(verbose_name="内容", help_text="内容")
    author = models.ForeignKey('users.Users', on_delete=models.SET_NULL, null=True)
    news = models.ForeignKey('News', on_delete=models.CASCADE)
    parents = models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True)
    class Meta:
        ordering = ['-update_time', '-id']
        db_table = "tb_comments"  # 指明数据库表名
        verbose_name = "评论"  # 在admin站点中显示的名称
        verbose_name_plural = verbose_name  # 显示的复数名称
    def __str__(self):
        return '<评论{}>'.format(self.id)

    def to_dict_data(self):
        comment_dict = {
            'news_id': self.news.id,
            'content_id': self.id,
            'content': self.content,
            'author': self.author.username,
            'update_time': self.update_time.strftime('%Y年%m月%d日 %H:%M'),
            'parents_id': self.parents.to_dict_data() if self.parents else None,
        }

        return comment_dict
class HotNews(ModelBase):
    """
    creat hotnews model
    """
    PRI_CHOICES = [
        (1,'第一级'),
        (2,'第二级'),
        (3,'第三级')
    ]
    news = models.OneToOneField('News', on_delete=models.CASCADE)
    priority = models.IntegerField(choices=PRI_CHOICES,default=3,verbose_name="优先级", help_text="优先级")
    class Meta:
        ordering = ['-update_time', '-id']
        db_table = "tb_hotnews"  # 指明数据库表名
        verbose_name = "热门新闻"  # 在admin站点中显示的名称
        verbose_name_plural = verbose_name  # 显示的复数名称
    def __str__(self):
        return '<热门新闻{}>'.format(self.id)
class Banner(ModelBase):
    """
    create news banner model
    """
    PRI_CHOICES = [
        (1,'第一级'),
        (2,'第二级'),
        (3,'第三级'),
        (4,'第四级'),
        (5,'第五级'),
        (6,'第六级'),
    ]
    image_url = models.URLField(verbose_name="轮播图url", help_text="轮播图url")
    priority = models.IntegerField(choices=PRI_CHOICES,default=6,verbose_name="优先级", help_text="优先级")
    news = models.OneToOneField('News', on_delete=models.CASCADE)
    class Meta:
        ordering = ['priority', '-update_time', '-id']
        db_table = "tb_banner"  # 指明数据库表名
        verbose_name = "轮播图"  # 在admin站点中显示的名称
        verbose_name_plural = verbose_name  # 显示的复数名称
    def __str__(self):
        return '<轮播图{}>'.format(self.id)

