#!/usr/bin/env python3
import subprocess
import os


class DebianRepo:
    def __init__(self, uri, suite, components):
        self.uri = uri
        self.suite = suite
        self.components = components

    def __str__(self):
        return 'deb {uri} {suite} {components}'.format(
            uri=self.uri,
            suite=self.suite,
            components=' '.join(self.componenets)
        )


class DebianBuilder:
    def __init__(self, mirror, suite, base_path,
                 variant='minbase'
                 base_components=None,
                 repo_sources=None):
        self.mirror = mirror
        self.suite = suite
        self.base_path = base_path
        self.chroot_base = os.path.join(base_path, 'chroot')
        self.debootstrap_path = '/usr/sbin/debootstrap'
        self.chroot_path = '/usr/sbin/chroot'
        self.repo_sources = repo_sources
        if base_components is None:
            self.base_components = ['main', 'contrib']
        else:
            self.base_components = base_components
        if repo_sources is None:
            self.repo_sources = [
                DebianRepo(
                    'http://security.debian.org/',
                    '{suite}/updates'.format(suite=suite),
                    self.base_components
                )
            ]
        self.base_components = base_components
        self.variant = variant

    def chroot(self, *args):
        return subprocess.check_call([
            self.chroot_path,
            self.chroot_base,
        ] + list(args))

    def chroot_file(self, path, mode='w'):
        if path.startswith('/'):
            path = path[1:]
        return open(os.path.join(self.chroot_base, path), mode)

    def chroot_write_file(self, path, contents):
        with self.chroot_file(path, 'w') as f:
            f.write(contents.strip())

    def append_line(self, path, line):
        with self.chroot_file(path, 'a') as f:
            f.write(line + '\n')

    def initialize_chroot(self):
        subprocess.check_call([
            self.debootstrap_path,
            '--components=' + ','.join(self.base_components),
            '--variant=' + self.variant,
            self.suite,
            self.chroot,
            self.mirror,
        ])

    def setup_apt_policy(self):
        # Disable auto starting on package install
        # For most Docker users, "apt-get install" only happens during
        # "docker build", where starting services doesn't work and
        # often fails in humorous ways. This prevents those failures
        # by stopping the services from attempting to start.
        self.chroot_write_file('/usr/sbin/policy-rc.d', """#!/bin/bash
    exit 101""")
        self.chroot('/bin/chmod', '+x', '/usr/sbin/policy-rc.d')

        self.chroot(
            '/usr/bin/dpkg-divert',
            '--local', '--rename', '--add', '/sbin/initctl'
        )
        self.chroot_write_file('/sbin/initctl', """#!/bin/bash
    exit 0""")
        self.chroot('/bin/chmod', '+x', '/sbin/initctl')

        # this file is one APT creates to make sure we don't
        # "autoremove" our currently in-use kernel, which doesn't
        # really apply to debootstraps/Docker images that don't
        # even have kernels installed
        self.chroot('/bin/rm', '-f',
                    '/etc/apt/apt.conf.d/01autoremove-kernels')

        # Since for most Docker users, package installs happen
        # in "docker build" steps, they essentially become
        # individual layers due to the way Docker handles layering,
        # especially using CoW filesystems.  What this means for us
        # is that the caches that APT keeps end up just wasting
        # space in those layers, making our layers unnecessarily
        # large (especially since we'll normally never use these
        # caches again and will instead just "docker build" again
        # and make a brand new image).

        # Ideally, these would just be invoking "apt-get clean",
        # but in our testing, that ended up being cyclic and we
        # got stuck on APT's lock, so we get this fun creation
        # that's essentially just "apt-get clean".

        apt_get_clean = '"rm -f /var/cache/apt/archives/*.deb' + \
            '/var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin' + \
            ' || true";'
        docker_clean = """
DPkg::Post-Invoke {{ {clean_cmd} }};
APT::Update::Post-Invoke {{ {clean_cmd} }};

Dir::Cache::pkgcache "";
Dir::Cache::srcpkgcache "";""".format(clean_cmd=apt_get_clean)
        self.chroot_write_file(
            '/etc/apt/apt.conf.d/docker-clean',
            docker_clean
        )

        # In Docker, we don't often need the "Translations"
        # files, so we're just wasting time and space by downloading
        # them, and this inhibits that.  For users that do need them,
        # it's a simple matter to delete this file and "apt-get update". :)
        self.chroot_write_file(
            '/etc/apt/apt.conf.d/docker-no-languages',
            'Acquire::Languages "none";'
        )

        # Since Docker users using "RUN apt-get update && apt-get
        # install -y ..." in their Dockerfiles don't go delete the
        # lists files afterwards, we want them to be as small as
        # possible on-disk, so we explicitly request "gz" versions and
        # tell Apt to keep them gzipped on-disk.

        # For comparison, an "apt-get update" layer without this on a
        # pristine debian:wheezy" base image was "29.88 MB", where with
        # this it was only "8.273 MB".

        self.chroot_write_file(
            '/etc/apt/apt.conf.d/docker-gzip-indexes',
            """Acquire::GzipIndexes "true";
Acquire::CompressionTypes::Order:: "gz";""")

        # Since Docker users are looking for the smallest possible final
        # images, the following emerges as a very common pattern:

        #   RUN apt-get update \
        #       && apt-get install -y <packages> \
        #       && <do some compilation work> \
        #       && apt-get purge -y --auto-remove <packages>

        # By default, APT will actually _keep_ packages installed via
        # Recommends or Depends if another package Suggests them, even
        # and including if the package that originally caused them to
        # be installed is removed.  Setting this to "false" ensures
        # that APT is appropriately aggressive about removing the
        # packages it added.

        # https://aptitude.alioth.debian.org/doc/en/ch02s05s05.html#configApt-AutoRemove-SuggestsImportant

        self.chroot_write_file(
            '/etc/apt/apt.conf.d/docker-autoremove-suggests',
            """Apt::AutoRemove::SuggestsImportant "false";"""
        )

    def setup_apt_sources(self):
        for rs in self.repo_sources:
            self.append_line('/etc/apt/sources.list', rs)

    def setup_dns(self):
        with open('/etc/resolv.conf') as read:
            with self.chroot_file('/etc/resolv.conf', 'w') as write:
                write.write(read.read())

    def update_apt(self):
        self.chroot('/usr/bin/apt-get', 'update')
        self.chroot('/usr/bin/apt-get', 'dist-upgrade', '--yes')

    def cleanup(self):
        self.chroot('/usr/bin/apt-get', 'clean')
        self.chroot('/bin/rm', '-r', '-f', '/var/lib/apt/lists/*')

    def tar_chroot(self):
        subprocess.check_call([
            '/bin/tar',
            '--auto-compress',
            '--create',
            '--file', os.path.join(self.base_path, 'root.tar.xz'),
            '--directory', self.chroot_base,
            # sed expression to transform file paths
            # Removes ./ from the beginning of file paths
            '--transform', 's,^./,,',
            '.'
        ])

    def run(self):
        self.initialize_chroot()
        self.setup_apt_policy()
        self.setup_apt_sources()
        self.setup_dns()
        self.update_apt()
        self.cleanup()
        self.tar_chroot()


db = DebianBuilder(
    'http://httpredir.debian.org/debian',
    'jessie',
    'jessie',
    []
)

db.run()
