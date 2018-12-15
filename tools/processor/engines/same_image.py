from . import __init__
from PIL import Image
import os

USE = True

class Prepectual_hash(__init__.Engine):
  """
  Checks if photos are visually similar (Not if they're the same hash)
  """
  accepts = ["image/png", 'image/jpeg']

  def process(self, profile_path):
    hash_buffer = set()
    for root, dir, files in os.walk(profile_path):
      for f in files:
        path = os.path.join(root, f)
        if self.compat(path):
          phash = __init__.lib.imagehash.dhash(Image.open(path)).hash
          yield path, phash not in hash_buffer
          hash_buffer.add(phash)

def setup(parent):
    Prepectual_hash.setup(parent)

