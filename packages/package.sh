#!/bin/bash
set -e

echo "package.sh needs git, pip and virtualenv to generate deb and rpm packages"
git --help 1>/dev/null  && pip -h 1>/dev/null  && virtualenv -h 1>/dev/null

# the temp directory used, within $DIR
# omit the -p parameter to create a temporal directory in the default location
WORK_DIR=`mktemp -d`

CUR_DIR=${PWD}

# check if tmp dir was created
if [[ ! "$WORK_DIR" || ! -d "$WORK_DIR" ]]; then
  echo "Could not create temp dir"
  exit 1
fi

# deletes the temp directory
function cleanup {
  rm -rf "$WORK_DIR"
  echo "Deleted temp working directory $WORK_DIR"
}

# register the cleanup function to be called on the EXIT signal
trap cleanup EXIT

cd $WORK_DIR
git clone https://github.com/genouest/os-vm-expire.git
cp os-vm-expire/packages/package_centos.sh .
cp os-vm-expire/packages/package_debian.sh .

cd os-vm-expire
version=`git describe --abbrev=0 --tags`
git checkout tags/${version}

virtualenv venv
. venv/bin/activate
pip install reno
reno report > CHANGELOG
deactivate

git log --tags --simplify-by-decoration --format="* %cd %aN%n- (%h) %s%d%n" --date=local | sed -r 's/[0-9]+:[0-9]+:[0-9]+ //' >> packages/centos/os-vm-expire.spec

cd $WORK_DIR

mv os-vm-expire os-vm-expire-${version}

tar cvfz os-vm-expire-${version}.tar.gz
echo "generate rpm...."
docker run -v ${PWD}:/opt/package --rm  centos /opt/package/package_centos.sh ${version}

echo "generate deb...."
cp -r packages/debian ./
tar cvfz python-osvmexpire_${version}.orig.tar.gz os-vm-expire-${version}
docker run -v ${PWD}:/opt/package --rm  centos /opt/package/package_debian.sh ${version}

cp *.rpm *.deb *.dsc *.changes ${PWD}/
