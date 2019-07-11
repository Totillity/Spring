import dataclasses
import json


def _serialize(obj: object):
    if dataclasses.is_dataclass(obj):
        d = {"<class>": obj.__class__.__name__}
        cls = obj.__class__
        field: dataclasses.Field
        # noinspection PyDataclass
        for field in dataclasses.fields(cls):
            if field.repr:
                d[field.name] = getattr(obj, field.name)
        return d
    else:
        return repr(obj)


def pretty_json(obj):
    return json.dumps(obj, indent='    ', default=_serialize)


def pretty(obj):
    # TODO  A python-like representation
    return pretty_json(obj)
