class AmbiguityError(Exception):
    pass

class NoneDict(dict):
    def __init__(self, *args, **kwargs):
        super(NoneDict, self).__init__(*args, **kwargs)
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = NoneDict(value)

    def __getitem__(self, key):
        return super(NoneDict, self).get(key, None)
    
class AbbrDict_content:
    def __init__(self, true_key, abbr_key, content):
        self.ture_key = true_key
        self.abbr_key = abbr_key
        self.content= content
    def __str__(self):
        return "_".join([self.ture_key, self.abbr_key, str(self.content)])
    def __repr__(self):
        return "_".join([self.ture_key, self.abbr_key, repr(self.content)])

class AbbrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AbbrDict, self).__init__(*args, **kwargs)
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = AbbrDict(value)
        self.__abbrdict_keys = list(super(AbbrDict, self).keys())
        for i in self.__abbrdict_keys:
            if isinstance(i, str)==False:
                raise TypeError("all keys of AbbrDict must be str")

    def __getitem__(self, key):
        keys = list(super(AbbrDict, self).keys())
        maybe = list(filter(lambda string: string.startswith(key), keys))
        if len(maybe)==0:
            raise KeyError("can't find key %s"%key)
        elif len(maybe)==1:
            res = AbbrDict_content(maybe[0], key, super(AbbrDict, self).get(maybe[0], None))
            return res
        else:
            error_str = "get ambiguity with %s: "%key+" ".join(maybe)
            raise AmbiguityError(error_str)