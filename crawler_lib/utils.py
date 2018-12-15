from .cfg import *
import json
import os

pprint = lambda obj: print(json.dumps(obj, separators=[',', ':'], indent=4, sort_keys=True))

class BlackList:
    ''' This is hackish - and i should probably find another way of implementing this, but fuck it'''
    _FP = CONFIG_FILE.BLACKLST
    ignore = set()

    if os.path.isfile(_FP):
        with open(_FP) as fd:
            for l in fd:
                data = l.strip()
                if data:
                    ignore.add(data)
    else:
        with open(_FP, 'w') as fd:
            fd.write('')

    @classmethod
    def save(cls):
        with open(CONFIG_FILE.BLACKLST, 'w') as fd:
            fd.write('\n'.join(cls.ignore))

    @classmethod
    def add(cls, user):
        cls.ignore.add(user)

    @classmethod
    def update(cls, iterable):
        cls.ignore.update(iterable)

    @classmethod
    def remove(cls, user):
        cls.ignore.remove(user)


