# credit: http://djangosnippets.org/snippets/2841/
# this allows us to loop through a checkbox group in a template just like a
# radioselect. 
from itertools import groupby, chain

from django import forms
from django.conf import settings
from django.forms import Widget
from django.forms.widgets import SubWidget, SelectMultiple
from django.forms.util import flatatt
from django.utils.html import conditional_escape

# force_text and StrAndUnicode are deprecated as of django 1.5
# replaced with the following
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.safestring import mark_safe

class CheckboxInput(SubWidget):
    """
    An object used by CheckboxRenderer that represents a single
    <input type='checkbox'>.
    """
    def __init__(self, name, value, attrs, choice, index):
        self.name, self.value = name, value
        self.attrs = attrs
        self.choice_value = force_text(choice[0])
        self.choice_label = force_text(choice[1])
        self.index = index

    def __str__(self):
        return self.render()

    def render(self, name=None, value=None, attrs=None, choices=()):
        name = name or self.name
        value = value or self.value
        attrs = attrs or self.attrs

        if 'id' in self.attrs:
            label_for = ' for="%s_%s"' % (self.attrs['id'], self.index)
        else:
            label_for = ''
        choice_label = conditional_escape(force_text(self.choice_label))
        return mark_safe(u'<label%s>%s %s</label>' % (label_for, self.tag(), choice_label))

    def is_checked(self):
        return self.choice_value in self.value

    def tag(self):
        if 'id' in self.attrs:
            self.attrs['id'] = '%s_%s' % (self.attrs['id'], self.index)
        final_attrs = dict(self.attrs, type='checkbox', name=self.name, value=self.choice_value)
        if self.is_checked():
            final_attrs['checked'] = 'checked'
        return mark_safe(u'<input%s />' % flatatt(final_attrs))

@python_2_unicode_compatible
class CheckboxRenderer(object):
    def __init__(self, name, value, attrs, choices):
        self.name, self.value, self.attrs = name, value, attrs
        self.choices = choices

    def __iter__(self):
        for i, choice in enumerate(self.choices):
            yield CheckboxInput(self.name, self.value, self.attrs.copy(), choice, i)

    def __getitem__(self, idx):
        choice = self.choices[idx] # Let the IndexError propogate
        return CheckboxInput(self.name, self.value, self.attrs.copy(), choice, idx)

    def __str__(self):
        return self.render()

    def render(self):
        output = []
        # init
        self.i = 0
        output.append("<ul>")


        # recursively build up the list of nested checkboxinput items
        def markup(choices, output, i):
            for choice in choices:
                # this choice has a sublist of choices
                if isinstance(choice[1], (list, tuple)):
                    # build up the heading for the sublist
                    group_label = conditional_escape(force_text(choice[0]))
                    output.append(u"<li><span class='checkbox-group-heading'>%s</span>" % (group_label))
                    output.append(u'<ul class="checkbox-group">')
                    # now build the list of checkboxinputs
                    i = markup(choice[1], output, i)
                    # close off the sublist
                    output.append(u"</ul></li>")
                else:
                    output.append(u"<li>%s</li>" % (CheckboxInput(self.name, self.value, self.attrs.copy(), choice, i)))
                    i += 1

            return i

        markup(self.choices, output, 0)
        output.append("</ul>")
        return mark_safe("\n".join(output))

class CheckboxSelectMultiple(SelectMultiple):
    """
    Checkbox multi select field that enables iteration of each checkbox
    Similar to django.forms.widgets.RadioSelect
    """
    renderer = CheckboxRenderer

    def __init__(self, *args, **kwargs):
        # Override the default renderer if we were passed one.
        renderer = kwargs.pop('renderer', None)
        if renderer:
            self.renderer = renderer
        super(CheckboxSelectMultiple, self).__init__(*args, **kwargs)

    def subwidgets(self, name, value, attrs=None, choices=()):
        for widget in self.get_renderer(name, value, attrs, choices):
            yield widget

    def get_renderer(self, name, value, attrs=None, choices=()):
        """Returns an instance of the renderer."""
        if value is None: value = ''
        str_values = set([force_text(v) for v in value]) # Normalize to string.
        if attrs is None:
            attrs = {}
        if 'id' not in attrs:
            attrs['id'] = name
        final_attrs = self.build_attrs(attrs)
        choices = list(chain(self.choices, choices))

        # For testing purposes, I replaced the line
        #   return self.renderer(name, str_values, final_attrs, choices)
        # with the following to avoid "CheckboxRenderer object not callable" error
        if settings.TEST:
            self.renderer.name = name
            self.renderer.str_values = str_values
            self.renderer.final_attrs = final_attrs
            self.renderer.choices = choices
            return self.renderer
        else:
            return self.renderer(name, str_values, final_attrs, choices)


    def render(self, name, value, attrs=None, choices=()):
        return self.get_renderer(name, value, attrs, choices).render()

    def id_for_label(self, id_):
        if id_:
            id_ += '_0'
        return id_
