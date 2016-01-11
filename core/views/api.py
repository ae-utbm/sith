from core.templatetags.renderer import markdown
from django.http import HttpResponse

def render_markdown(request):
    return HttpResponse(markdown(request.GET['text']))
