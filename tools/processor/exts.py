import os
import logging

class Extension:
    ''' Dynamic object carrying for objects to hold extensions '''

    def __init__(self, parent, folder, load_func='setup', exclusions=[]):
        self.folder = folder
        self.parent = parent
        self.load_func = load_func
        self.loaded = set()
        self.available = list()
        self.exclusions = exclusions

    def find_files(self):
        for root, dirs, files in os.walk(os.path.join(os.path.dirname(__file__), self.folder)):
            for x in files:
                if not x.startswith('_') and x.endswith('.py') and x not in self.exclusions \
                        and not x.split('.', -1)[0] in self.exclusions:
                    yield x.split('.')[0]

            if not '__init__.py' in files:
                with open(os.path.join(root, '__init__.py'), 'w') as f:
                    f.write('pass')
            break

    def reload_setup_hooks(self):
        loaded = [x.__name__ for x in self.loaded]
        avail = [x.__name__ for x in self.available]
        for f in self.find_files():
            needs_containment = False
            if f in loaded + avail:
                mod = [x for x in self.loaded if x.__name__ == f][0]
            else:
                needs_containment = True
                mod = __import__(self.folder + '.' + f).__dict__[f]

            if hasattr(mod, 'USE'):
                if mod.USE:
                    if hasattr(mod, self.load_func):
                        try:
                            getattr(mod, self.load_func)(self.parent)
                        except Exception as e:
                            logging.exception(
                                mod.__name__ + ' Has failed to load due to [' + e.__class__.__name__ + '] Being raised.')
                    else:
                        logging.warning(mod.__name__ + ' Has no setup function. Ignoring...')
            else:
                logging.warning(mod.__name__ + ' Has no USE flag, ignoring...')

            if needs_containment:
                self.loaded.add(mod)

    def load_ext(self):
        ''' gimme moar stuff
        status protocol:
        0 = cant use
        1 = is using
        2 = can use

        '''
        fs = list(self.find_files())

        for mod in fs:
            try:
                _mod = __import__(self.folder + '.' + mod).__dict__[mod]
            except Exception as e:
                logging.exception(str(mod) + ' Has failed to load due to [' + e.__class__.__name__ + '] Being raised.')
                yield 0, mod, e
                continue

            if hasattr(_mod, 'USE'):
                if _mod.USE:
                    if hasattr(_mod, self.load_func):
                        getattr(_mod, self.load_func)(self.parent)
                        self.loaded.add(_mod)
                        yield _mod, 1
                    else:
                        logging.warning(str(mod) + ' Has no setup function. Ignoring...')
                        yield _mod, 0
                else:
                    yield _mod, 2
            else:
                logging.warning(str(mod) + ' Has no USE flag, ignoring...')
                self.available.append(_mod)
                yield _mod, 2
