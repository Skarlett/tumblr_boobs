DEBUGGING = True

import os, pwd
import configparser

getusername = lambda: pwd.getpwuid(os.getuid())[0]

class CONFIG_FILE:
    ''' Lets load up some configuration variables '''
    user = getusername()
    if user == "root":
      DIR = '/root/.config/tumblr_scraper'
    else:
      DIR = "/home/{}/.config/tumblr_scraper/".format(user)
    FP = os.path.join(DIR, "tumblr_scraper.conf")
    _CONFIG = configparser.ConfigParser()

    if not os.path.isfile(FP):
        if not os.path.exists(DIR):
          os.makedirs(DIR)
        _CONFIG['APP'] = {
            'jsondb': os.path.join(DIR, 'keys.json'),
            'reset': 24 * 60 * 60,
            'total_limit': 5000,
            'hour_limit': 1000,
            'save_every_x_requests': 50,
            'download_chunk_size': 4098,
            'download_threads': 4,
            'download_agents': 4,
            'pass_tags_to_crawl_tags_if_crawl_tags_empty': True,
            'debug': False,
            'blacklist_fp': os.path.join(DIR, 'blacklist.lst')
        }
        _CONFIG['API'] = {
            'maxpost': 20,
            'default_img_cnt': 200,
            'default_vid_cnt': 40,
            'default_min_media': 20
        }
        with open(FP, 'w') as cf:
            _CONFIG.write(cf)

        print('configuration file wrote to {} - exitting, please restart.'.format(FP))
        exit(0)

    else:
        DB = _CONFIG.get('app', 'jsondb', fallback=os.path.join(DIR, 'keys.json'))
        BLACKLST = _CONFIG.get('app', 'blacklist_fp', fallback=os.path.join(DIR, 'blacklist.lst'))
        RESET = _CONFIG.get('app', 'reset', fallback=24 * 60 * 60)
        TLIMIT = _CONFIG.get('app', 'total_limit', fallback=5000)
        HLIMIT = _CONFIG.get('app', 'hour_limit', fallback=1000)
        DL_SIZE = _CONFIG.get('app', 'download_chunk_size', fallback=1028)
        DL_AGENTS = _CONFIG.get('app', 'download_agents', fallback=2)
        DL_THREADS = _CONFIG.get('app', 'download_threads', fallback=2)
        SAVECNT = _CONFIG.get('app', 'save_every_x_requests', fallback=200)
        PASS_TAGS = _CONFIG.get('app', 'pass_tags_to_crawl_tags_if_crawl_tags_empty', fallback=True)
        DEBUG = _CONFIG.get('app', 'debug', fallback=False)

        POST_SIZE = _CONFIG.get('api', 'maxpost', fallback=20)
        IMG_CNT = _CONFIG.get('api', 'default_img_cnt', fallback=200)
        VID_CNT = _CONFIG.get('api', 'default_vid_cnt', fallback=40)
        MIN_CNT = _CONFIG.get('api', 'default_min_media', fallback=20)

        if DEBUG:
            global DEBUGGING
            DEBUGGING = True