def my_decorator(func):
    def wrapper(request,*args,**kwargs):
        print('这是定义的装饰器')
        print('判断用户是否登录，是否有相关权限')
        print(args,kwargs)#(<WSGIRequest: GET '/admin/index/'>,) {}
        return func(request,*args,**kwargs)
    return wrapper