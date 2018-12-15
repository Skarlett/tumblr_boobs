"""
Tool that processes images after collection - per profile
"""
from . import processor as lib
import fire
import os
import shutil
import time
import logging

def timer(func):
    '''
    Why not wrap a generator, nothing could possibly go wrong *sarcasm*
    '''
    def wrapper(profile):
      generator = func(profile)
      while True:
        try:
          start = time.time()
          item = next(generator)
          yield item
          print("[{}] : {}".format(item, time.time()-start))
        except StopIteration:
          break
    return wrapper

def main(profile, trash=None, stopwatch=False):
  assert os.path.isdir(profile)
  mgr = lib.Engine()
  processing = timer(mgr.process) if stopwatch else mgr.process

  for fp, result in processing(profile):
    if not result:
      if not trash:
        os.remove(fp)
      else:
        trash_loc = os.path.join(trash, '/'.join(profile.split('/')[:-1]))
        if not os.path.isdir(trash_loc):
          os.makedirs(trash_loc)
        shutil.copy(fp, os.path.join(trash_loc, fp))

if __name__ == '__main__':
  try:
    fire.Fire(main)
    exit(0)
  except Exception as e:
    logging.exception("Failed {}".format(e.__class__.__name__))
    exit(1)
