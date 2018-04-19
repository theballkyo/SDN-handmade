class TextField:
    pass


class Model:
    # def __init__(self, **kwargs):
    #     pass

    @classmethod
    def init(cls, obj):
        _cls = cls()
        for o_key, o_value in obj.items():
            attr = _cls.__getattribute__(o_key)

            # Add
            setattr(_cls, o_key, o_value)

        return _cls
