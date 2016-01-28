from debimgbuilder.builder import DebianBuilder, DebianRepo


class DebianBaseImageBuilder(DebianBuilder):
    def __init__(self, **kwargs):
        super(self).__init__(**kwargs)
        # Add security repository
        self.repo_sources.append(
            DebianRepo(
                'http://security.debian.org/',
                'jessie/updates',
                ['main', 'contrib', 'non-free']
            )
        )
        # Add Wikimedia apt repository
        self.repo_sources.append(
            DebianRepo(
                'http://apt.wikimedia.org/wikimedia',
                'jessie-wikimedia',
                ['main', 'backports', 'thirdparty']
            )
        )


class DebianProdImageBuilder(DebianBaseImageBuilder):
    def setup_apt_policy(self):
        super(self).setup_apt_policy()
        self.chroot_write_file(
            '/etc/apt/apt.conf.d/80security-debian-proxy',
            'Acquire::http::Proxy::security.debian.org "http://webproxy.eqiad.wmnet:8080";'
        )


if __name__ == '__main__':
    db = DebianProdImageBuilder(
        'http://mirrors.wikimedia.org/debian',
        'jessie',
        'jessie',
    )
    db.build()
