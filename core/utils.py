# Image utils

from io import BytesIO
from PIL import Image
# from exceptions import IOError
import PIL
from django.core.files.base import ContentFile

def scale_dimension(width, height, long_edge):
    if width > height:
        ratio = long_edge * 1. / width
    else:
        ratio = long_edge * 1. / height
    return int(width * ratio), int(height * ratio)

def resize_image(im, edge, format):
    (w, h) = im.size
    (width, height) = scale_dimension(w, h, long_edge=edge)
    content = BytesIO()
    im = im.resize((width, height), PIL.Image.ANTIALIAS)
    try:
        im.save(fp=content, format=format.upper(), quality=90, optimize=True, progressive=True)
    except IOError:
        PIL.ImageFile.MAXBLOCK = im.size[0] * im.size[1]
        im.save(fp=content, format=format.upper(), quality=90, optimize=True, progressive=True)
    return ContentFile(content.getvalue())

