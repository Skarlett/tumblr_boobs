from . import __init__
from PIL import Image
import os

USE = True

class SizeCheck(__init__.Engine):
    """ checks image is of size """
    accepts = ["image/png", 'image/jpeg']
    min_px = 200000

    def process(self, profile_path):
      for root, dir, files in os.walk(profile_path):
        for f in files:
          fp = os.path.join(root, f)
          if self.compat(fp):
            im = Image.open(fp)
            width, height = im.size
            im.close()
            yield fp, width*height >= self.min_px

def setup(parent):
    SizeCheck.setup(parent)

