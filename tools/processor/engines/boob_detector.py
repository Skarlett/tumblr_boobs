import os
from nude import Nude
from . import __init__

USE = True

class Boob_detector(__init__.Engine):
    """
    uses nudity AI engine
    """
    accepts = ['image/png', 'image/jpeg']

    def process(self, profile_path):
      for root, dirs, files in os.walk(profile_path):
        for f in files:
          fp = os.path.join(root, f)
          if self.compat(fp):
            ai = Nude(fp)
            ai.parse()

            yield fp, ai.result

def setup(parent):
    Boob_detector.setup(parent)


