from django.shortcuts import render

def render_markdown(request):
    return render(request, 'core/api/markdown.html', context={'text': request.GET['text']})
