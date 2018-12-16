import logging
from .utils import *
from .exc import *

class RestlessCrawler:
    #######
    # Manages the amount of pictures received from one place
    DEFAULT_POST_CNT = CONFIG_FILE.POST_SIZE
    DEFAULT_IMAGE_COUNT = CONFIG_FILE.IMG_CNT
    DEFAULT_VIDEO_COUNT = CONFIG_FILE.VID_CNT
    DEFAULT_TAGS = [""]
    DEFAULT_CRAWL_TAGS = [""]
    DEFAULT_MIN_MEDIA = CONFIG_FILE.MIN_CNT
    DEFAULT_IMAGE_OFFSET = 0
    DEFAULT_VIDEO_OFFSET = 0

    # Lots of samples yas
    ########

    def __init__(
        self, mgr, user, db, tags=None, crawl_tags=None,
        max_imgs=None, max_vids=None, minimum_media=None,
        ioffset=None, voffset=None, ignore=False, adult=False,
        nsfw=False, min_likes_post=0, min_followers=0, min_posts=0):

        self.mgr = mgr
        self.db = db
        self.name = user
        self.shoutouts = set()
        self.media = set()
        self.ignore = ignore
        self.max_img = max_imgs or self.DEFAULT_IMAGE_COUNT
        self.max_vid = max_vids or self.DEFAULT_VIDEO_COUNT
        self.tags = tags or self.DEFAULT_TAGS
        self.crawl_tags = crawl_tags or self.DEFAULT_CRAWL_TAGS
        self.minimum_media = minimum_media or self.DEFAULT_MIN_MEDIA
        self.ioffset = ioffset or self.DEFAULT_IMAGE_OFFSET
        self.voffset = voffset or self.DEFAULT_VIDEO_OFFSET
        self.adult = adult
        self.nsfw = nsfw
        self.min_likes_post = min_likes_post
        self.min_followers = min_followers
        self.min_posts = min_posts
        self.dead_limit = int(len(self.db._data)*1.5)
        self.counter = 0
        self.og = (tags, crawl_tags)


    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


    def _rotate_posts(self, start_at=0, **kwargs):
        jpkg = self.db.current_client.posts(self.name, offset=start_at, **kwargs)
        if jpkg and 'blog' in jpkg:
           if self.adult or self.nsfw:
              for _filter in ['is_adult', 'is_nsfw']:
                if not _filter in jpkg['blog']:
                  break

           if 'posts' in jpkg and jpkg['posts']:
             for post in jpkg['posts']:
               if post['note_count'] > self.min_likes_post:
                 yield jpkg, post
               else:
                 continue
           else:
             logging.warning("No posts found! Tags: {}".format(self.tags))
             raise NoMorePosts()
        else:
          return

    def conviece(self, user, use_og=False):
        if user != self.name and not user in BlackList.ignore:
            if use_og:
              tags = self.og
            else:
              tags = self.crawl_tags, self.crawl_tags

            u = self.__class__(
                self.mgr, user, self.db, tags[0], tags[1],
                self.max_img, self.max_vid,
                minimum_media=self.minimum_media,
                adult=self.adult,
                nsfw=self.nsfw, min_followers=self.min_followers,
                min_likes_post=self.min_likes_post,
                min_posts=self.min_posts,
            )
            if not u in self.mgr.remember and not u == self:
              self.shoutouts.add(u)

    def follow_reblog_source(self, post):
        if 'source_url' in post:
          self.conviece(post['source_url'].split('//')[1].split('.')[0])

    def follow_notes(self, post):
        if 'notes' in post:
          for note in post['notes']:
            if post['type'] == 'reblog':
              self.conviece(note['blog_name'], use_og=True)

    def scrape_post(self, post):
        if post['type'] == 'video' and 'video_url' in post:
          self.media.add(post['video_url'])

        if post['type'] == 'photo':
          self.media.update(pic['original_size']['url'] for pic in post['photos'])


    def scrape(self, **kwargs):
        for deprecated in ('type', 'tag', 'offset'):
            if deprecated in kwargs:
                kwargs.pop(deprecated)

        for tag in self.tags:
          for catagory, limit in (('photo', self.max_img), ('video', self.max_vid)):
            for i in range(0, limit, self.DEFAULT_POST_CNT):
              logging.info("offset: "+str(i))
              try:
                for jpkg, post in self._rotate_posts(start_at=i, type=catagory, tag=tag, notes_info=True, **kwargs):
                  for func in (self.follow_reblog_source, self.follow_notes):
                    func(post)
                    #print(post)
                  self.scrape_post(post)
              except NoMorePosts:
                break



