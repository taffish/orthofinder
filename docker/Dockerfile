# Rebuild boundary: the Python tag, Debian repositories and Python build tools
# can drift or disappear. Checksummed release archives fail closed; this recipe
# does not promise permanent upstream availability or byte-identical rebuilds.
# On a missing archive, inspect the pinned release and recover verified original
# bytes if available. Adopting replacement bytes requires review and a full new
# build/test receipt; never just replace the checksum or remove verification.
FROM python:3.12-slim-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive

ARG ORTHOFINDER_VERSION=3.2
ARG DIAMOND_VERSION=2.1.25
ARG DIAMOND_COMMIT=b03a535f6e94f18158043d37ad6c18fbf4c8e9e3
ARG FAMSA_VERSION=2.5.2
ARG FASTME_VERSION=2.1.6.3
ARG ASTER_TAG=v1.25
ARG ASTER_COMMIT=db2b3e95da5bb0318b933afe1a144eb943ef7cbf
ARG MUSCLE_VERSION=5.3
ARG MUSCLE_SOURCE_SHA256=74b22a94e630b16015c2bd9ae83aa2be2c2048d3e41f560b2d4a954725c81968
ARG VCXPROJ_MAKE_COMMIT=806d016
ARG VCXPROJ_MAKE_SHA256=902735703004c47705ffa389329378f237fecb154945b489edf6abe260c6694f
ARG TARGETARCH

# Debian package revisions follow Bookworm repositories, not a frozen snapshot.
# Retry transient index errors first; a removed revision requires a reviewed
# dependency update and fresh native/backend tests, not a fabricated lock hash.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      git \
      build-essential \
      cmake \
      zlib1g-dev \
      libsqlite3-dev \
      automake \
      autoconf \
      libtool \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Runtime pins constrain versions, not archive retention. PyPI transitives and
# isolated build dependencies can change; retain build receipts and wheel hashes.
# Diagnose resolver/download failures separately. Recover verified old wheels or
# review new dependency pins and rerun the full matrix before accepting drift.
RUN set -eux; \
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
    printf '%s\n' \
      "biopython==1.87" \
      "bottle==0.13.4" \
      "brotli==1.2.0" \
      "certifi==2026.4.22" \
      "charset-normalizer==3.4.7" \
      "cheroot==11.1.2" \
      "ete4==4.4.0" \
      "idna==3.15" \
      "jaraco.functools==4.5.0" \
      "joblib==1.5.3" \
      "markdown-it-py==4.2.0" \
      "mdurl==0.1.2" \
      "more-itertools==11.0.2" \
      "numpy==2.4.5" \
      "pandas==3.1.0" \
      "pygments==2.20.0" \
      "requests==2.34.2" \
      "rich==15.0.0" \
      "scikit-learn==1.8.0" \
      "scipy==1.17.1" \
      "threadpoolctl==3.6.0" \
      "urllib3==2.7.0" \
      > /tmp/orthofinder-python-constraints.txt; \
    python -m pip wheel --timeout 120 --retries 5 --wheel-dir /wheels -c /tmp/orthofinder-python-constraints.txt "orthofinder-${ORTHOFINDER_VERSION}.tar.gz"

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

RUN set -eux; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fL \
      "https://gite.lirmm.fr/atgc/FastME/-/archive/v${FASTME_VERSION}/FastME-v${FASTME_VERSION}.tar.gz" \
      -o "FastME-v${FASTME_VERSION}.tar.gz"; \
    echo "d49ff78cca7b76eadf8443efb33f071a7e8a152618ffa3d8e790f167d0a0b176  FastME-v${FASTME_VERSION}.tar.gz" | sha256sum -c -; \
    tar -xzf "FastME-v${FASTME_VERSION}.tar.gz"; \
    cd "FastME-v${FASTME_VERSION}"; \
    autoreconf -fi; \
    ./configure --prefix=/usr/local; \
    make -j "$(nproc)"; \
    ./src/fastme --version | grep -Fx "FastME ${FASTME_VERSION}"; \
    cp ./src/fastme /artifacts/bin/fastme

RUN set -eux; \
    git -c advice.detachedHead=false clone --filter=blob:none --branch "${ASTER_TAG}" --depth 1 \
      https://github.com/chaoszhang/ASTER.git /build/ASTER; \
    cd /build/ASTER; \
    test "$(git rev-parse HEAD)" = "${ASTER_COMMIT}"; \
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

FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/usr/local/bin:${PATH}

# Debian package revisions follow Bookworm repositories, not a frozen snapshot.
# Diagnose mirror/index failures before changing dependencies; a changed runtime
# package set requires fresh native and backend validation.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      bash \
      ca-certificates \
      curl \
      fasttree \
      gzip \
      libgomp1 \
      libsqlite3-0 \
      libstdc++6 \
      mafft \
      mcl \
      mmseqs2 \
      ncbi-blast+ \
      procps \
      raxml \
      tar \
      unzip \
      zlib1g \
 && rm -rf /var/lib/apt/lists/*

COPY docker/orthofinder-smoke /usr/local/bin/orthofinder-smoke
COPY docker/licenses/FAMSA-LICENSE /usr/local/share/doc/orthofinder/dependency-licenses/FAMSA-LICENSE

COPY --from=builder /artifacts/bin/ /usr/local/bin/
COPY --from=builder /artifacts/share/orthofinder /usr/local/share/doc/orthofinder

# Mount installation archives read-only so they never enter a runtime layer.
RUN --mount=type=bind,from=builder,source=/wheels,target=/tmp/wheels \
    set -eux; \
    python -m pip install --no-cache-dir --no-index --find-links=/tmp/wheels "orthofinder==3.2"; \
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
