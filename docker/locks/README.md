# Locked build inputs

These files are build inputs for OrthoFinder 3.2-r2. They retain the Debian and
Python runtime versions used by the preceding native validation and define an
explicit reviewed build environment. They replace open-ended dependency
resolution. The standard release Action and repository-root context are unchanged.

## Base and Debian packages

Both Dockerfile stages use the same Python multiarch index digest:
`sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70`.
The lock files also record its amd64 and ARM64 platform manifests.

APT uses the official [Debian mirror service](https://deb.debian.org/):

- `https://deb.debian.org/debian/`: bookworm and bookworm-updates, main.
- `https://deb.debian.org/debian-security/`: bookworm-security, main.

`apt-ARCH-STAGE.json` locks the complete installation transaction: 81 builder
packages or 42 runtime packages, each with its original version, architecture,
size and SHA256. The frozen base supplies packages already installed. Schema 2
retains the original signed Snapshot metadata under `lock_creation_provenance`
to document how these identities were established; it is not a build source or
fallback. The ordinary mirror is a separate official service. The build does not
route requests around Snapshot access restrictions.

The build helper preserves TLS, trusted signature, Date and Valid-Until checks.
Debian may reissue signed repository metadata without changing locked packages.
Each build verifies that current InRelease signatures and Packages hashes form
a valid chain, then requires every locked package's name, version, architecture,
path, size and SHA256 in that signed index. The receipt records the actual
InRelease hashes, signer fingerprints and package-index hashes used by the build.
Missing locked versions fail explicitly; current metadata cannot authorize newer
package versions or different bytes.

The helper checks each downloaded .deb before installation with downloads disabled and requires the final
dpkg package set to equal the frozen base plus the locked transaction. An extra
dependency, changed version, removal, wrong architecture or checksum fails the
build. Temporary package files and APT lists are removed in the same RUN layer.
Regular mirrors may eventually remove an older package. This lock guarantees
input identity while the verified material remains available, not permanent
archival availability. There is no automatic alternate-source fallback.

## Python packages

`python-ARCH.json` fixes filenames, official URLs, sizes and SHA256 for 24
runtime wheels, six build-tool wheels, and the OrthoFinder/ETE4 source archives.
Wheel platform tags and the dependency closure were reviewed for CPython 3.12
on the two native architectures. The six build tools stay in the builder.

After fetching verified bytes, wheel building runs with networking disabled,
`--no-build-isolation`, `--no-deps` and `--no-index`. It uses the locked build
environment, instead of resolving a new isolated environment. The resulting
26 runtime wheels receive a checked manifest before offline installation.
The final Python environment must match all 27 expected package versions,
including pip 25.0.1 inherited from the pinned base; `pip check` must pass.

The preceding build exposed setuptools 84.2.1 and Cython 3.3.0 in wheel/generated
source metadata. Other build-tool choices were reviewed from the earlier
resolver evidence and exact upstream package metadata; a complete inventory
of that earlier isolated environment was unavailable. The new lock explicitly
defines and validates the complete build environment.

## Maintenance and scope

The helper and lock files are mounted read-only during image construction;
they are not copied into the runtime image. Readable build receipts are retained
under `/usr/local/share/doc/orthofinder/build-locks`. Normal taf install retains
these small source files along with the app repository and the original FastME
archive; it does not download the locked package payloads or build the image.

Do not regenerate hashes to accept unexpected bytes or silently follow a newer
package, base image, mirror or snapshot. Restore the verified original material,
or explicitly review updated input versions/hashes and repeat the native builds,
offline backend and wrapper checks. Fixed identities do not guarantee permanent
server availability or byte-identical output from compilers and timestamps.
