from debimgbuilder.builder import DebianBuilder, DebianRepo


class JessieImageBuilder(DebianBuilder):
    def __init__(self, image_name, base_path,
                 mirror='http://httpredir.debian.org/debian',
                 suite='jessie',
                 variant='minbase',
                 base_components=None,
                 repo_sources=None):
        if base_components is None:
            base_components = ['main', 'contrib']
        if repo_sources is None:
            repo_sources = []
        super().__init__(
            image_name,
            base_path,
            mirror,
            suite,
            variant,
            base_components,
            repo_sources
        )

    def setup_apt_sources(self):
        super().setup_apt_sources()
        # Add jessie-updates
        self.repo_sources.append(
                DebianRepo(
                    self.mirror,
                    'jessie-updates',
                    self.base_components,
                )
        )


class JessieBackportsImageBuilder(JessieImageBuilder):
    def setup_apt_sources(self):
        super().setup_apt_sources()
        # Add jessie-backports
        self.repo_sources.append(
                DebianRepo(
                    self.mirror,
                    'jessie-backports',
                    self.base_components,
                )
        )
