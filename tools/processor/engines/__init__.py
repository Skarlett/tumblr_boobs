import magic
from . import lib

class Engine:
  accepts = []
  accepts_all = False

  def compat(self, filepath):
    return self.accepts_all or magic.from_file(filepath, mime=True) in self.accepts

  def process(self, profile_path):
    return False

  @classmethod
  def setup(cls, parent):
    self = cls()
    parent.engines.add(self)
    return self in parent.engines
