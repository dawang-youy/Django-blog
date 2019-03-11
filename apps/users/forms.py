#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-------------------------------------------------
  @Time : 2018/12/8 2:22 PM
  @Auth : Youkou
  @Site : www.youkou.site
  @File : forms.py
  @IDE  : PyCharm
  @Edit : 2018/12/8
-------------------------------------------------
"""
import re

from django import forms
from django.db.models import Q
from django_redis import get_redis_connection
from django.contrib.auth import login,logout

from verifications.constants import SMS_CODE_NUMS
from .models import Users
from . import constants
class RegisterForm(forms.Form):
    """
    """
    username = forms.CharField(label='用户名', max_length=20, min_length=5,
                               error_messages={"min_length": "用户名长度要大于5", "max_length": "用户名长度要小于20",
                                               "required": "用户名不能为空"}
                               )
    password = forms.CharField(label='密码', max_length=20, min_length=6,
                               error_messages={"min_length": "密码长度要大于6", "max_length": "密码长度要小于20",
                                               "required": "密码不能为空"}
                               )
    password_repeat = forms.CharField(label='确认密码', max_length=20, min_length=6,
                                      error_messages={"min_length": "密码长度要大于6", "max_length": "密码长度要小于20",
                                                      "required": "密码不能为空"}
                                      )
    mobile = forms.CharField(label='手机号', max_length=11, min_length=11,
                             error_messages={"min_length": "手机号长度有误", "max_length": "手机号长度有误",
                                             "required": "手机号不能为空"})

    sms_code = forms.CharField(label='短信验证码', max_length=SMS_CODE_NUMS, min_length=SMS_CODE_NUMS,
                               error_messages={"min_length": "短信验证码长度有误", "max_length": "短信验证码长度有误",
                                               "required": "短信验证码不能为空"})
    route_id = forms.CharField(label='路由id')

    def clean_mobile(self):
        """
        check mobile
        :return:
        """
        tel = self.cleaned_data.get('mobile')
        # route_id = self.cleaned_data.get('route_id')
        # username = self.cleaned_data.get('username')
        # print(2,tel,route_id,username)
        if not re.match(r"^1[3-9]\d{9}$", tel):
            raise forms.ValidationError("手机号码格式不正确")

        # if Users.objects.filter(mobile=tel).exists():
        #     raise forms.ValidationError("手机号已注册，请重新输入！")

        return tel

    def clean(self):
        """
        check whether the two passwords are the same,and check whether the sms_code is correct.
        :return:
        """
        #1.获取参数
        cleaned_data = super().clean()
        passwd = cleaned_data.get('password')
        passwd_repeat = cleaned_data.get('password_repeat')
        #2.判断两次输入的密码是否一致
        if passwd != passwd_repeat:
            raise forms.ValidationError("两次密码不一致")

        #3.判断短信验证码是否正确
        tel = cleaned_data.get('mobile')
        sms_text = cleaned_data.get('sms_code')
        #route_id = cleaned_data.get('route_id')
        #print(1,route_id)
        # 建立redis连接
        redis_conn = get_redis_connection(alias='verify_codes')
        #创建保存短信验证码的标记key
        sms_fmt = "sms_{}".format(tel).encode('utf-8')
        #
        real_sms = redis_conn.get(sms_fmt)
        #print(real_sms)
        #print(real_sms.decode('utf-8'),sms_text)
        #
        if (not real_sms) or (sms_text != real_sms.decode('utf-8')):
            raise forms.ValidationError("短信验证码错误")

class LoginForm(forms.Form):
    """
    login form data
    """
    user_account = forms.CharField()
    password = forms.CharField(label='密码', max_length=20, min_length=6,
                               error_messages={"min_length": "密码长度要大于6", "max_length": "密码长度要小于20",
                                               "required": "密码不能为空"})
    remember_me = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        构造request 参数 帮助传参 设置session
        """
        self.request = kwargs.pop('request', None)#pop 没有 返回None
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean_user_account(self):
        """
        初始校验
        """
        user_info = self.cleaned_data.get('user_account')
        if not user_info:
            raise forms.ValidationError("用户账号不能为空")

        if not re.match(r"^1[3-9]\d{9}$", user_info) and (len(user_info) < 5 or len(user_info) > 20):
            raise forms.ValidationError("用户账号格式不正确，请重新输入")

        return user_info

    def clean(self):
        """
        查询数据库 检查数据 实现登录
        """
        cleaned_data = super().clean()
        # 1.获取清洗之后的用户账号
        user_info = cleaned_data.get('user_account')
        # 2. 获取清洗之后的用户密码
        passwd = cleaned_data.get('password')
        hold_login = cleaned_data.get('remember_me')

        # 在form表单中实现登录逻辑
        #3.查询数据库，判断用户账号和密码是否正确
        user_queryset = Users.objects.filter(Q(mobile=user_info) | Q(username=user_info))
        if user_queryset:
            user = user_queryset.first()
            if user.check_password(passwd):
                if hold_login:  # 在redis中保存session信息
                    self.request.session.set_expiry(constants.USER_SESSION_EXPIRES)
                    #None 如果value是None,session会依赖全局session失效策略 为两周过期 constants.USER_SESSION_EXPIRES 5天
                else:
                    self.request.session.set_expiry(0)
                    #如果value是0,用户关闭浏览器session就会失效。如果value是个datatime或timedelta，session就会在这个时间后失效。
                login(self.request, user)
            else:
                raise forms.ValidationError("密码不正确，请重新输入")
        #4.查询结果返回
        else:
            raise forms.ValidationError("用户账号不存在，请重新输入")

class ChangeForm(forms.Form):
    """
    check password form data
    """
    user_account = forms.CharField()
    password = forms.CharField(label='密码', max_length=20, min_length=6,
                               error_messages={"min_length": "密码长度要大于6", "max_length": "密码长度要小于20",
                                               "required": "密码不能为空"})

    def clean_user_account(self):
        """
        初始校验
        """
        user_info = self.cleaned_data.get('user_account')
        if not user_info:
            raise forms.ValidationError("用户账号不能为空")

        if not re.match(r"^1[3-9]\d{9}$", user_info) and (len(user_info) < 5 or len(user_info) > 20):
            raise forms.ValidationError("用户账号格式不正确，请重新输入")

        return user_info

    def clean(self):
        """
        查询数据库 检查数据 实现登录
        """
        cleaned_data = super().clean()
        # 1.获取清洗之后的用户账号
        user_info = cleaned_data.get('user_account')
        # 2. 获取清洗之后的用户密码
        passwd = cleaned_data.get('password')
        #3.查询数据库，判断用户账号和密码是否正确
        user_queryset = Users.objects.filter(Q(mobile=user_info) | Q(username=user_info))
        if user_queryset:
            user = user_queryset.first()
            if not user.check_password(passwd):
                raise forms.ValidationError("密码不正确，请重新输入")
        #4.查询结果返回
        else:
            raise forms.ValidationError("用户账号不存在，请重新输入")