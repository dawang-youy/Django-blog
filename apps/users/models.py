import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser,UserManager as _UserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from utils.models import ModelBase
# Create your models here.
class UserManager(_UserManager):
    """
    define user manager for modifing 'no need email'
    when 'python manager.py createsuperuser '

    """

    def create_superuser(self, username, password, email=None, **extra_fields):
        super(UserManager, self).create_superuser(username=password,
                                                  password=password, email=email, **extra_fields)
class Users(AbstractUser):
    """
    add mobile/email_active fields to Django users modules
    """
    objects = UserManager()
    # A list of the field names that will be prompted for
    # when creating a user via the createsuperuser management command.
    REQUIRED_FIELDS = ['mobile']
    # help_text在api接口文档中会用到
    # verbose_name在admin站点中会用到
    mobile = models.CharField(max_length=11,unique=True,help_text="手机号",verbose_name="手机号",
                              error_messages={
                                  'unique':"此手机号已经注册",
                              },)
    email_active = models.BooleanField(default=False,verbose_name="邮箱验证状态")
    #源数据信息
    class Meta:
        #数据表
        db_table = 'tb_users'# 指明数据库表名
        verbose_name = '用户'# 在admin站点中显示的名称
        #显示的复数名称
        verbose_name_plural = verbose_name

    def get_groups_name(self):
        groups_name_list = [i.name for i in self.groups.all()]
        # 列表转字符串 通常用join方法 而非用 + 可迭代对象都可以用join方法
        return '|'.join(groups_name_list)#

    # 打印对象时调用
    def __str__(self):
        return self.username

class UsersProfile(ModelBase):
    """create users profile model
    """
    GENDER_CHOICES = (
        ('M', '男'),
        ('F', '女'),
    )
    user = models.OneToOneField(Users, on_delete=models.CASCADE, related_name='user_profile')
    nickname = models.TextField(max_length=100, null=True, blank=True)
    born_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    motto = models.TextField(max_length=1024, null=True, blank=True)

    class Meta:
        #数据表
        db_table = 'tb_users_profile'# 指明数据库表名
        verbose_name = '用户个人信息'# 在admin站点中显示的名称
        #显示的复数名称
        verbose_name_plural = verbose_name

@receiver(post_save,sender=Users)
def create_user_profile(sender,**kwargs):
    """
        create user profile function
    """
    if kwargs.get('created',False):
        user_profile = UsersProfile.objects.get_or_create(user=kwargs.get('instance'))
        if user_profile[-1]:
            user_profile = user_profile[0]
            user_profile.nickname = '老李'
            user_profile.born_date = datetime.date(1980,11,11)
            user_profile.motto = '老李出马，一个顶两'
            user_profile.save()