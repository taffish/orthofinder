# taf-orthofinder

TAFFISH wrapper for [OrthoFinder](https://github.com/OrthoFinder/OrthoFinder),
a phylogenetic orthology inference toolkit for comparative genomics.
OrthoFinder infers orthogroups, gene trees, a rooted species tree, gene
duplications, orthologues, hierarchical orthogroups, and comparative genomics
statistics from per-species protein FASTA files.

This repository packages upstream OrthoFinder 3.1.5 as TAFFISH release
`3.1.5-r2`.

Release `3.1.5-r2` is a help-only TAFFISH update. It keeps the upstream
software, Dockerfile, runtime dependencies, smoke tests, and command behavior
unchanged from `3.1.5-r1`, and refreshes the terminal `taf-orthofinder --help`
text.

## Installation

Install from the public TAFFISH Hub index:

```sh
taf update
taf install orthofinder
```

Install the exact release:

```sh
taf install orthofinder 3.1.5-r2
```

For local testing before the app is published to the public index:

```sh
taf install --from .
```

## Usage

Show TAFFISH app help:

```sh
taf-orthofinder --help
```

Show the TAFFISH package version:

```sh
taf-orthofinder --version
```

Show the upstream OrthoFinder version and help:

```sh
taf-orthofinder orthofinder --version
taf-orthofinder -- --version
taf-orthofinder orthofinder --help
taf-orthofinder -- --help
```

Run OrthoFinder on one protein FASTA file per species:

```sh
taf-orthofinder orthofinder -f proteomes -t 16 -a 8 -o orthofinder-out
```

The default command is also available when the first argument is an upstream
option:

```sh
taf-orthofinder -f proteomes -t 16 -a 8 -o orthofinder-out
```

Use `primary_transcript` before OrthoFinder when proteomes contain multiple
isoforms per gene:

```sh
taf-orthofinder primary_transcript proteomes
taf-orthofinder orthofinder -f proteomes/primary_transcripts -t 16 -a 8
```

Choose method backends explicitly:

```sh
taf-orthofinder orthofinder -f proteomes -S diamond -M msa -A famsa -T fasttree
taf-orthofinder orthofinder -f proteomes -S blastp -M msa -A mafft -T raxml
taf-orthofinder orthofinder -f proteomes -S mmseqs -M msa -A muscle -T fasttree
taf-orthofinder orthofinder -f proteomes -M dendroblast
```

For large datasets, run a core set first and then assign additional species:

```sh
taf-orthofinder orthofinder -f core-proteomes -t 32 -a 16 -o core-results
taf-orthofinder orthofinder --assign additional-proteomes --core core-results/Results_* -t 32 -a 16
```

The `--assign` path requires `astral-pro`; this image includes a fixed
ASTER/ASTRAL-Pro build for that dependency.

Because this is a command-mode TAFFISH tool, the first non-option argument is
the in-container command. For OrthoFinder runs, naming the upstream
`orthofinder` binary explicitly is the clearest form:

```sh
taf-orthofinder orthofinder -f proteomes -t 16 -a 8
taf-orthofinder primary_transcript proteomes
taf-orthofinder diamond version
```

The `--` separator is useful for option-leading arguments sent to the default
`orthofinder` command:

```sh
taf-orthofinder -- --version
taf-orthofinder -- -f proteomes -t 16 -a 8
```

This README lists common usage patterns, not the full upstream manual. The
TAFFISH wrapper calls upstream `orthofinder` directly, so official OrthoFinder
options are available as upstream implements them.

## Package

```text
name: orthofinder
command: taf-orthofinder
version: 3.1.5-r2
kind: tool
image: ghcr.io/taffish/orthofinder:3.1.5-r2
upstream release: v3.1.5
upstream runtime version: 3.1.5
```

## Container

The container image is built from `docker/Dockerfile`. It starts from
`python:3.12-slim-bookworm`, installs upstream OrthoFinder from the official
`orthofinder-3.1.5.tar.gz` release archive, verifies official release
checksums, and installs the external programs needed for OrthoFinder's default
and common alternative method paths.

Included core runtime:

```text
orthofinder 3.1.5
orthofinder-utils and OrthoFinder utility commands
DIAMOND 2.1.25
FAMSA 2.5.2
MUSCLE 5.3, TAFFISH source-built static binary
FastTree 2.1.11
MCL
FastME 2.1.6.3
ASTER/astral-pro 1.25.3.8
Python 3.12 with OrthoFinder Python dependencies
Pinned build-time Python wheels for the OrthoFinder dependency stack
```

Included alternative method backends:

```text
BLAST+ commands: makeblastdb, blastp, blastn
MMseqs2 command: mmseqs
MAFFT
RAxML classic command: raxmlHPC
gzip, tar, unzip, bash and standard runtime utilities
```

Not included:

```text
IQ-TREE 3 / iqtree3
RAxML-NG
VeryFastTree
large custom databases or user proteome datasets
downstream visualization, report post-processing, or workflow orchestration tools
```

OrthoFinder can use custom method definitions through configuration files, but
this TAFFISH image only guarantees the included executables above. Keep large
downstream processing or visualization steps as separate TAFFISH tools or flows.
MUSCLE is bundled as the same TAFFISH source-built static MUSCLE 5.3 strategy
used by the standalone `muscle` app, because the Debian and official Linux
arm64 binaries fail a runtime sanity check. This keeps OrthoFinder's
`-A muscle` path usable on both declared image platforms.

The image keeps the upstream README, license, official `ExampleData`, release
`user_config.json`, and small upstream test proteomes under:

```text
/usr/local/share/doc/orthofinder
```

The image is built and validated for:

```text
linux/amd64
linux/arm64
```

## Smoke Checks

The TAFFISH metadata declares Docker smoke checks that verify:

```text
main OrthoFinder command and utility commands exist
orthofinder --version reports upstream version 3.1.5
upstream help advertises the main -f workflow
Python package import exposes version 3.1.5
DIAMOND, FAMSA, MUSCLE, FastME, ASTRAL-Pro, FastTree, MCL, BLAST+, MMseqs2 exist and run
primary_transcript produces a representative-transcript FASTA
DIAMOND can build and search a tiny protein database
FAMSA, MUSCLE, FastTree, and FastME can process tiny local inputs
OrthoFinder can run a minimal offline protein-set workflow and produce orthogroups and a rooted species tree
OrthoFinder can run the legacy dendroblast workflow on the same tiny data
OrthoFinder can run an MSA workflow with the bundled MUSCLE backend
```

Each smoke test is self-contained so the Hub index can run them in fresh
containers independently.

## Upstream

- Upstream repository: <https://github.com/OrthoFinder/OrthoFinder>
- Upstream website: <https://orthofinder.github.io/OrthoFinder/>
- Upstream release: <https://github.com/OrthoFinder/OrthoFinder/releases/tag/v3.1.5>
- Upstream license: GPL-3.0

If you use OrthoFinder, cite the relevant upstream OrthoFinder papers:

```text
Emms and Kelly. OrthoFinder: solving fundamental biases in whole genome comparisons dramatically improves orthogroup inference accuracy. Genome Biology. 2015.
doi:10.1186/s13059-015-0721-2.

Emms and Kelly. STRIDE: Species Tree Root Inference from Gene Duplication Events. Molecular Biology and Evolution. 2017.
doi:10.1093/molbev/msx259.

Emms and Kelly. OrthoFinder: phylogenetic orthology inference for comparative genomics. Genome Biology. 2019.
doi:10.1186/s13059-019-1832-y.

Emms and Kelly. SHOOT: phylogenetic gene search and ortholog inference. Genome Biology. 2022.
doi:10.1186/s13059-022-02652-8.

Emms et al. OrthoFinder3. bioRxiv. 2025.
doi:10.1101/2025.07.15.664860.
```
