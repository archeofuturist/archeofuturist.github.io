#!/usr/bin/env bash

set -eux

pushd `dirname $0`
./generate.py 10
cp 1.html index.html
git add .
git commit -m "New Post."
git push origin master
popd
