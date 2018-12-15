from .cfg import *
from .exc import *
from .utils import pprint
import pytumblr as api
import time
import os
import json


class RotatedTumblrRestClient(api.TumblrRestClient):
    def __init__(self, db, keys):
        self.db = db
        self.dlimit = CONFIG_FILE.TLIMIT
        self.reset = CONFIG_FILE.RESET
        self.hlimit = CONFIG_FILE.HLIMIT
        self.save_limit = CONFIG_FILE.SAVECNT

        self.consumer_key = keys[0]
        self.save_counter = 0

        api.TumblrRestClient.__init__(self, *keys)

    @property
    def dcnt(self):
        return self.db._data[self.consumer_key]['dcnt']

    @property
    def dts(self):
        return self.db._data[self.consumer_key]['dts']

    @property
    def hcnt(self):
        return self.db._data[self.consumer_key]['hcnt']

    @property
    def hts(self):
        return self.db._data[self.consumer_key]['hts']

    def is_ready(self):
        return self.hlimit > self.hcnt and self.dlimit > self.dcnt + self.hcnt

    def kill(self):
        self.db._data[self.consumer_key]['hcnt'] = self.hlimit
        self.db._data[self.consumer_key]['dcnt'] = self.dlimit

    def time_check(self):
        if self.hts + 60 * 60 >= time.time():
            self.db._data[self.consumer_key]['dcnt'] += self.db._data[self.consumer_key]['hcnt']
            self.db._data[self.consumer_key]['hts'] = time.time()
            self.db._data[self.consumer_key]['hcnt'] = 0

        if self.dts + self.reset >= time.time():
            self.db._data[self.consumer_key]['dcnt'] = 0
            self.db._data[self.consumer_key]['dts'] = time.time()


    def send_api_request(self, method, url, params={}, valid_parameters=[], needs_api_key=False):
        if self.save_counter >= self.save_limit:
            self.save_counter = 0
            self.db.save()
        else:
            self.save_counter += 1

        self.time_check()
        if not self.dcnt + self.hcnt > self.dlimit or not self.db._raise:
            if not self.hcnt > self.hlimit or not self.db._raise:
                # if DEBUGGING:
                    # print(method, url, params, needs_api_key)

                resp = api.TumblrRestClient.send_api_request(
                    self, method, url,
                    params, valid_parameters, needs_api_key
                )

                if resp:
                    self.db._data[self.consumer_key]['hcnt'] += 1
                    return resp

            else:
                if self.db._raise:
                    raise HourLimitCap('Reached hour limit')
        else:
            if self.db._raise:
                raise DayLimitCap('Reached day limit')


class JSONAPIrotator:
    '''
    Saves all API keys in a json loadable format to
    create multiple instances of clients with different api keys

    '''

    FP = CONFIG_FILE.DB
    Client_Klass = RotatedTumblrRestClient

    def __init__(self, client_class=None):
        self.clients = set()
        self.client_cls = client_class or self.Client_Klass
        self._raise = True

        if not os.path.isfile(self.FP):
            with open(self.FP, 'w') as fd:
                json.dump({}, fd)
        else:
            with open(self.FP) as fd:
                self._data = json.load(fd)

        for key in self._data.keys():
          client = self.client_cls(self, self._data[key]['keys'])
          self.clients.add(client)


    def save(self):
        for x in self.clients:
          x.time_check()

        with open(self.FP, 'w') as fd:
            json.dump(self._data, fd)

    def requests_used(self):
        t = 0
        for _, v in self._data.items():
            t += v['dcnt'] + v['hcnt']
        return t

    def requests_left_today(self):
        t = 0
        for _, v in self._data.items():
            t += CONFIG_FILE.TLIMIT - v['dcnt'] - v['hcnt']
        return t

    def requests_left_inhour(self):
        t = 0
        for _, v in self._data.items():
            t += CONFIG_FILE.HLIMIT - v['hcnt']
        return t

    def add_key(self, consumer_key, consumer_secret, oauth_token, oauth_secret):
        self._data[consumer_key] = {
            'dts': time.time(),
            'hts': time.time(),
            'dcnt': 0,
            'hcnt': 0,
            'keys': [consumer_key, consumer_secret, oauth_token, oauth_secret]
        }
        return "Updated key"

    def remove_key(self, consumer_key):
        self._data.pop(consumer_key)
        return "Removed key"

    def no_raise(self):
        self._raise = False
        return "Api limits turned off...", False

    def list_keys(self):
        data = '\n\t\t'.join(k for k in self._data.keys())
        return '''
        Listing Keys...
                {}

        Total Left per 24h: {}
        Total Left per 1h: {}
        '''.format(data, self.requests_left_today(), self.requests_left_inhour()), True

    def feed_client(self):
        self.save()

        for x in self.clients:
            if x.is_ready():
                return x

        if self._raise:
            raise NoKeysInDatabase('No keys found in database to return')
        else:
            return list(self.clients)[0]
