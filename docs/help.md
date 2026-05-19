taf-orthofinder 3.1.5-r2

TAFFISH wrapper for OrthoFinder 3.1.5, a phylogenetic orthology toolkit for
comparative genomics from per-species protein FASTA files.

Usage:
  taf-orthofinder --help
  taf-orthofinder --version
  taf-orthofinder --compile [ARGS...]
  taf-orthofinder -- [ORTHOFINDER-ARGS...]
  taf-orthofinder orthofinder [ORTHOFINDER-ARGS...]
  taf-orthofinder COMMAND [ARGS...]

Wrapper help vs upstream help:
  taf-orthofinder --help                  Show this TAFFISH help
  taf-orthofinder --version               Show package version
  taf-orthofinder -- --version            Show upstream OrthoFinder version
  taf-orthofinder orthofinder --version   Show upstream OrthoFinder version
  taf-orthofinder orthofinder --help      Show upstream OrthoFinder help
  taf-orthofinder -- --help               Show upstream OrthoFinder help

Examples:
  taf-orthofinder orthofinder -f proteomes -t 16 -a 8 -o orthofinder-out
  taf-orthofinder -f proteomes -t 16 -a 8 -o orthofinder-out
  taf-orthofinder primary_transcript proteomes
  taf-orthofinder orthofinder -f proteomes/primary_transcripts -t 16 -a 8
  taf-orthofinder orthofinder -f proteomes -S diamond -M msa -A famsa -T fasttree
  taf-orthofinder orthofinder -f proteomes -S blastp -M msa -A mafft -T raxml
  taf-orthofinder orthofinder -f proteomes -S mmseqs -M msa -A muscle -T fasttree
  taf-orthofinder orthofinder -f proteomes -M dendroblast
  taf-orthofinder orthofinder --assign extra-proteomes --core core-results/Results_* -t 32 -a 16

Command mode:
  OrthoFinder has its own executable and helper commands. The clearest form is
  to name the executable explicitly:

    taf-orthofinder orthofinder -f proteomes -t 16 -a 8
    taf-orthofinder primary_transcript proteomes
    taf-orthofinder diamond version

  If the first argument starts with "-", TAFFISH passes it to the default
  orthofinder command, so option-leading shorthand also works.

Included:
  orthofinder, orthofinder-utils, primary_transcript, make_ultrametric,
  convert_orthofinder_tree_ids, create_hog_fastas, ncbi_primary_transcript,
  orthogroup_gene_count, diamond 2.1.25, famsa 2.5.2, muscle 5.3,
  FastTree 2.1.11, MCL, FastME 2.1.6.3, astral-pro 1.25.3.8, BLAST+,
  MMseqs2, MAFFT, classic RAxML, official ExampleData, and user_config.json.

Not included:
  IQ-TREE 3, RAxML-NG, VeryFastTree, large user datasets, custom databases,
  visualization tools, or downstream report post-processing tools.

Notes:
  MUSCLE is bundled as a TAFFISH source-built static MUSCLE 5.3 binary so the
  OrthoFinder -A muscle backend works on the published platforms.
  The --assign workflow requires astral-pro, which is included.
  Typical outputs are written under a Results_* directory. If -o is used,
  OrthoFinder requires the chosen output directory not to already exist.
  Native image platforms are linux/amd64 and linux/arm64.

Upstream:
  repository: https://github.com/OrthoFinder/OrthoFinder
  website:    https://orthofinder.github.io/OrthoFinder/
  release:    v3.1.5
  license:    GPL-3.0
