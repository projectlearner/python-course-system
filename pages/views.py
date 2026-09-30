from django.http import HttpResponse

def hello_page(request):
    return HttpResponse("Hello World!")
