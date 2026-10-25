# FastME build source

`FastME-v2.1.6.3.tar.gz` is the unmodified upstream source archive for FastME
2.1.6.3 (1,100,731 bytes). It is retained because the upstream source server
was unreachable from GitHub-hosted build runners.

- Original URL: https://gite.lirmm.fr/atgc/FastME/-/archive/v2.1.6.3/FastME-v2.1.6.3.tar.gz
- SHA256: `d49ff78cca7b76eadf8443efb33f071a7e8a152618ffa3d8e790f167d0a0b176`
- Verify here: `sha256sum -c SHA256SUMS` or `shasum -a 256 -c SHA256SUMS`.

The Docker builder copies this archive and verifies the original checksum
before extraction. Existing compilation commands remain unchanged. The final
runtime image receives the executable and dependency notices, not the source
archive. Normal `taf install` retains the archive with app source, without
compiling FastME or performing a separate archive download.

## License and attribution

FastME source headers, including `src/fastme.c`, declare GNU GPL version 3 or
(at your option) any later version (GPL-3.0-or-later), with these notices:

- Copyright 2002-2007 Rick Desper, Olivier Gascuel
- Copyright 2007-2014 Olivier Gascuel, Stephane Guindon, Vincent Lefort

The unchanged archive preserves all upstream notices. The TAFFISH packaging
repository's Apache-2.0 license does not relicense this third-party source.

The archive's `COPYING` is an absolute symbolic link to
`/usr/share/automake-1.16/COPYING`, so a portable readable copy of GNU GPLv3 is
provided beside it as `FastME-COPYING`. That text comes from Automake's fixed
v1.16.5 `lib/COPYING` (the installed COPYING), at
https://github.com/autotools-mirror/automake/blob/v1.16.5/lib/COPYING.
The existing builder continues to dereference its installed Automake COPYING
into the runtime dependency-license directory. The original archive is not
repacked to alter its symlinks.

## Maintenance

Do not silently replace the archive, repack it or weaken checksum validation.
An intentional source update must review provenance/version/license and update
the archive, SHA256SUMS and Dockerfile hash together in a new app revision.
Other build inputs are locked as described in [../locks/README.md](../locks/README.md),
including their remaining availability and reproducibility boundaries. This
archive addresses FastME acquisition only.
