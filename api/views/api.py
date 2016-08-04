from rest_framework.response import Response
from rest_framework.decorators import api_view

from core.templatetags.renderer import markdown


@api_view(['GET'])
def RenderMarkdown(request):
    """
        Render Markdown
    """
    if request.method == 'GET':
        return Response(markdown(request.GET['text']))
