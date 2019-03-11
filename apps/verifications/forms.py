#!/usr/bin/myblog_env python3
# -*- coding: utf-8 -*-
"""
-------------------------------------------------
  @Time : 2018/12/3 4:18 PM
  @Auth : Youkou
  @Site : www.youkou.site
  @File : forms.py
  @IDE  : PyCharm
  @Edit : 2018/12/3
-------------------------------------------------
"""
import re

from django import forms
from django.core.validators import RegexValidator
from django_redis import get_redis_connection
from django.db.models import Q

from users.models import Users

# 创建手机号的正则校验器
mobile_validator = RegexValidator(r"^1[345789]\d{9}$", "手机号码格式不正确")


class CheckImgCodeForm(forms.Form):
    """
    check image code
    """
    mobile = forms.CharField(max_length=11, min_length=11, validators=[mobile_validator, ],
                             error_messages={"min_length": "手机号长度有误", "max_length": "手机号长度有误",
                                             "required": "手机号不能为空"})
    image_code_id = forms.UUIDField(error_messages={"required": "图片UUID不能为空"})
    text = forms.CharField(max_length=4, min_length=4,
                           error_messages={"min_length": "图片验证码长度有误", "max_length": "图片验证码长度有误",
                                           "required": "图片验证码不能为空"})
    route_id = forms.IntegerField(error_messages={"required":"不能为空"})
    # Cleaning and validating fields that depend on each other
    def clean(self):
        cleaned_data = super().clean()
        # 1、
        image_uuid = cleaned_data.get("image_code_id")
        image_text = cleaned_data.get("text")
        mobile_num = cleaned_data.get("mobile")
        route_id = cleaned_data.get('route_id')
        #print(route_id)
        # 2、

        if route_id == 1 and Users.objects.filter(mobile=mobile_num).count():
            raise forms.ValidationError("手机号已注册，请重新输入")
        if route_id == 0 and not Users.objects.filter(mobile=mobile_num).count():
            raise forms.ValidationError("手机号不存在，请重新输入")

        # 确保settings.py文件中有配置redis CACHE
        # Redis原生指令参考 http://redisdoc.com/index.html
        # Redis python客户端 方法参考 http://redis-py.readthedocs.io/en/latest/#indices-and-tables
        # 2、
        con_redis = get_redis_connection(alias='verify_codes')
        # 创建保存到redis中图片验证码的key
        img_key = "img_{}".format(image_uuid).encode('utf-8')

        # 取出图片验证码
        real_image_code_origin = con_redis.get(img_key)
        real_image_code = real_image_code_origin.decode('utf-8') if real_image_code_origin else None
        con_redis.delete(img_key)

        # 验证手机号
        if (not real_image_code) or (image_text.upper() != real_image_code):
            raise forms.ValidationError("图片验证失败")

        # 检查是否在60s内有发送记录
        sms_flag_fmt = "sms_flag_{}".format(mobile_num).encode('utf-8')
        sms_flag = con_redis.get(sms_flag_fmt)
        if sms_flag:
            raise forms.ValidationError("获取手机短信验证码过于频繁")


class CheckPasswordForm(forms.Form):
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
        查询数据库用户登录密码 验证通过 才可修改
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