# Tumblr Scraper Kit
Kit is a basic server & client relationship based on SSH (rsync)

Features:
  + Rolling API db
  + Multithreaded
  + Crawler
  + Fine tuned options
  + retrieve and kill backups

To use the scraper, you'll need API keys (supports rolling API keys for 100s of requests)

```python crawler --db-add <4 part key>```

**NOTE** its still really janky, I highly recommend using `-il`, use atleast 6+ keys.
It does work well but not all issues resolved.


A basic Diagram
```
    Crawler -> ../downloads/ -> auto_drop.sh -> ../packaged <- auto_recv.sh -> processor -> processed.
```

Crawler scrapes **VIDEOS/IMAGES** only. It saves it in the following format.

`../downloads/<username>/0.jpeg`

The `auto_recv` script uses *rsync* to connect via SSH, pulling the downloads, decrypting and unpacking them


in more details, it includes a backup system (https://transfer.sh) with keeps files for **14 days**.

where it keeps a `backup.lst` file to specify that where the urls have been loaded to.
The project generates a Symmetric key on first run, assert both these match. (`key`).
During the execution of `auto_recv` it will check `key.md5` provided in `../downloads`.
Comparing the hashes and a mismatch will cause an error.

- `crawler.py` - Scrapes tumblr
- `auto_drop.sh` - Packages + encrypts
- `auto_recv.sh` - Unpackages + decrypts
- `process.py` - runs processing engine
