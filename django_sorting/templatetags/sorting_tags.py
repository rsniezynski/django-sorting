from django import template
from django.http import Http404
from django.conf import settings

register = template.Library()

DEFAULT_SORT_UP = getattr(settings, 'DEFAULT_SORT_UP' , '&uarr;')
DEFAULT_SORT_DOWN = getattr(settings, 'DEFAULT_SORT_DOWN' , '&darr;')
INVALID_FIELD_RAISES_404 = getattr(settings, 
        'SORTING_INVALID_FIELD_RAISES_404' , False)

sort_directions = {
    'asc': {'icon':DEFAULT_SORT_UP, 'inverse': 'desc'}, 
    'desc': {'icon':DEFAULT_SORT_DOWN, 'inverse': 'asc'}, 
    '': {'icon':DEFAULT_SORT_DOWN, 'inverse': 'asc'}, 
}

def anchor(parser, token):
    """
    Parses a tag that's supposed to be in this format: {% anchor field title %}    
    """
    bits = [b.strip('"\'') for b in token.split_contents()]
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "anchor tag takes at least 1 argument"
    try:
        title = bits[2]
    except IndexError:
        title = bits[1].capitalize()
    name = len(bits) == 4 and bits[3].strip() or None
    return SortAnchorNode(bits[1].strip(), title.strip(), name)
    

class SortAnchorNode(template.Node):
    """
    Renders an <a> HTML tag with a link which href attribute 
    includes the field on which we sort and the direction.
    and adds an up or down arrow if the field is the one 
    currently being sorted on.

    Eg.
        {% anchor name Name %} generates
        <a href="/the/current/path/?sort=name" title="Name">Name</a>

    """
    def __init__(self, field, title, name=None):
        self.field = field
        self.title = title
        self.name = name

    def render(self, context):
        request = context['request']
        getvars = request.GET.copy()
        if self.name:
            field_var = "sort_" + self.name
            dir_var = "dir_" + self.name
        else:
            field_var = "sort"
            dir_var = "dir"
        sort_default = field_var + "_default"
        if field_var in getvars:
            sortby = getvars[field_var]
            del getvars[field_var]
        else:
            sortby = ''
        if dir_var in getvars:
            sortdir = getvars[dir_var]
            del getvars[dir_var]
        else:
            sortdir = ''
        if sortby == self.field:
            getvars[dir_var] = sort_directions[sortdir]['inverse']
            icon = sort_directions[sortdir]['icon']
        elif not sortby and sort_default in context:
            sort_default_order = context[sort_default]
            sort_default_field = sort_default_order.lstrip("-")
            if self.field == sort_default_field:
                sortdir = "desc" if sort_default_order.startswith("-") else "asc"
                icon = sort_directions[sortdir]['icon']
                getvars[dir_var] = sort_directions[sortdir]['inverse']
            else:
                icon = ""


        else:
            icon = ''
        if len(getvars.keys()) > 0:
            urlappend = "&%s" % getvars.urlencode()
        else:
            urlappend = ''
        if icon:
            title = "%s %s" % (self.title, icon)
        else:
            title = self.title


        url = '%s?%s=%s%s' % (request.path, field_var, self.field, urlappend)
        return '<a href="%s" title="%s">%s</a>' % (url, self.title, title)


def autosort(parser, token):
    bits = [b.strip('"\'') for b in token.split_contents()]
    if len(bits) > 3:
        raise template.TemplateSyntaxError, "autosort tag takes exactly at most two arguments"
    return SortedDataNode(bits[1], bits[2] if len(bits) > 2 else None)

class SortedDataNode(template.Node):
    """
    Automatically sort a queryset with {% autosort queryset %}
    """
    def __init__(self, queryset_var, name=None):
        self.queryset_var = template.Variable(queryset_var)
        self.name = name

    def render(self, context):
        key = self.queryset_var.var
        value = self.queryset_var.resolve(context)
        order_by = context['request'].get_field(self.name)
        if len(order_by) > 1:
            try:
                context[key] = value.order_by(order_by)
            except template.TemplateSyntaxError:
                if INVALID_FIELD_RAISES_404:
                    raise Http404('Invalid field sorting. If DEBUG were set to ' +
                    'False, an HTTP 404 page would have been shown instead.')
                context[key] = value
        else:
            context[key] = value

        return ''

anchor = register.tag(anchor)
autosort = register.tag(autosort)

