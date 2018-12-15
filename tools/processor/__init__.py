from . import exts

class Engine:
  def __init__(self):
    self.engine_modules = exts.Extension(self, 'engines')
    self.engines = set()

    if not self.engine_modules.loaded:
      self.engine_modules.load_ext()

  def process(self, profile_path):
    for engine in self.engines:
      yield engine.process(profile_path)
