#!/bin/sh

set -e

DIR="$1"

if [ -z "$DIR" ] ; then
    echo "You must give a directory to build into"
    echo "  usage: $(basename $0) DIR"
    exit 2
fi

silver init $DIR
cd $DIR

if [ ! -e src/openwebapps-sticky-repo ] ; then
    cd src
    git clone git@github.com:mozilla/openwebapps-sticky-repo.git
    cd ..
fi

if [ ! -L app.ini ] ; then
    rm -f app.ini
    ln -s src/openwebapps-sticky-repo/silver/app.ini
fi

if [ ! -L lib/python ] ; then
    cd lib
    if [ -e python ] ; then
        rmdir python
    fi
    ln -s ../src/openwebapps-sticky-repo/silver/lib-python python
    cd ..
fi

if [ ! -L static/static ] ; then
    cd static
    ln -s ../src/openwebapps-sticky-repo/static
    cd ..
fi

if [ -e README.txt ] ; then
    rm README.txt
fi
