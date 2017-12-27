#!/bin/bash
set -e

yum install -y rpm-build centos-release-openstack-pike

cd /root

mkdir -p /root/rpmbuild/SPEC
mkdir -p /root/rpmbuild/SOURCES

export version=$1

cp /opt/package/os-vm-expire-$1.tar.gz /root/rpmbuild/SOURCES
cp /opt/package/os-vm-expire-$1/packages/centos/* /root/rpmbuild/SPEC/
sed -i "s/Version:.*/Version: $version/" /root/rpmbuild/SPEC/os-vm-expire.spec

yum-builddep -y rpmbuild/SPEC/os-vm-expire.spec

rpmbuild -ba /root/rpmbuild/SPEC/os-vm-expire.spec

cp /root/rpmbuild/RPMS/noarch/*.rpm /opt/package/
