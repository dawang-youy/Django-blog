from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def home_index(request):
    """
    index page
    :param request:
    :return:
    """
    return render(request,'../templates/news/index.html',context={})
    #return HttpResponse("hello Django!")
