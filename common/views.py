from django.shortcuts import render

def service_paused(request):
    return render(request, 'service_paused.html') 