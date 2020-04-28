#!/bin/bash
echo $DEPTH
echo $WEBSITE
echo $FILTER

wget -rnd --spider --delete-after --force-html --user "$USER" --password "$PASSWORD" -l $DEPTH "$WEBSITE" 2>&1 \
| awk '/^--/ {u=$3} /^HTTP request sent, awaiting response... / {s=$6} /^Length: .*\[(.+)\]$/ {t=$NF} /^$/ {printf "%s\n",u}' | egrep "$FILTER" | sort | uniq
