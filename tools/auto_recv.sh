#!/usr/bin/env bash
# auto_recv.sh
# cronjob it

DEAD_DROP="admin@satori.vps:/home/admin/backup/"

SAVEDIR="/home/god/tumblr_packs"

DISCARDDIR="/home/god/tumblr_rejects"
DROPOFF="/home/god/tumblr_drop_off"



ERRORS="$(dirname $0)/errs.log"
AES_KEY="$(dirname $0)/../key"

echo "Initial Check ..."

if [ ! -f $AES_KEY ]; then
  echo "No key found... making one"
  dd if=/dev/urandom bs=32 count=1 > $AES_KEY
fi

echo "Done"

echo "Downloading..."
rsync -r -t $DEAD_DROP $DROPOFF
echo "Done. Performing Symmetric Encryption check."

if [ -f "$DROPOFF/key.md5" ]; then
  if [ $(cat "$DROPOFF/key.md5") -eq $(cat $AES_KEY | md5sum) ]; then
    echo "Key Matched up!"
    # Everything looks good
  else
    echo "KEY DIDN'T MATCH" >> $ERRORS
    echo "KEY DIDN'T MATCH"
    exit 1
  fi
else
  echo "NO KEY FOUND" >> $ERRORS
  echo "NO KEY FOUND"
  exit 1
fi

echo "Unpackaging & Decrypting"

for drop in $(ls $DROPOFF | grep *.tar.gz); do
  if [ "$(python -c "print('$drop'.endswith('enc'))")" -eq "True" ]; then
    openssl aes-256-cbc -d -k $(cat AES_KEY) -in "$DROPOFF/$drop" -out "/tmp/$drop"
    rm "$DROPOFF/$drop"
    drop="/tmp/$drop"
  else
    drop="$DROPOFF/$drop"
  fi

  folder="$(python -c "print('$drop'.split('/')[-1].split('.')[0])")"
  tar -xzf $drop "/tmp/$folder"
  mv "/tmp/$folder/*" "$SAVEDIR"
  rm -rf "/tmp/$folder"
done

echo "Done."
echo "running profile collections against scraping engines"

for profile_dir in $(ls "$SAVEDIR"); do
  python process.py $profile_dir --trash=$DISCARDDIR 2>> $ERRORS
done
