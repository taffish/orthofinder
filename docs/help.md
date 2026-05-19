# taf-orthofinder Help

`taf-orthofinder` runs upstream OrthoFinder 3.1.5, a phylogenetic orthology
inference toolkit for comparative genomics.

## Wrapper Usage

```sh
taf-orthofinder --help
taf-orthofinder --version
taf-orthofinder --compile [ARGS...]
taf-orthofinder -- [ORTHOFINDER-ARGS...]
taf-orthofinder orthofinder [ORTHOFINDER-ARGS...]
```

`taf-orthofinder --help` shows this TAFFISH help. `taf-orthofinder --version`
shows the TAFFISH package version. Use `taf-orthofinder -- --version` or
`taf-orthofinder orthofinder --version` for the upstream OrthoFinder version.

Show upstream help:

```sh
taf-orthofinder orthofinder --help
taf-orthofinder -- --help
```

## Common Commands

Run OrthoFinder on one protein FASTA file per species:

```sh
taf-orthofinder orthofinder -f proteomes -t 16 -a 8 -o orthofinder-out
```

Use option-leading shorthand for the default upstream command:

```sh
taf-orthofinder -f proteomes -t 16 -a 8 -o orthofinder-out
```

Prepare representative transcripts before running OrthoFinder:

```sh
taf-orthofinder primary_transcript proteomes
taf-orthofinder orthofinder -f proteomes/primary_transcripts -t 16 -a 8
```

Use the default MSA workflow explicitly:

```sh
taf-orthofinder orthofinder -f proteomes -S diamond -M msa -A famsa -T fasttree
```

Use common alternative backends included in the same container:

```sh
taf-orthofinder orthofinder -f proteomes -S blastp -M msa -A mafft -T raxml
taf-orthofinder orthofinder -f proteomes -S mmseqs -M msa -A muscle -T fasttree
taf-orthofinder orthofinder -f proteomes -M dendroblast
```

Scale by assigning additional species to a core run:

```sh
taf-orthofinder orthofinder -f core-proteomes -t 32 -a 16 -o core-results
taf-orthofinder orthofinder --assign additional-proteomes --core core-results/Results_* -t 32 -a 16
```

The `--assign` workflow requires `astral-pro`; this image includes it.

## Command-Mode Notes

This is a normal TAFFISH tool app with command mode enabled. The clearest form
is to name the upstream executable explicitly:

```sh
taf-orthofinder orthofinder -f proteomes -t 16 -a 8
taf-orthofinder primary_transcript proteomes
taf-orthofinder diamond version
```

If the first argument starts with `-`, TAFFISH sends it to the default
`orthofinder` command:

```sh
taf-orthofinder -- --version
taf-orthofinder -- -f proteomes -t 16 -a 8
```

## Included And Not Included

Included:

```text
orthofinder, orthofinder-utils, primary_transcript, make_ultrametric
convert_orthofinder_tree_ids, create_hog_fastas, ncbi_primary_transcript
orthogroup_gene_count
diamond 2.1.25, famsa 2.5.2, muscle 5.3, FastTree 2.1.11, MCL, FastME 2.1.6.3
astral-pro 1.25.3.8
BLAST+, MMseqs2, MAFFT, classic RAxML
official ExampleData, user_config.json, and small upstream test proteomes
```

Not included:

```text
IQ-TREE 3 / iqtree3
RAxML-NG
VeryFastTree
large user datasets or custom databases
downstream visualization or report post-processing tools
```

MUSCLE is bundled as a TAFFISH source-built static MUSCLE 5.3 binary, matching
the standalone `muscle` app build strategy. This is intentional: Debian and
official Linux arm64 MUSCLE binaries fail a runtime sanity check, while
OrthoFinder can call `muscle` internally for the `-A muscle` backend.

## Outputs

Typical OrthoFinder output includes orthogroups, orthologues, gene trees,
species trees, duplication events, hierarchical orthogroups, and summary
statistics inside a `Results_*` directory. Use `-o` to choose a non-default
output parent directory; OrthoFinder requires that a non-default output
directory does not already exist.

## Platform

The image is built for `linux/amd64` and `linux/arm64`. It uses native Linux
builds for both declared platforms; this is not an amd64-only emulation
package.

## Citation

Upstream:

- Repository: <https://github.com/OrthoFinder/OrthoFinder>
- Website: <https://orthofinder.github.io/OrthoFinder/>
- Release: <https://github.com/OrthoFinder/OrthoFinder/releases/tag/v3.1.5>
- License: GPL-3.0

Main OrthoFinder citations:

```text
Emms and Kelly 2015. doi:10.1186/s13059-015-0721-2.
Emms and Kelly 2017. doi:10.1093/molbev/msx259.
Emms and Kelly 2019. doi:10.1186/s13059-019-1832-y.
Emms and Kelly 2022. doi:10.1186/s13059-022-02652-8.
Emms et al. 2025. doi:10.1101/2025.07.15.664860.
```
