#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version__ = '1.7.13'
__author__ = 'https://github.com/Skarlett'

##################
# Tumblr APIv2 Basic Util Scraper
import multiprocessing  # moar power
import threading
import queue
import sys
import time
import requests
import hashlib
from .scraper import *
from .db import JSONAPIrotator

pprint = lambda obj: print(json.dumps(obj, separators=[',', ':'], indent=4, sort_keys=True))
getusername = lambda: pwd.getpwuid(os.getuid())[0]
DEBUGGING = False


def download_media(pkg):
    url, to, bs = pkg
    if url:
        resp = requests.get(url)
        generator = resp.iter_content(bs)
        first_chunk = next(generator)
        file_hash = hashlib.md5(first_chunk).hexdigest()
        file_extension = url.split('.')[-1].lower()
        fp = os.path.join(to, '{}.{}'.format(file_hash, file_extension))

        if not os.path.isdir(os.path.split(fp)[0]):
          try:
            os.makedirs(os.path.split(fp)[0])
          except:
            pass

        if not os.path.isfile(fp):
            try:
              with open(fp, 'wb') as f:
                f.write(first_chunk)
                for chunk in generator:
                  f.write(chunk)
            except Exception as e:
                logging.warning('{} - {}'.format(url, str(e)))


class SetQueue(queue.Queue):
    def _init(self, maxsize):
      self.queue = set()

    def _put(self, item):
      self.queue.add(item)

    def _get(self):
      return self.queue.pop()


class Worker(threading.Thread):
    def __init__(self, parent, id, threads=CONFIG_FILE.DL_THREADS, chunksize=CONFIG_FILE.DL_SIZE):
      self.id = id
      self.closed = False
      self.parent = parent
      self.handles = threads
      self.chunksize = chunksize
      self.done = parent.running
      threading.Thread.__init__(self, daemon=True)

    def run(self):
      ''' Agent - This handles on per user'''
      with multiprocessing.Pool(processes=self.handles) as pool:
        try:
          while self.parent.running:
              while not self.parent.users.empty():
                user = self.parent.users.get(block=True)
                self.parent.remember.add(user)

                download_to = os.path.join(self.parent.directory, user.name)
                print("gathering <{}>".format(user.name))
                user.scrape()

                for user in user.shoutouts:
                  if not user in self.parent.remember:
                    self.parent.users.put(user)

                self.parent.users.task_done()

                if user.media and not user.ignore and len(user.media) >= user.minimum_media:
                  if not os.path.isdir(download_to):
                    try:
                      os.mkdir(download_to)
                    except:
                        pass
                print('[{}] Scraping {} <{}>'.format(self.id, user.name, len(user.media)))
                pool.map(download_media, [(str(url), str(download_to), self.chunksize) for url in user.media])

                if self.parent.user_limit > 0 and len(self.parent.remember) >= self.parent.user_limit:
                  break

        except KeyboardInterrupt:
          if not self.closed:
            pool.close()

      if not self.closed:
         pool.close()

      pool.join()

class Manager:
  def __init__(self, user_limit=0, output=None, agents=CONFIG_FILE.DL_AGENTS, workers=CONFIG_FILE.DL_THREADS):
      self.user_limit = user_limit
      self.users = SetQueue()
      self.directory = output or os.getcwd()
      self.remember = set()
      self._download_agents = agents
      self._dl_workers = workers
      self._spawned = False
      self._agents = set()
      self.running = True


  def read_cache(self, db, **kwargs):
      with open(os.path.join(self.directory, '.last_scrape.tscrape')) as f:
        for line in f:
          self.users.put_nowait(RestlessCrawler(self, line.strip(), db, **kwargs))

  def write_cache(self):
    fp = os.path.join(self.directory, '.last_scrape.tscrape')
    with open(fp, 'w') as f:
      while not self.users.empty():
        f.write('{}\n'.format(self.users.get_nowait().name))

  def spawn_agents(self):
    if not self._spawned:
      for id in range(self._download_agents):
        self._agents.add(Worker(self, id, threads=self._dl_workers))
      self._spawned = True

  def start(self, user, db, **kwargs):
    user = RestlessCrawler(self, user, db, **kwargs)

    fp = os.path.join(self.directory, '.last_scrape.tscrape')
    if os.path.isfile(fp):
      self.read_cache(db, **kwargs)

    self.users.put_nowait(user)
    self.spawn_agents()

    for agent in self._agents:
      agent.start()
    try:
      while self.running:
        if all(not(agent.is_alive()) for agent in self._agents):
          break
        # print(tuple(x.name for x in self.remember), self.users.qsize())
        time.sleep(2)
    except KeyboardInterrupt:
        print("exitting...")
        self.running = False
    self.write_cache()



class CLI:
        ''' this thing is stiff as hell '''

        HELP = """
     _______ 
    ( Boobs )
     ------- 
           o   ^__^
            o  (xx)\_______
               (__)\       )\/\\
                U  ||----w |
                   ||     ||

    tumblr scraper tool for APIv2 - crawls profiles pulling pictures and videos while scanning for more users
    usage: {fp} <args> <blog_name> 

    It should be noted this application is not retard-proof
    it probably wont work if you suffer from retardism,
    skiddism, aufucktism or all the above. P.S, your computer will blow up
    if you're a jew and use this application.

    DESC
    CMD <ARGUMENTS> | DEFAULT

      Use "None" if you'd like to query without comparing tags
      -t | --tags <tag1> <tag2> <tag3> | {tags_default}
    
      When a name gets found, use these tags
      -ct | --crawltags <tag1> <tag2> <tag3> | {tags_default}
      
      Crawling instructions
      -m  | --method source likes | reblog, source (Shoutouts), likes (Everything)) | reblog source
      
      Limits the amount of users this application may crawl. 0 = Infinite.
      -ul | --user-limit <int> | 0

      Maximum Retrieval of media
      -i | --img <int> | {img_default}
      -v | --vid <int> | {vid_default}
      
      point to target Directory
      -o | --out <dir> | {output_dir}
      
      Forces it not to download ROOT BLOG CONTENTS but instead
      iterates through them for crawl tags
      -x | --ignore | False
        
      Add API keyset for the application to use.
      --db-add <consumer-key> <consumer-secret> <oauth_token> <oauth_secret>

      Remove an API keyset from the database
      --db-del <consumer-key>

      List database keys
      --keys

      Only captures blogs marked with ...
      -a | --adult | False
      -n | --nsfw | False

      Fine Tuning settings
      --min-media     <int> | {min_data} =>
      --offset-images <int> | 0 => +20
      --offset-videos <int> | 0 => +20
      --min-likes-per <int> | 0 =>
      --min-followers <int> | 0 =>
      --min-posts     <int> | 0 =>
      -il | --ignore-api-limitations | False
      --throttle | auto limits requests   

      The amount of agents is the amount of account that can simultaneously be downloaded at once
      --agents <int> | {agents}
      The amount of agent handles is how many pieces of media can be downloaded simultaneously per agent
      --workers <int> | {agents_handles}
      
      Extra output
      --debug

      spawns help message.
      -h | --help

    """.format(
            fp=__file__ if __file__.count('/') < 2 else __file__.split('/')[-1],
            tags_default=RestlessCrawler.DEFAULT_TAGS,
            img_default=RestlessCrawler.DEFAULT_IMAGE_COUNT,
            vid_default=RestlessCrawler.DEFAULT_VIDEO_COUNT,
            min_data=RestlessCrawler.DEFAULT_MIN_MEDIA,
            output_dir=os.getcwd(),
            agents=CONFIG_FILE.DL_AGENTS,
            agents_handles=CONFIG_FILE.DL_THREADS
        )

        if len(sys.argv) == 1 or \
                '-h' in sys.argv or \
                '--help' in sys.argv:
            print(HELP)
            exit(2)

        GLOBAL_CMDS = (
            (('-ul', '--user-limit'), 'user_limit'),
            (('-o', '--out'), 'output'),
            (('--agents',), 'agents'),
            (('--workers',), 'workers'),
        )

        DB_CMDS = (
            (('--db-add',), 'add_key'),
            (('--db-del',), 'remove_key'),
        )

        DB_FLAGS = (
            (('--keys',), 'list_keys'),
            (('--ignore-api-limitations', '-il'), 'no_raise'),
            (('--throttle',), 'throttle')
        )

        CRAWL_CMDS = (
            (('-t', '--tags'), 'tags'),
            (('-ct', '--crawltags'), 'crawl_tags'),
            (('-i', '--img'), 'max_imgs'),
            (('-v', '--vid'), 'max_vids'),
            (('-m', '--method'), 'follow_instructions'),
            (('--min-media',), 'minimum_media'),
            (('--offset-images',), 'ioffset'),
            (('--offset-videos',), 'voffset',),
            (('--min-posts',), 'min_posts',),
            (('--min-followers',), 'min_followers',),
            (('--min-likes-per'),  'min_likes_post')
        )

        CRAWL_FLAGS = (
            (('-x', '--ignore'), 'ignore'),
            (('-a', '--adult'), 'adult'),
            (('-ns', '--nsfw'), 'nsfw')
        )

        @classmethod
        def find_value(cls, key_tuple, kill_on_last_arg=True):
            ret = []
            for key in key_tuple:
                if key in sys.argv:
                    collect = False
                    for i, part in enumerate(sys.argv):
                        if part == key:
                            collect = True
                        else:
                            if part.startswith('-') or (kill_on_last_arg and i + 1 == len(sys.argv)):
                                collect = False

                            elif collect:
                                if key in ('-ct', '-t', '--crawltags', '--tags'):
                                    if part.lower() == "none":
                                        part = ""
                                    else:
                                        part = part.replace('_', ' ')

                                ret.append(part)

                    ret = [x for x in ret if x and not x == 0]

                    if not key in ('-ct', '-t', '--crawltags', '--tags'):
                        if len(ret) > 1:
                            return ret

                        elif len(ret) == 1:
                            data = ret[0]
                            if data.isdigit():
                                return int(data)
                            return data

                        elif len(ret) == 0:
                            return None
                    else:
                        return ret

        @classmethod
        def interface(cls):
            global DEBUGGING
            # for keys, reference in cls.GLOBAL_CMDS:
            #   resp = cls.find_value(keys)
            db = JSONAPIrotator()

            g = {}  # global shit
            for keys, reference in cls.GLOBAL_CMDS:
                resp = cls.find_value(keys)
                if isinstance(resp, int):
                    g[reference] = resp
                elif resp:
                    g[reference] = resp

            for keys, reference in cls.DB_CMDS:
                resp = cls.find_value(keys, False)
                if resp:
                    if hasattr(db, reference):
                        ret = getattr(db, reference)(*tuple(resp))
                        print(ret)
                        db.save()
                        exit(0)
                    else:
                        raise ValueError('{} had no method {}'.format(db, reference))

            for keys, reference in cls.DB_FLAGS:
                for k in keys:
                    if k in sys.argv:
                        if hasattr(db, reference):
                            db.save()
                            ret, status = getattr(db, reference)()
                            print(ret)
                            if status:
                                exit(0)

                        else:
                            raise ValueError('{} had no method {}'.format(db, reference))

            kwargs = {}
            for keys, reference in cls.CRAWL_CMDS:
                resp = cls.find_value(keys)
                if isinstance(resp, int):
                    kwargs[reference] = resp
                elif resp:
                    kwargs[reference] = resp

            if 'tags' in kwargs and not 'crawl_tags' in kwargs and CONFIG_FILE.PASS_TAGS:
                kwargs['crawl_tags'] = kwargs['tags']

            for keys, reference in cls.CRAWL_FLAGS:
                for k in keys:
                    if k in sys.argv:
                        kwargs[reference] = True
                        break

            if '--debug' in sys.argv:
                DEBUGGING = True

            # user = RestlessCrawler(sys.argv[-1], db, **kwargs)
            # print(user.ignore)
            # if not any(i in kwargs for i in ('-x', '--ignore')) and user.ignore:
            #   user.ignore = False

            Manager(**g).start(sys.argv[-1], db, **kwargs)
            db.save()

