from debimgbuilder.builder import DebianBuilder, DebianRepo

if __name__ == '__main__':
    db = DebianBuilder(
        'ubuntu:trusty-wikimedia',
        'trusty',
        'http://ubuntu.wikimedia.org/ubuntu/',
        'trusty',
        'minbase',
        ['main', 'universe'],
        [
            DebianRepo(
                'http://ubuntu.wikimedia.org/ubuntu/',
                'trusty-updates',
                ['main', 'universe'],
            )
        ]
    )
    db.build()
