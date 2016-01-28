from debimgbuilder.builder import DebianRepo
from debimgbuilder.jessie import JessieBackportsImageBuilder

class DebianBaseImageBuilder(JessieBackportsImageBuilder):
    def setup_apt_sources(self):
        super().setup_apt_sources()
        # Setup wikimedia repository
        self.repo_sources.append(
            DebianRepo(
                'http://apt.wikimedia.org/wikimedia',
                'jessie-wikimedia',
                ['main', 'backports', 'thirdparty']
            )
        )
        # Add key for apt.wikimedia.org
        wikimedia_apt_key = """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1

mQGiBEUtBY8RBACJTZdWEBZHlibArWM1HrX5rcPCb+o2nmeTfNrtMpmVbkmi9vBE
VmIDnjc+VQlJNoiBOKMhAhRSO0rIwEbOTewiQSPERfsClGpv0ikb3kQVFls5HpfZ
49u9EAERRez+P2VJUH7CBmigKdxtKRGM5aLI+eOLUl+lZUn4NU6BsQOUGwCgtLiL
I+8DSNkoiV40UR3uFsS9KLMD/30Lth9A9JgwrDTFl8rlNxq3Eluulv0+2MYoDutW
2p384vJ8Vil+x1GPzZXT1NVHCPdJMXqfnUl33XkPJEFSJ3B1WhwU3muItPoM+GKM
cnJMn2rYJa6Fae7UZy8iRJwSuqSg4mGNa900m/izyYoijJzl1u4HtZhbV++lgubO
j+YfA/4sz68H/ZQZwG+d8X/xTgZ3+9qekqGFgxdGTICtiD7IRPPaQ7EUWOBml6tn
SHfd0TBkCKtfFkr6+rA3ZJ5pyo3OwO2yUAvlBOPeaX4ZKTl7+8lG9kqqGIBm/iZy
bHC75DF506Zm4IiesAXRmRqfB8gReOHEJybZkaCg8FZqhdGErLQ8V2lraW1lZGlh
IEFyY2hpdmUgQXV0b21hdGljIFNpZ25pbmcgS2V5IDxyb290QHdpa2ltZWRpYS5v
cmc+iF8EExECACAFAkUtBY8CGwMGCwkIBwMCBBUCCAMEFgIDAQIeAQIXgAAKCRAJ
29n5P2zUSmaGAJjipA+xkWInJJHCCcoJrf7rBzqEAJ9OEsJuxbBOvOJBovwpWtNh
goMcubkCDQRFLQWdEAgAvEAe6PnzhGdOC3ZYIeJalQyBEelRZiEdzjtdojTNEf29
6J75O8QqjQt/pyOZ9w/DCiy81dym3GlXeS61tcfNdSBMXqGtgXAskLV1djz0U7SU
89MiwjrSiYhYRYNSQcrshVDjzpHkj8HY0gwNyN5yZ1xnZ9/WG46Kay6quHQbfKn7
Egxs6ONJJaW7H1MM2cPzsJuzk1aXq4PJOFHgDo9J2j+nGVgk8XdGqgk5t0we69Oh
YXlxUTjgOE+XMxk4PEOFDjk0pTmxOUMP0b08dpvJf652O4jpnylBIiT9ZxRadENM
zmeBT//sJJIleYDh2a1xeDDQwzRig1swFnfYeuEugwADBQf/b7xdqYrLZYqtJVLO
fgh3HOJ605KNYlyreKj67x04fy8lIhrkp3wraVTN74+jObNhJTq3VesUoPPgJqRi
sABCwbGQeKriz7NUAflBliVapPjSd7qD696zO+wQd03z8wJecdxAcmw89+8jyHWV
bgSf3Thy0pfCDBOZL5ApDzPp/zveTAJJdl9xJ+kQA9g4kXIbqdsv0ytqfT56CAOC
vBIJ7JuzIz8eKZ5LlPoGosU5C6TPwlHwfrh1ttD5/LdoSbcz1ThCM3Q9nasvmQjQ
EGZteBiJH8UogRLTsqbJCtQM6aQL8J/+bWjSrmPdCp2z/dzFTgtga4DKcXiSYo+U
JVwilYhJBBgRAgAJBQJFLQWdAhsMAAoJEAnb2fk/bNRK/HEAn0ud2S4zsHv4Ayzp
QqdXQFnLYQ6mAJ9LlSuxDwXm+ln+7o++xUBMQCKJ7g==
=XekF
-----END PGP PUBLIC KEY BLOCK-----
        """.strip()
        self.chroot_write_file('/tmp/apt.wikimedia.org.pub', wikimedia_apt_key)
        self.chroot('/usr/bin/apt-key', 'add', '/tmp/apt.wikimedia.org.pub')
        self.chroot('/bin/rm', '/tmp/apt.wikimedia.org.pub')


class DebianProdImageBuilder(DebianBaseImageBuilder):
    def setup_apt_policy(self):
        super().setup_apt_policy()
        self.chroot_write_file(
            '/etc/apt/apt.conf.d/80security-debian-proxy',
            'Acquire::http::Proxy::security.debian.org "http://webproxy.eqiad.wmnet:8080";'
        )


if __name__ == '__main__':
    db = DebianProdImageBuilder(
        'debian:wikimedia-prod',
        'jessie',
        'http://mirrors.wikimedia.org/debian',
        'jessie',
    )
    db.build()
