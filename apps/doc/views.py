import requests
import logging
import urllib3

from django.shortcuts import render
from django.http import FileResponse, Http404
from django.utils.encoding import escape_uri_path
from django.views import View
from django.conf import settings

from .models import Doc

# 导入日志器
logger = logging.getLogger('django')

# Create your views here.
def doc_index(request):
    """
    download doc
    :param request:
    :return:
    """
    docs = Doc.objects.defer('author', 'create_time', 'update_time', 'is_delete').filter(is_delete=False)
    navId = 2
    return render(request, 'doc/docDownload.html', locals())


class DocDownload(View):
    """
    create doc download view
    route:/docs/<int:doc_id>/
    """
    def get(self, request, doc_id):
        doc = Doc.objects.only('file_url').filter(is_delete=False, id=doc_id).first()
        if doc:
            doc_url = doc.file_url
            doc_url = settings.SITE_DOMAIN_PORT + doc_url if not doc_url.startswith('http') else doc_url
            doc_name = doc.title
            try:
                res = FileResponse(requests.get(doc_url, stream=True))#stream 参数 第一次请求不会下载 优化
                # 仅测试的话可以这样子设置
                # res = FileResponse(open(doc.file_url, 'rb'))
            except Exception as e:
                logger.info("获取文档内容出现异常：\n{}".format(e))
                raise Http404("文档下载异常！")

            ex_name = doc_url.split('.')[-1]
            # https://stackoverflow.com/questions/23714383/what-are-all-the-possible-values-for-http-content-type-header
            # http://www.iana.org/assignments/media-types/media-types.xhtml#image
            if not ex_name:
                raise Http404("文档url异常！")
            else:
                ex_name = ex_name.lower()

            if ex_name == "pdf":
                res["Content-type"] = "application/pdf"
            elif ex_name == "zip":
                res["Content-type"] = "application/zip"
            elif ex_name == "doc":
                res["Content-type"] = "application/msword"
            elif ex_name == "xls":
                res["Content-type"] = "application/vnd.ms-excel"
            elif ex_name == "docx":
                res["Content-type"] = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif ex_name == "ppt":
                res["Content-type"] = "application/vnd.ms-powerpoint"
            elif ex_name == "pptx":
                res["Content-type"] = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

            else:
                raise Http404("文档格式不正确！")
            final_filename = doc.title + '.'+ ex_name
            #http://192.168.192.128:8888/group1/M00/00/00/wKjAgFxa5NqAM0x8ALVDjXyBkGA890.pdf
            # doc_filename = escape_uri_path(doc_url.split('/')[-1])
            doc_filename = escape_uri_path(final_filename)
            # 设置为inline，会直接打开 attachment 不打开 提示下载
            # res["Content-Disposition"] = "inline; filename={}".format(doc_url.split('/')[-1])
            res["Content-Disposition"] = "attachment; filename*=UTF-8''{}".format(doc_filename)
            return res

        else:
            raise Http404("文档不存在！")

# def doc_down(request):
#     """
#     docDownload page
#         :param request:
#         :return:
#     """
#     return render(request,'doc/docDownload.html')
