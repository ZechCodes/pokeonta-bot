# Container trust maintenance

The image installs certifi 2026.10.19 through uv 0.13.4, then replaces both
`/etc/ssl/certs/ca-certificates.crt` and the entire hashed certificate directory
with that bundle. Existing anchors cannot survive through old hash links.
Poetry 1.8.5 preserves compatibility with this project's existing lock format.
A rebuild and deployment are required; changing this repository does not update
a running container. Rebuild after future CA trust changes.

The Python 3.8 / Debian Buster base remains unsupported. Migrating to a
supported Python base also requires reviewing discord.py 1.7.3 and its
`aiohttp<3.8` dependency, PyYAML 5.4.1, and old binary dependencies. That
application compatibility migration is separate from this CA trust correction;
the current change does not claim to patch the rest of the operating system.

Validation on 2026-10-21: the CA-install layer builds, rejects all 16 disclosed
affected chains via file/hash/default OpenSSL trust, and completes ordinary
HTTPS. The full application build currently fails while building existing
PyYAML 5.4.1 (`AttributeError: cython_sources` under PEP 517). The CA-only
change does not claim the full legacy application image is buildable.
