from pathlib import Path

from django.core.exceptions import FieldError
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from PIL import Image

from core.utils import resize_image_explicit


class ResizedImageFieldFile(ImageFieldFile):
    def get_resized_dimensions(self, image: Image.Image) -> tuple[int, int]:
        """Get the dimensions of the resized image.

        If the width and height are given, they are used.
        If only one is given, the other is calculated to keep the same ratio.

        Returns:
            Tuple of width and height
        """
        width = self.field.width
        height = self.field.height
        if width is not None and height is not None:
            return self.field.width, self.field.height
        if width is None:
            width = int(image.width * height / image.height)
        elif height is None:
            height = int(image.height * width / image.width)
        return width, height

    def get_name(self) -> str:
        """Get the name of the resized image.

        If the field has a force_format attribute,
        the extension of the file will be changed to match it.
        Otherwise, the name is left unchanged.

        Raises:
            ValueError: If the image format is unknown
        """
        if not self.field.force_format:
            return self.name
        formats = {val: key for key, val in Image.registered_extensions().items()}
        new_format = self.field.force_format
        if new_format in formats:
            extension = formats[new_format]
        else:
            raise ValueError(f"Unknown format {new_format}")
        return str(Path(self.file.name).with_suffix(extension))

    def save(self, name, content, save=True):  # noqa FBT002
        content.file.seek(0)
        img = Image.open(content.file)
        width, height = self.get_resized_dimensions(img)
        img_format = self.field.force_format or img.format
        new_content = resize_image_explicit(img, (width, height), img_format)
        name = self.get_name()
        return super().save(name, new_content, save)


class ResizedImageField(models.ImageField):
    """A field that automatically resizes images to a given size.

    This field is useful for profile pictures or product icons, for example.

    The final size of the image is determined by the width and height parameters :

    - If both are given, the image will be resized
      to fit in a rectangle of width x height
    - If only one is given, the other will be calculated to keep the same ratio

    If the force_format parameter is given, the image will be converted to this format.

    Examples:
        To resize an image with a height of 100px, without changing the ratio,
        and a format of WEBP :

        ```python
        class Product(models.Model):
            icon = ResizedImageField(height=100, force_format="WEBP")
        ```

        To explicitly resize an image to 100x100px (but possibly change the ratio) :

        ```python
        class Product(models.Model):
            icon = ResizedImageField(width=100, height=100)
        ```

    Raises:
        FieldError: If neither width nor height is given

    Args:
        width: If given, the width of the resized image
        height: If given, the height of the resized image
        force_format: If given, the image will be converted to this format
    """

    attr_class = ResizedImageFieldFile

    def __init__(
        self,
        width: int | None = None,
        height: int | None = None,
        force_format: str | None = None,
        **kwargs,
    ):
        if width is None and height is None:
            raise FieldError(
                f"{self.__class__.__name__} requires "
                "width, height or both, but got neither"
            )
        self.width = width
        self.height = height
        self.force_format = force_format
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.width is not None:
            kwargs["width"] = self.width
        if self.height is not None:
            kwargs["height"] = self.height
        kwargs["force_format"] = self.force_format
        return name, path, args, kwargs
