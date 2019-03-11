import json
import logging
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.contrib.auth import login,logout
from django.db.models import Q

from .forms import RegisterForm,LoginForm
from .models import Users
from utils.json_fun import to_json_data
from utils.res_code import Code, error_map
#导包顺序  PEP8 规范  内置的包 》 Django的包 》 （第三方包》）自己的包
logger = logging.getLogger('django')
# Create your views here.
# def register(request):
#     """
#     register page
#     :param request:
#     :return:
#     """
#     return render(request,'users/register.html')
# def login(request):
#     return render(request,'users/login.html')
#1.创建一个类
#2.创建get方法
#3.创建post方法
#4.获取前端传过来的参数
#5.校验参数
#6.将用户信息保存到数据库
#7.结果返回给前端
class RegisterView(View):
    """
    handle get request，render register page
    """
    def get(self, request):
        """
        :param request:
#       :return:
        创建get register page
        """
        return render(request, 'users/register.html')
    def post(self, request):
        """
        :param request:
#       :return:
        创建post
        """
        # 4.验证传过来的参数
        try:
            json_data = request.body
            if not json_data:
                return to_json_data(errno=Code.PARAMERR, errmsg='参数为空，请重新输入！')
            # 将json转化为dict
            #print(json_data.decode('utf8'))
            #print(type(json_data.decode('utf8')))
            dict_data = json.loads(json_data.decode('utf8'))
            # dict_data = json.loads(json_data)
        except Exception as e:
            logger.info('错误信息：\n{}'.format(e))
            return to_json_data(errno=Code.UNKOWNERR, errmsg=error_map[Code.UNKOWNERR])
        dict_data.update({'route_id': '0'})
        form = RegisterForm(data=dict_data)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            mobile = form.cleaned_data.get('mobile')
            print(password)
            user = Users.objects.create_user(username=username, password=password, mobile=mobile)
            # 处理session
            login(request, user)
            return to_json_data(errmsg="恭喜您，注册成功！")
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)
            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)
class LoginView(View):
    """
    user login view
    router:/users/login
    #1.创建类
    """
    def get(self, request):
        """
        :param request:
        :return login page
        """
        return render(request, 'users/login.html')
    def post(self, request):
        """
        :param request:
        :return:
        """
        #2.获取前端数据
        json_data = request.body
        #print(json_data,type(json_data))
        #3.校验参数
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8')) # 没有解码，会产生bug
        print(dict_data, type(dict_data))
        #4.用户登录，设置session
        form = LoginForm(data=dict_data, request=request)
        if form.is_valid():
            #5.返回前端
            return to_json_data(errmsg="恭喜您，登录成功！")
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串
            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)
class LogoutView(View):
    """
    """
    def get(self, request):
        logout(request)
        return redirect(reverse("users:login"))


class ChangeView(View):
    """
    create changepassword view
    """
    def get(self, request):
        """
        :param request:
#       :return:
        创建get change page
        """
        return render(request, 'users/changepassword.html')
    def post(self, request):
        """
        :param request:
#       :return:
        创建post
        """
        # 验证传过来的参数
        try:
            json_data = request.body
            if not json_data:
                return to_json_data(errno=Code.PARAMERR, errmsg='参数为空，请重新输入！')
            # 将json转化为dict
            dict_data = json.loads(json_data.decode('utf8'))
        except Exception as e:
            logger.info('错误信息：\n{}'.format(e))
            return to_json_data(errno=Code.UNKOWNERR, errmsg=error_map[Code.UNKOWNERR])
        dict_data.update({'route_id':'1'})#加一验证字段 可区别 注册与修改密码功能的form验证
        form = RegisterForm(data=dict_data)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user_queryset = Users.objects.filter(Q(mobile=username) | Q(username=username))
            if user_queryset:
                user = user_queryset.first()
                # 判断手机号与用户手机号是否相同
                tel = dict_data.get('mobile')
                #print(user.mobile)
                if tel != user.mobile:
                    return to_json_data(errno=Code.DATAERR, errmsg="手机号与注册时不符！")
                if user.check_password(password):
                    return to_json_data(errno=Code.DATAEXIST,errmsg="新密码与旧密码相同！")
                else:
                    user.set_password(password)
                    user.save()
                    return to_json_data(errmsg="恭喜您，密码修改成功!")
            else:
                return to_json_data(errmsg="用户账号不存在，请重新输入")
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)
            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)
