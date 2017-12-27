#!/bin/bash

apt-get update && apt-get install -y git git-buildpackage devscripts moreutils

version=$1
cd /root
cp /opt/package/python-osvmexpire_${version}.orig.tar.gz /root/
tar xvfz python-osvmexpire_${version}.orig.tar.gz
cd os-vm-expire-${version}
echo y | mk-build-deps --install debian/control
>debian/changelog
prevtag=initial
pkgname=`cat debian/control | grep '^Package: ' | sed 's/^Package: //'`
git tag  | sort -V | while read tag; do
    if [ $prevtag != 'initial' ]; then
        (echo "$pkgname (${tag}) unstable; urgency=low"; echo ""; git log --simplify-by-decoration --pretty=format:'  * %(%h) %d%n' $prevtag..$tag; git log --pretty='format:%n%n -- %aN <%aE>  %aD%n%n' $tag^..$tag) | cat - debian/changelog | sponge debian/changelog
    fi
    prevtag=$tag
    done

sed -i 's;/usr/sbin/uwsgi;/usr/bin/uwsgi;' etc/systemd/system/osvmexpire-api.service

debian/rules binary
cd /root
cp -f *.deb  /opt/package/
