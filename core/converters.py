from django.urls.converters import IntConverter, StringConverter


class FourDigitYearConverter(IntConverter):
    regex = "[0-9]{4}"

    def to_url(self, value):
        return str(value).zfill(4)


class TwoDigitMonthConverter(IntConverter):
    regex = "[0-9]{2}"

    def to_url(self, value):
        return str(value).zfill(2)


class BooleanStringConverter:
    """Converter whose regex match either True or False."""

    regex = r"(True)|(False)"

    def to_python(self, value):
        return str(value) == "True"

    def to_url(self, value):
        return str(value)


class ResultConverter(StringConverter):
    """Converter whose regex match either "success" or "failure"."""

    regex = "(success|failure)"
