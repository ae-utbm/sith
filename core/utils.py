# Image utils

from io import BytesIO
from PIL import Image

def scale_dimension(width, height, long_edge):
    if width > height:
        ratio = long_edge * 1. / width
    else:
        ratio = long_edge * 1. / height
    return int(width * ratio), int(height * ratio)

def resize_image(im, edge, format): # TODO move that into a utils file
    from django.core.files.base import ContentFile
    (w, h) = im.size
    (width, height) = scale_dimension(w, h, long_edge=edge)
    content = BytesIO()
    im.resize((width, height), Image.ANTIALIAS).save(fp=content, format=format, dpi=[72, 72])
    return ContentFile(content.getvalue())

