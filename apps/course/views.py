import logging
from . import models
from django.http import Http404
from django.shortcuts import render
from django.views import View

logger = logging.getLogger('django')
# Create your views here.
def course_list(request):
    course = models.Course.objects.only('title', 'cover_url', 'teacher__positional_title').filter(is_delete=False)
    print(course)
    navId = 1
    return render(request, 'course/course.html', locals())
# def course(request):
#     """
#     course page
#     :param request:
#     :return:
#     """
#     return render(request,'course/course.html')

class CourseDetailView(View):
    """
    create course detail view
    route:/course/<int:course_id>/
    """
    def get(self, request, course_id):
        try:
            course = models.Course.objects.only('title', 'cover_url', 'video_url', 'profile', 'outline',
                                                'teacher__name', 'teacher__avatar_url',
                                                'teacher__positional_title', 'teacher__profile').\
                select_related('teacher').filter(is_delete=False, id=course_id).first()
            return render(request, 'course/course_detail.html', locals())
        except models.Course.DoesNotExist as e:
            logger.info("当前课程出现如下异常：\n{}".format(e))
            raise Http404("此课程不存在！")
# def course_detail(request):
#     return render(request,'course/course_detail.html')
