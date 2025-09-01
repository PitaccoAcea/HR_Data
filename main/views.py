from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def home(request):
    #return HttpResponse("HR_Data è online ✅")
    return render(request, "main/home.html")