# taf-orthofinder

TAFFISH tool packaging for [OrthoFinder](https://github.com/OrthoFinder/OrthoFinder):
orthogroups, orthologs, gene/species trees and comparative-genomics statistics
from per-species protein FASTA files.

- Package: `orthofinder 3.2-r1`; installed command: `taf-orthofinder`.
- Image: `ghcr.io/taffish/orthofinder:3.2-r1`.
- Native platforms: `linux/amd64,linux/arm64`.
- Packaging license: Apache-2.0; upstream license files remain unchanged.
- Upstream: official [v3.2](https://github.com/OrthoFinder/OrthoFinder/releases/tag/v3.2),
  commit `c2142b862aea0ea8cfad71a32764572e4b086aa6`.

## Install and run

After this version is published and indexed:

```sh
taf update
taf install orthofinder 3.2-r1
taf-orthofinder --help
taf-orthofinder -- --help
taf-orthofinder -- --version
taf-orthofinder -f proteomes -t 8 -a 2 -o results
```

Provide one protein FASTA file per species. Choose a representative transcript
per gene when appropriate; the wrapper does not make scientific choices for you:

```sh
taf-orthofinder primary_transcript transcripts.fa last_dot
taf-orthofinder orthofinder-utils
taf-orthofinder -f proteomes -A muscle -t 8 -a 2 -o muscle-results
taf-orthofinder -f proteomes -M dendroblast -t 8 -a 2 -o dendro-results
taf-orthofinder --assign extra-proteomes --core core-results/Results_NAME -t 8 -a 2
```

Replace `Results_NAME` with the actual directory. A non-option first argument
selects an in-container executable. Option-leading arguments use `orthofinder`.
Wrapper `--help/--version` describe the TAFFISH package; use `-- --help` and
`-- --version` for upstream. Use a project and analysis-output/core path with no
whitespace. Upstream 3.2 explicitly rejects whitespace in `-o` and in the full
result location used for continuation/assignment; quoting cannot remove this
upstream restriction. Prefer whitespace-free paths for utilities too. Ordinary
shell quotes are not sufficient in the current TAFFISH automatic command mode:
the outer shell removes them before TAFFISH joins the arguments into a command.
For a utility output containing ordinary spaces, preserve literal double quotes
inside single quotes, for example after generating `results/Results_NAME`:

```sh
taf-orthofinder species_tree_alignment results/Results_NAME -o '"species alignment"' --species-names
```

The outer single quotes preserve the inner double quotes for the container
command; those double quotes are not part of the output directory name.
Do not replace this with `-o "species alignment"`, which loses the boundary.
This narrow workaround is for simple utility paths containing spaces, not
arbitrary shell characters (such as quotes, dollar signs or backticks), and it
cannot bypass upstream's analysis-output/core whitespace restriction. Rename
such paths or copy inputs into a whitespace-free project directory instead.

## Version 3.2 output and restart changes

The default now writes compressed per-species `Orthologs/SPECIES.tsv.gz`.
The old `Orthologues/` spelling has changed to `Orthologs/`; downstream code
also needs the new `Single_Copy_Ortholog_Sequences/`,
`Orthogroups/Orthogroups_SingleCopyOrthologs.txt` and
`Comparative_Genomics_Statistics/OrthologsStats_*.tsv` spellings.
Use `-pof` to request pairwise ortholog files during the run, or split selected
results afterwards:

```sh
taf-orthofinder split_ortholog_files results/Results_NAME -o pairwise -t 1
taf-orthofinder species_tree_alignment results/Results_NAME -o alignment --species-names
taf-orthofinder mcl_orthogroup_sequences results/Results_NAME -o mcl-sequences
```

The latter two are new upstream utilities for the concatenated species-tree
alignment and MCL orthogroup FASTAs. They require the complete working files,
not just copied final TSVs. See each utility's `--help`.

A complete result tree includes `Orthogroups/`, `Orthologs/`,
`Species_Tree/`, `Gene_Trees/`, `Resolved_Gene_Trees/`,
`Phylogenetic_Hierarchical_Orthogroups/`,
`Gene_Duplication_Events/`, `Comparative_Genomics_Statistics/`,
`WorkingDirectory/` and `Log.txt`; some outputs depend on the chosen method
and stop point. Technical smoke results are not a scientific accuracy claim.

```sh
taf-orthofinder -f proteomes -og -t 8 -a 2 -o staged-results
taf-orthofinder -fg staged-results/Results_NAME -t 8 -a 2
```

Fresh `-o` must not exist and is only accepted with `-f`, not `--assign`.
Assignment creates a new `Results_*` directory beside the core results directory.
Restart modes can modify the original run in place
and upgrade old directory names: make a backup first. Keep `WorkingDirectory`
and its state/metadata. `split_ortholog_files` skips existing pairwise files
unless `--force` is explicitly supplied; alignment/FASTA utilities can replace
their own outputs, so prefer separate destinations.

## Runtime and dependency choices

The existing Python 3.12 Bookworm source-install strategy is retained.
The official sdist is verified against SHA256
`554cc15b4cca86e496c680cccf8697f3b0953ff25403e2ff0d585bd015071adb`.
No OrthoFinder algorithm or release/preview flags are patched.

Included: OrthoFinder and all eleven official console entry points; DIAMOND
2.1.25, FAMSA 2.5.2, MUSCLE 5.3, FastTree 2.1.11, FastME 2.1.6.3,
ASTER/ASTRAL-Pro 1.25.3.8, MCL, BLAST+, MMseqs2, MAFFT and classic RAxML.
The existing small compiler-portability fixes for DIAMOND/MUSCLE remain;
MUSCLE's `-march=native` is removed and its AArch64 macro recognized.
These are dependency build fixes, not OrthoFinder algorithm changes.

Python runtime constraints retain the prior versions and add pandas 3.1.0
required by 3.2. Versions constrain resolution but do not guarantee permanent
archive retention or byte-identical rebuilds. The base tag, Debian repositories,
Python transitives and isolated build dependencies may drift; Dockerfile
comments identify those boundaries. Fixed source hashes fail closed instead of
silently accepting different archives. Keep a built image digest for exact reuse.

IQ-TREE 3, RAxML-NG and VeryFastTree are not included. Custom program configurations
can only use installed executables; `--config FILE` does not install programs.
Full datasets, benchmarks and all alternative scientific methods are not
validated by the tiny packaging checks.

## Resources and shared use

The released CLI does not download reference databases or models.
Proteomes, optional species tree/config files,
and previous `--core` results are project-specific inputs and derived state,
not an independently versioned upstream resource collection. Therefore a
database/model installation helper and automatic resource selection are N/A.
There is no silent reference download fallback.

The official ExampleData, small upstream test proteomes, README, LICENSE and
release configuration are bundled read-only at
`/usr/local/share/doc/orthofinder`. Tests copy them to writable scratch before
running; do not use that image directory as an output location.

An administrator may share project proteomes read-only using normal filesystem
permissions (traversable directories, readable files). Each user supplies a
separate writable output/project directory. Do not concurrently mutate a shared
core run or restart someone else's results. Input-data licensing belongs to the
chosen dataset; the software license does not grant rights to arbitrary inputs.

## Backends and GUI boundary

The wrapper automatically binds the current working directory for all three
backends. Docker uses your UID/GID; Podman additionally uses keep-id; Apptainer
keeps the calling user. Choose a directory writable by that account, without
requiring root or fixing output ownership afterwards. Run from a project
directory containing the inputs and outputs:

```sh
TAFFISH_CONTAINER_BACKEND=docker taf-orthofinder -f proteomes -o results
TAFFISH_CONTAINER_BACKEND=podman taf-orthofinder -f proteomes -o results
TAFFISH_CONTAINER_BACKEND=apptainer taf-orthofinder -f proteomes -o results
```

No GPU, GUI service, listening port or privileged mode is required. Apptainer
requires Linux; macOS users can use Docker or Podman. Site scheduler resources
and CPU/RAM/disk sizing remain the user's responsibility.

GUI discovery checked the release README, extras, entry points and source.
The archive contains HTML viewer code, but `run/cli_options.py` explicitly
sets `PREVIEW_OPTIONS=False`: `--view/--tree-view/--stats-view/--groups-view`
are unreleased development features, omitted from stable CLI help.
`tools/list_tools.py` likewise marks `view_results` as unreleased; it is not a
console entry point. We retain the official code but do not enable or advertise
it as a supported 3.2 GUI. PyQt6 belongs to the upstream docs extra, not the
released CLI. Stable outputs are tables, FASTAs and trees; browser/service
lifecycle checks are N/A for this public surface, not a claimed GUI PASS.

## Testing and local development

```sh
taf check
taf build
./target/taf-orthofinder-v3.2-r1 -- --version
```

Each `orthofinder-smoke MODE` is independent and creates its own writable
temporary directory. Modes cover identity, all helpers, transcript selection,
DIAMOND, aligners, default/dendroblast/MUSCLE pipelines, stop/restart,
assignment and failures. Redirected failures replay bounded stage logs.

The initial 2026-10-24 candidate was built natively on both declared architectures.
On the private xjp Linux amd64 host, Docker, Podman and actual read-only
Apptainer SIF passed; native ARM64 Docker and Podman also passed. The matrix
contained 396 independent offline smoke invocations and 105 real-wrapper calls.
Docker/Podman each passed normal and non-root read-only-root checks. The
wrapper tests covered metadata, command-mode helpers, actual host-bound
outputs and ownership, new output utilities, restart, assignment, negative
cases and idempotent splitting. Utility space-path checks preserve literal
double quotes as shown above; they do not prove ordinary shell quoting works.
Analysis paths with whitespace are explicitly rejected by upstream.

Five runtime permission probes checked parent-directory traversal, dependency
notices and denied-access/read-only negative controls. Five injected failures
confirmed visible stage, original exit code and bounded log output. Each of
the five runtime axes matched 101 upstream Python files against the official
sdist; only `_version.py` is regenerated by upstream's setuptools-scm build,
and its reported version was separately checked as 3.2.

The documentation-closeout rerun passed 396 fresh independent offline smoke
invocations. The final current-wrapper evidence contains 22 passing checks on
each of five native axes (110 calls): xjp amd64 Docker, Podman and Apptainer,
plus local ARM64 Docker and Podman. The engine-recovery follow-up reran both
ARM64 wrappers completely and repeated all 88 ARM64 Docker offline normal /
non-root read-only smoke invocations. Its permission, source-integrity and
failure-log probes also passed. The unchanged xjp three-backend receipts and
ARM64 Podman exact-smoke receipts were rechecked, not presented as fresh reruns.

Current image sizes are 808,712,503 bytes (amd64) and 798,678,188 bytes (ARM64).
The largest directories are the Python runtime/dependencies (460/481 MiB),
system libraries (168/184 MiB), and shared runtime data (55 MiB). Small official
fixtures and notices occupy about 2.2 MiB. Mounting wheels from the build stage
instead of copying them into a retained layer removed 87,172,600 bytes from
the amd64 baseline. The fresh amd64 closeout rebuild is four bytes larger than
the initial validated image and has a separately recorded identity.

ARM64 Apptainer is not separately validated; this is not a six-combination
claim. Earlier Docker Desktop runs failed in host file sharing with
`service fs failed: injecting event blocked for 60s`, including with Podman
temporarily stopped. After an authorized switch from VirtioFS to gRPC FUSE,
the unchanged wrapper and its default mounts passed the complete regression.
Podman was started in an independent process session and passed its complete
wrapper regression and subsequent health checks. Final engine/residue checks
passed; no memory, quota or security settings were changed. These observations
support a local recovery/workaround, not a guarantee against future Desktop
failures. Earlier failures remain in maintainer evidence. Local validation is
not a claim that future floating CI, public GHCR/Index acceptance or
production-scale scientific accuracy is proven.

## Troubleshooting

- Missing input: run from the directory containing the input folder; missing
  proteomes are an error, not a request to download data.
- Existing output: select a new directory, or deliberately use the appropriate
  restart option with a backed-up complete result tree.
- Old downstream script: update `Orthologues` paths and compressed-table parsing.
- Unknown `--view`: that preview feature is disabled by upstream in stable 3.2.
- Memory/process limits: reduce `-t/-a`; keep enough writable scratch and output
  space. The default analysis-thread count changed in upstream 3.2.

## License and citation

The sdist's top-level LICENSE is GPLv3 and several source headers are GPLv3,
while its pyproject metadata says `LGPL-3.0-only`. These upstream declarations
are inconsistent; this package preserves both rather than relicensing code.
Dependencies retain their own licenses. TAFFISH packaging files are Apache-2.0.
Official examples retain their upstream notices.

Cite the upstream OrthoFinder papers as appropriate:
2015 [Genome Biology](https://doi.org/10.1186/s13059-015-0721-2),
2017 [STRIDE](https://doi.org/10.1093/molbev/msx259),
2019 [Genome Biology](https://doi.org/10.1186/s13059-019-1832-y),
2022 [SHOOT](https://doi.org/10.1186/s13059-022-02652-8), and
2026 [OrthoFinder in Nature Methods](https://doi.org/10.1038/s41592-026-03126-6),
plus [STAG](https://doi.org/10.1101/267914) when applicable.
