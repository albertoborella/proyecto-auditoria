from django.shortcuts import render

def home_empresa(request):
    return render(request, 'home-empresa.html')
