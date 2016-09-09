from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import StaticHTMLRenderer
from rest_framework.views import APIView

from core.templatetags.renderer import markdown


@api_view(['GET'])
@renderer_classes((StaticHTMLRenderer,))
def RenderMarkdown(request):
    """
        Render Markdown
    """
    try:
        data = markdown(request.GET['text'])
    except:
        data = 'Error'
    return Response(data)

