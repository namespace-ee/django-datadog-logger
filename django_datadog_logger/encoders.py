from django.core.serializers.json import DjangoJSONEncoder


class SafeJsonEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super(SafeJsonEncoder, self).default(o)
        except TypeError as e:
            return str(e)
