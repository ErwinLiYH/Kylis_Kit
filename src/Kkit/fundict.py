class AmbiguityError(Exception):
    """
    Exception raised for ambiguity error.
    """
    pass

class NoneDict(dict):
    """
    A dict that returns None for missing keys.

    Example:

    ```python
    from Kkit import fundict
    a = fundict.NoneDict({"a":1, "b":2})
    a["c"] # None
    ```
    """
    def __init__(self, *args, **kwargs):
        super(NoneDict, self).__init__(*args, **kwargs)
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = NoneDict(value)

    def __getitem__(self, key):
        return super(NoneDict, self).get(key, None)


class AbbrDict(dict):
    """
    A dict that returns the value of the key that starts with the input key.

    Example:

    ```python
    from Kkit import fundict
    a = fundict.AbbrDict({"abxx":1, "acxx":2, "adxx":{"bcxx": 10, "bdxx":20}})
    a["a"]        # raise AmbiguityError
    a["ab"]       # 1
    a["ac"]       # 2
    a["ad"]["bc"] # 10
    a["ad"]["bd"] # 20
    a["c"]        # raise KeyError
    ```
    """
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
            # res = AbbrDict_content(maybe[0], key, super(AbbrDict, self).get(maybe[0], None))
            return super(AbbrDict, self).get(maybe[0], None)
        else:
            error_str = "get ambiguity with %s: "%key+" ".join(maybe)
            raise AmbiguityError(error_str)