#!env
DIR_PARENT=$(dirname $GITHUB_WORKSPACE)
mkdir -p $(dirname $GITHUB_WORKSPACE)
cd $(dirname $GITHUB_WORKSPACE)
rm -rf docker-base
git clone git@github.com:legendu-net/docker-base.git
cd docker-base
pwd
ls -lha
