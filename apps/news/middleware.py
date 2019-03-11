from django.http import HttpResponse, HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin


def my_middleware1(get_response):
    print("my_middleware1 init called.")

    def middleware(request):
        print("my_middleware1 called before request.")
        response = get_response(request)
        print("my_middleware1 called after request.")
        return response
    return middleware


def my_middleware2(get_response):
    print("my_middleware2 init called.")

    def middleware(request):
        print("my_middleware2 called before request.")
        response = get_response(request)
        print("my_middleware2 called after request.")

        return response

    return middleware


class MyMiddleware1(MiddlewareMixin):
    def process_request(self, request):
        print('M1.request')
        # return HttpResponse("return from process_request of MyMiddleware1...")
        # user_agent = request.META.get("HTTP_USER_AGENT")
        # if not user_agent or not user_agent.lower().startswith("mozilla"):    # type: str
        #     return HttpResponseForbidden("爬虫滚开...")

    def process_view(self, request, callback, callback_args, callback_kwargs):
        print("M1.process_view")
        # return callback(request, callback_args, callback_kwargs)

    def process_response(self, request, response):
        print('M1.response')
        return response

    def process_exception(self, request, exception):
        print('M1的process_exception')


class MyMiddleware2(MiddlewareMixin):
    def process_request(self, request):
        print('M2.request')

    def process_view(self, request, callback, callback_args, callback_kwargs):
        print("M2.process_view")
        # return HttpResponse("process_view...")

    def process_response(self, request, response):
        print('M2.response')
        return response

    def process_exception(self, request, exception):
        print('M2的process_exception')
