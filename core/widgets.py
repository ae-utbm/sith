from django import forms
from django.utils.safestring import mark_safe

class ChoiceWithOtherRenderer(forms.RadioSelect.renderer):
    """RadioFieldRenderer that renders its last choice with a placeholder."""
    def __init__(self, *args, **kwargs):
        super(ChoiceWithOtherRenderer, self).__init__(*args, **kwargs)
        self.choices, self.other = self.choices[:-1], self.choices[-1]

    def __iter__(self):
        for input in super(ChoiceWithOtherRenderer, self).__iter__():
            yield input
        id = '%s_%s' % (self.attrs['id'], self.other[0]) if 'id' in self.attrs else ''
        label_for = ' for="%s"' % id if id else ''
        checked = '' if not self.other[0] == self.value else 'checked="true" '
        yield '<label%s><input type="radio" id="%s" value="%s" name="%s" %s/> %s</label> %%s' % (
            label_for, id, self.other[0], self.name, checked, self.other[1])

class ChoiceWithOtherWidget(forms.MultiWidget):
    """MultiWidget for use with ChoiceWithOtherField."""
    def __init__(self, choices):
        widgets = [
            forms.RadioSelect(choices=choices, renderer=ChoiceWithOtherRenderer),
            forms.TextInput
        ]
        super(ChoiceWithOtherWidget, self).__init__(widgets)

    def decompress(self, value):
        if not value:
            return [None, None]
        return value

    def format_output(self, rendered_widgets):
        """Format the output by substituting the "other" choice into the first widget."""
        return rendered_widgets[0] % rendered_widgets[1]

class ChoiceWithOtherField(forms.MultiValueField):
    """
    ChoiceField with an option for a user-submitted "other" value.

    The last item in the choices array passed to __init__ is expected to be a choice for "other". This field's
    cleaned data is a tuple consisting of the choice the user made, and the "other" field typed in if the choice
    made was the last one.

    >>> class AgeForm(forms.Form):
    ...     age = ChoiceWithOtherField(choices=[
    ...         (0, '15-29'),
    ...         (1, '30-44'),
    ...         (2, '45-60'),
    ...         (3, 'Other, please specify:')
    ...     ])
    ...
    >>> # rendered as a RadioSelect choice field whose last choice has a text input
    ... print AgeForm()['age']
    <ul>
    <li><label for="id_age_0_0"><input type="radio" id="id_age_0_0" value="0" name="age_0" /> 15-29</label></li>
    <li><label for="id_age_0_1"><input type="radio" id="id_age_0_1" value="1" name="age_0" /> 30-44</label></li>
    <li><label for="id_age_0_2"><input type="radio" id="id_age_0_2" value="2" name="age_0" /> 45-60</label></li>
    <li><label for="id_age_0_3"><input type="radio" id="id_age_0_3" value="3" name="age_0" /> Other, please \
specify:</label> <input type="text" name="age_1" id="id_age_1" /></li>
    </ul>
    >>> form = AgeForm({'age_0': 2})
    >>> form.is_valid()
    True
    >>> form.cleaned_data
    {'age': (u'2', u'')}
    >>> form = AgeForm({'age_0': 3, 'age_1': 'I am 10 years old'})
    >>> form.is_valid()
    True
    >>> form.cleaned_data
    {'age': (u'3', u'I am 10 years old')}
    >>> form = AgeForm({'age_0': 1, 'age_1': 'This is bogus text which is ignored since I didn\\'t pick "other"'})
    >>> form.is_valid()
    True
    >>> form.cleaned_data
    {'age': (u'1', u'')}
    """
    def __init__(self, *args, **kwargs):
        fields = [
            forms.ChoiceField(widget=forms.RadioSelect(renderer=ChoiceWithOtherRenderer), *args, **kwargs),
            forms.CharField(required=False)
        ]
        widget = ChoiceWithOtherWidget(choices=kwargs['choices'])
        kwargs.pop('choices')
        self._was_required = kwargs.pop('required', True)
        kwargs['required'] = False
        super(ChoiceWithOtherField, self).__init__(widget=widget, fields=fields, *args, **kwargs)

    def compress(self, value):
        if self._was_required and not value or value[0] in (None, ''):
            raise forms.ValidationError(self.error_messages['required'])
        if not value:
            return [None, u'']
        return (value[0], value[1] if value[0] == self.fields[0].choices[-1][0] else u'')