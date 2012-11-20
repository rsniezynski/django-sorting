def get_field(self, name=None):
    try:
        if name:
            field = self.REQUEST["sort_" + name]
        else:
            field = self.REQUEST['sort']
    except (KeyError, ValueError, TypeError):
        field = ''
    return (self.get_direction(name) == 'desc' and '-' or '') + field

def get_direction(self, name=None):
    try:
        if name:
            return self.REQUEST['dir_' + name]
        else:
            return self.REQUEST['dir']
    except (KeyError, ValueError, TypeError):
        return 'desc'

class SortingMiddleware(object):
    """
    Inserts a variable representing the field (with direction of sorting)
    onto the request object if it exists in either **GET** or **POST** 
    portions of the request.
    """
    def process_request(self, request):
        request.__class__.get_field = get_field
        request.__class__.get_direction = get_direction
