# Image utils

from io import BytesIO
from PIL import Image, ExifTags
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

def exif_auto_rotate(image):
    for orientation in ExifTags.TAGS.keys() :
        if ExifTags.TAGS[orientation]=='Orientation' : break
    exif=dict(image._getexif().items())

    if   exif[orientation] == 3 :
        image=image.rotate(180, expand=True)
    elif exif[orientation] == 6 :
        image=image.rotate(270, expand=True)
    elif exif[orientation] == 8 :
        image=image.rotate(90, expand=True)

    return image
