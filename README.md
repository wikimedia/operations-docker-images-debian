# Debian / Ubuntu Base docker images #

Provides a nice little python setup for building base
debian/ubuntu images. Based off of the upstream
[`mkimage/debootstrap.sh`](https://github.com/docker/docker/blob/master/contrib/mkimage/debootstrap) but written in python, since the upstream script is a
very-hard-to-customize bash script. See `wikimedia.py`
for an example of how to customize this.

## Wikimedia base images ##

Right now the repo organization is a mess, but you can
build a docker image appropriate for use in Wikimedia
production by simply running

```
python3 -m debimgbuilder.wikimedia
```
