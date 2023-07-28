from django.http import HttpResponse
from configuration.settings import VERSION


def index(request):
    return HttpResponse("Penny Pusher (v" + VERSION + ")")
