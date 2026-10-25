# Base, complete APT package transactions and Python inputs
# are locked in docker/locks. Every downloaded archive is hash-checked; missing
# material fails closed. Locks fix input identities, not mirror availability or
# byte-identical compiler output. Recover verified original bytes, or explicitly
# review new locks and rerun all native/backend gates; never weaken verification.
FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70 AS builder

ENV DEBIAN_FRONTEND=noninteractive

ARG ORTHOFINDER_VERSION=3.2
ARG DIAMOND_VERSION=2.1.25
ARG DIAMOND_COMMIT=b03a535f6e94f18158043d37ad6c18fbf4c8e9e3
ARG FAMSA_VERSION=2.5.2
ARG FASTME_VERSION=2.1.6.3
# ASTER v1.25, unchanged from the preceding app revision.
ARG ASTER_COMMIT=db2b3e95da5bb0318b933afe1a144eb943ef7cbf
ARG ASTER_SOURCE_SHA256=f4538195a9d5143774fd6d94dadc73718df4512dba43e2c5b2659e99cdad3b48
ARG MUSCLE_VERSION=5.3
ARG MUSCLE_SOURCE_SHA256=74b22a94e630b16015c2bd9ae83aa2be2c2048d3e41f560b2d4a954725c81968
ARG VCXPROJ_MAKE_COMMIT=806d016
ARG VCXPROJ_MAKE_SHA256=902735703004c47705ffa389329378f237fecb154945b489edf6abe260c6694f
ARG TARGETARCH

# Use the regular official Debian service with current signature/expiry checks.
# Package identities stay locked: verify the signed index and each .deb before
# no-download install; reject extra packages, upgrades and removals. A removed
# locked package fails closed instead of following a newer version or fallback.
RUN --mount=type=bind,source=docker/locked-inputs.py,target=/tmp/locked-inputs.py,readonly \
    --mount=type=bind,source=docker/locks,target=/tmp/locks,readonly \
    python /tmp/locked-inputs.py apt --arch "${TARGETARCH}" \
      --lock "/tmp/locks/apt-${TARGETARCH}-builder.json" \
      --receipt /artifacts/share/orthofinder/build-locks/apt-builder.json

WORKDIR /build

# Fetch only the selected, checksummed source and wheel files. Build tooling is
# installed from the locked local inputs in the following network-free step.
RUN --mount=type=bind,source=docker/locked-inputs.py,target=/tmp/locked-inputs.py,readonly \
    --mount=type=bind,source=docker/locks,target=/tmp/locks,readonly \
    set -eux; \
    mkdir -p /artifacts/bin /artifacts/share/orthofinder /wheels; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fL \
      "https://github.com/OrthoFinder/OrthoFinder/releases/download/v${ORTHOFINDER_VERSION}/orthofinder-${ORTHOFINDER_VERSION}.tar.gz" \
      -o "orthofinder-${ORTHOFINDER_VERSION}.tar.gz"; \
    echo "554cc15b4cca86e496c680cccf8697f3b0953ff25403e2ff0d585bd015071adb  orthofinder-${ORTHOFINDER_VERSION}.tar.gz" | sha256sum -c -; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fL \
      "https://github.com/OrthoFinder/OrthoFinder/releases/download/v${ORTHOFINDER_VERSION}/ExampleData.tar.gz" \
      -o ExampleData.tar.gz; \
    echo "60024e9590ebdf48e89e6a7b564c803f93affa76238bd32dc7f16ebad5c7245f  ExampleData.tar.gz" | sha256sum -c -; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fL \
      "https://github.com/OrthoFinder/OrthoFinder/releases/download/v${ORTHOFINDER_VERSION}/user_config.json" \
      -o /artifacts/share/orthofinder/user_config.json; \
    echo "ecc3e10fdae09be7c16fc55bd8f26306201275b8a5fe56802d412b2f88b40ef1  /artifacts/share/orthofinder/user_config.json" | sha256sum -c -; \
    tar -xzf "orthofinder-${ORTHOFINDER_VERSION}.tar.gz" -C /artifacts/share/orthofinder --strip-components=1 \
      "orthofinder-${ORTHOFINDER_VERSION}/README.md" \
      "orthofinder-${ORTHOFINDER_VERSION}/LICENSE" \
      "orthofinder-${ORTHOFINDER_VERSION}/tests/data/proteome"; \
    tar -xzf ExampleData.tar.gz -C /artifacts/share/orthofinder; \
    python /tmp/locked-inputs.py fetch-python --arch "${TARGETARCH}" \
      --lock "/tmp/locks/python-${TARGETARCH}.json" \
      --inputs /build/python-inputs --reuse-from /build \
      --receipt /artifacts/share/orthofinder/build-locks/python-inputs.json

RUN --network=none \
    --mount=type=bind,source=docker/locked-inputs.py,target=/tmp/locked-inputs.py,readonly \
    --mount=type=bind,source=docker/locks,target=/tmp/locks,readonly \
    python /tmp/locked-inputs.py build-python --arch "${TARGETARCH}" \
      --lock "/tmp/locks/python-${TARGETARCH}.json" \
      --inputs /build/python-inputs --wheels /wheels \
      --receipt /artifacts/share/orthofinder/build-locks/python-build.json

RUN set -eux; \
    git -c advice.detachedHead=false clone --filter=blob:none --branch "v${DIAMOND_VERSION}" --depth 1 \
      https://github.com/bbuchfink/diamond.git /build/diamond; \
    cd /build/diamond; \
    test "$(git rev-parse HEAD)" = "${DIAMOND_COMMIT}"; \
    grep -q '#include <algorithm>' src/util/parallel/filestack.cpp || sed -i '1i #include <algorithm>' src/util/parallel/filestack.cpp; \
    mkdir build; \
    cd build; \
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local ..; \
    cmake --build . -j "$(nproc)"; \
    ./diamond version | grep -Fx "diamond version ${DIAMOND_VERSION}"; \
    cp ./diamond /artifacts/bin/diamond

RUN set -eux; \
    arch="${TARGETARCH:-$(uname -m)}"; \
    case "${arch}" in \
      amd64|x86_64) \
        famsa_archive="famsa-v${FAMSA_VERSION}-x64_linux.tar.gz"; \
        famsa_sha="ce5fbee7705567cdf6500445b3b93bee66f027d71bc550a35f8be24853df9bda"; \
        ;; \
      arm64|aarch64) \
        famsa_archive="famsa-v${FAMSA_VERSION}-arm64_linux.tar.gz"; \
        famsa_sha="3033258ac3ef07bdf102db806285a33fa7146674aaffbace00fd6aaa20c1e28e"; \
        ;; \
      *) \
        echo "Unsupported TARGETARCH for FAMSA: ${arch}" >&2; \
        exit 1; \
        ;; \
    esac; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fL \
      "https://github.com/refresh-bio/FAMSA/releases/download/v${FAMSA_VERSION}/${famsa_archive}" \
      -o "${famsa_archive}"; \
    echo "${famsa_sha}  ${famsa_archive}" | sha256sum -c -; \
    tar -xzf "${famsa_archive}" -C /artifacts/bin famsa; \
    chmod 0755 /artifacts/bin/famsa; \
    /artifacts/bin/famsa -help 2>&1 | grep -F "version ${FAMSA_VERSION}-" >/dev/null

# Keep the upstream archive byte-for-byte: GitHub runners cannot reach its host.
# Provenance and a readable license accompany it in docker/vendor. Verify the
# original checksum before extraction; do not replace bytes or relax the hash.
COPY docker/vendor/FastME-v${FASTME_VERSION}.tar.gz /build/
RUN set -eux; \
    echo "d49ff78cca7b76eadf8443efb33f071a7e8a152618ffa3d8e790f167d0a0b176  FastME-v${FASTME_VERSION}.tar.gz" | sha256sum -c -; \
    tar -xzf "FastME-v${FASTME_VERSION}.tar.gz"; \
    cd "FastME-v${FASTME_VERSION}"; \
    autoreconf -fi; \
    ./configure --prefix=/usr/local; \
    make -j "$(nproc)"; \
    ./src/fastme --version | grep -Fx "FastME ${FASTME_VERSION}"; \
    cp ./src/fastme /artifacts/bin/fastme

# The fixed-commit official archive avoids the failing Git pack transfer.
# Its source blobs were compared with the commit tree; astral-pro needs neither
# Git metadata nor the optional TAPER submodule. Archive compression can change:
# retain this hash and review any mismatch, never silently accept new bytes.
RUN set -eux; \
    curl --fail --location --show-error --proto '=https' --proto-redir '=https' \
      --connect-timeout 30 --max-time 1200 --retry 2 --retry-delay 3 \
      --retry-all-errors --retry-max-time 1800 \
      "https://github.com/chaoszhang/ASTER/archive/${ASTER_COMMIT}.tar.gz" \
      -o /build/aster.tar.gz; \
    echo "${ASTER_SOURCE_SHA256}  /build/aster.tar.gz" | sha256sum -c -; \
    mkdir -p /build/ASTER; \
    tar -xzf /build/aster.tar.gz -C /build/ASTER --strip-components=1; \
    cd /build/ASTER; \
    g++ -std=gnu++11 -O2 -pthread src/astral-pro.cpp -o /artifacts/bin/astral-pro; \
    /artifacts/bin/astral-pro -h 2>&1 | grep -F "Version: v1.25.3.8" >/dev/null

RUN set -eux; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      "https://github.com/rcedgar/muscle/archive/refs/tags/v${MUSCLE_VERSION}.tar.gz" \
      -o muscle.tar.gz; \
    echo "${MUSCLE_SOURCE_SHA256}  muscle.tar.gz" | sha256sum -c -; \
    mkdir -p /build/muscle; \
    tar -xzf muscle.tar.gz -C /build/muscle --strip-components=1; \
    cd /build/muscle; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      "https://raw.githubusercontent.com/rcedgar/vcxproj_make/${VCXPROJ_MAKE_COMMIT}/vcxproj_make.py" \
      -o src/vcxproj_make.py; \
    echo "${VCXPROJ_MAKE_SHA256}  src/vcxproj_make.py" | sha256sum -c -; \
    sed -i \
      -e "s/ -march=native//g" \
      -e 's#rc = os.system("make 2> make.stderr | tee make.stdout")#rc = os.system("true")#' \
      src/vcxproj_make.py; \
    chmod +x src/vcxproj_make.py; \
    sed -i "s/defined(__arm64__)/defined(__arm64__) || defined(__aarch64__)/" src/myutils.h; \
    cd src; \
    python ./vcxproj_make.py --openmp; \
    printf '"v%s-taffish-r1"\n' "${MUSCLE_VERSION}" > gitver.txt; \
    make -j"$(nproc)"; \
    install -D -m 0755 ../bin/muscle /artifacts/bin/muscle; \
    /artifacts/bin/muscle -version 2>&1 | sed -n "1p" | grep -Fx "muscle ${MUSCLE_VERSION}.linux64 [v${MUSCLE_VERSION}-taffish-r1]" >/dev/null; \
    mkdir -p /tmp/muscle-check; \
    cd /tmp/muscle-check; \
    printf ">a\nMKTAYIAK\n>b\nMKTAYIG\n" > aln.fa; \
    /artifacts/bin/muscle -align aln.fa -output muscle.fa >/tmp/muscle-align.log 2>&1; \
    test -s muscle.fa

# Preserve source-built dependency notices in the runtime image.
RUN set -eux; \
    mkdir -p /artifacts/share/orthofinder/dependency-licenses; \
    find /build/diamond /build/ASTER /build/muscle "/build/FastME-v${FASTME_VERSION}" \
      -maxdepth 2 -type f \( -iname '*license*' -o -iname 'copying*' \) \
      -exec cp --parents '{}' /artifacts/share/orthofinder/dependency-licenses/ \;; \
    cp -L "/build/FastME-v${FASTME_VERSION}/COPYING" /artifacts/share/orthofinder/dependency-licenses/FastME-COPYING; \
    cp "/build/FastME-v${FASTME_VERSION}/README" /artifacts/share/orthofinder/dependency-licenses/FastME-README

FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70

ARG TARGETARCH

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/usr/local/bin:${PATH}

# Runtime packages use the same official sources and full-transaction checks as
# the builder. Lock/helper mounts are build-only, outside the runtime image.
RUN --mount=type=bind,source=docker/locked-inputs.py,target=/tmp/locked-inputs.py,readonly \
    --mount=type=bind,source=docker/locks,target=/tmp/locks,readonly \
    python /tmp/locked-inputs.py apt --arch "${TARGETARCH}" \
      --lock "/tmp/locks/apt-${TARGETARCH}-runtime.json" \
      --receipt /usr/local/share/doc/orthofinder/build-locks/apt-runtime.json

COPY docker/orthofinder-smoke /usr/local/bin/orthofinder-smoke
COPY docker/licenses/FAMSA-LICENSE /usr/local/share/doc/orthofinder/dependency-licenses/FAMSA-LICENSE

COPY --from=builder /artifacts/bin/ /usr/local/bin/
COPY --from=builder /artifacts/share/orthofinder /usr/local/share/doc/orthofinder

# Mount installation archives read-only so they never enter a runtime layer.
RUN --network=none \
    --mount=type=bind,from=builder,source=/wheels,target=/tmp/wheels,readonly \
    --mount=type=bind,source=docker/locked-inputs.py,target=/tmp/locked-inputs.py,readonly \
    --mount=type=bind,source=docker/locks,target=/tmp/locks,readonly \
    set -eux; \
    python /tmp/locked-inputs.py install-python --arch "${TARGETARCH}" \
      --lock "/tmp/locks/python-${TARGETARCH}.json" --wheels /tmp/wheels \
      --receipt /usr/local/share/doc/orthofinder/build-locks/python-runtime.json; \
    chmod 0755 /usr/local/bin/orthofinder-smoke; \
    chmod -R a+rX /usr/local/share/doc/orthofinder; \
    python -m pip check; \
    orthofinder --version 2>&1 | python -c 'import re, sys; text = re.sub(chr(27) + r"\[[0-9;]*m", "", sys.stdin.read()); assert "OrthoFinder:v3.2" in text, text'; \
    diamond version | grep -Fx "diamond version 2.1.25"; \
    famsa -help 2>&1 | grep -F "version 2.5.2-" >/dev/null; \
    fastme --version | grep -Fx "FastME 2.1.6.3"; \
    astral-pro -h 2>&1 | grep -F "Version: v1.25.3.8" >/dev/null; \
    FastTree 2>&1 | grep -F "FastTree Version 2.1.11" >/dev/null; \
    mcl -h >/dev/null; \
    makeblastdb -help >/dev/null; \
    mmseqs version >/dev/null; \
    muscle -version 2>&1 | sed -n "1p" | grep -Fx "muscle 5.3.linux64 [v5.3-taffish-r1]" >/dev/null; \
    raxmlHPC -v 2>&1 | grep -F "RAxML" >/dev/null

ENV TAFFISH_ENV=TAFFISH
ENV TAFFISH_NAME=orthofinder
