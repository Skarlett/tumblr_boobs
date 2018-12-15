#!/usr/bin/env bash
# auto_drop.sh
# usage: script <backup from dir>
# setup in cronjob

SIZE=5000000 # 5GB
BACKUP="/home/admin/backup/"
BACKUP_FILE="/home/admin/backup/backed.lst"

AES_KEY="$(dirname $PWD)/key"

find_next() {
  return python -c "import os;print(list(
     int(f.split('_')[1].split('.')[0])
     for root, dirs, files in os.walk('$1')
     for f in files if 'tar.gz' in files
   ).sort()[-1])"
}

if [ $# -eq 0 ]; then
  echo "$0 <dir>"
fi

if [ ! -f $AES_KEY ]; then
  echo "No key found... making one"
  dd if=/dev/urandom bs=32 count=1 > $AES_KEY
fi

if [ ! -f $BACKUP/key.md5 ]; then
  echo "No key hash found... making one"
  cat $AES_KEY | md5sum > "$BACKUP/key.md5"
fi

if [ ! -d $BACKUP ]; then
  mkdir $BACKUP
fi

bank_size=$(du -sc $1 | tail -n 1 | cut -f 1)

if [ $bank_size -gt $SIZE ]; then
  NEXT=$(find_next $BACKUP)
  filename="backup_$NEXT.tar.gz"

  tar -czf /tmp/$filename $1
  openssl aes-256-cbc -e -k $(cat AES_KEY) -in "/tmp/$filename" -out "/tmp/$filename.enc"
  rm /tmp/$filename
  rm -r $1/*
  filename="$filename.enc"
  mv /tmp/$filename $BACKUP

  backed_up_url=$(curl --upload-file "$BACKUP/$filename" "https://transfer.sh/$filename")

  echo "$filename | $(date) | $(ls -lh $1 | head -n 1) -> $backed_up_url" >> $BACKUP_FILE

  if [ $(python -c "print($NEXT - 2 >= 0)") -eq "True" ]; then
    rm "backup_$(python -c "print($NEXT - 2)")*"
  fi
fi

