from django.shortcuts import render
import subprocess
from django.http import HttpResponse


# Create your views here.
def index(request):
    # list_path = '/Users/kid.wang/Desktop/django/mysite/App01/static'
    # print(__file__)
    # result = subprocess.run(['ls', list_path], stdout=subprocess.PIPE, text=True)
    # return render(request, 'index.html', {'items':result.stdout.split('\n')})
    return HttpResponse("unit_process_check=OK")