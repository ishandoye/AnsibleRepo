#!/bin/bash

packages=$@

# Check there is an exclude line already existing. Add it if not
if ! grep -q "^exclude.*=" /etc/yum.conf; then
  echo "exclude=" >> /etc/yum.conf
fi

# Ensure each package is present on the exclude line. Add them if not
for package in $packages
do
  if ! grep -q "^exclude=.*$package" /etc/yum.conf; then
    sed -i "s/^\(exclude=.*\)/\1 $package/" /etc/yum.conf
  fi
done

