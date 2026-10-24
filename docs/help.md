taf-orthofinder 3.2-r1

Purpose:
  Infer orthogroups, orthologs and gene/species trees from protein FASTA files.
  This stable release exposes the upstream CLI, not its unreleased HTML preview.

Usage:
  taf-orthofinder -f proteomes -t 8 -a 2 -o results
  taf-orthofinder orthofinder -f proteomes -t 8 -a 2 -o results
  taf-orthofinder -- --help
  taf-orthofinder -- --version

Inputs:
  Put one protein FASTA file per species in proteomes/.
  Choose representative transcripts before running if genes have many isoforms:
    taf-orthofinder primary_transcript transcripts.fa last_dot
  Supply your own proteomes, species tree/configuration and any previous core
  results. No reference database or model download is required.

Common tasks:
  Default DIAMOND / FAMSA / FastTree pipeline:
    taf-orthofinder -f proteomes -t 8 -a 2 -o results
  MUSCLE alignment or legacy dendroblast:
    taf-orthofinder -f proteomes -A muscle -t 8 -a 2 -o muscle-results
    taf-orthofinder -f proteomes -M dendroblast -t 8 -a 2 -o dendro-results
  Add species to an existing core analysis:
    taf-orthofinder --assign extra-proteomes --core core-results/Results_NAME -t 8 -a 2
  Stop after orthogroups, then resume the same run:
    taf-orthofinder -f proteomes -og -t 8 -a 2 -o staged-results
    taf-orthofinder -fg staged-results/Results_NAME -t 8 -a 2
  Replace Results_NAME with the actual results directory, not an invented name.

Result utilities:
  taf-orthofinder split_ortholog_files results/Results_NAME -o pairwise -t 1
  taf-orthofinder species_tree_alignment results/Results_NAME -o alignment --species-names
  taf-orthofinder mcl_orthogroup_sequences results/Results_NAME -o mcl-sequences
  taf-orthofinder orthofinder-utils
  Use TOOL --help for each utility's options.

Common options:
  -t N / -a N       Search / analysis threads; set these for your machine.
  -s TREE          User-supplied rooted species tree.
  -S METHOD        Search program; default diamond.
  -M msa|dendroblast  Gene-tree method.
  -A METHOD / -T METHOD  Alignment / gene-tree program.
  -pof             Also write pairwise ortholog files (many files).
  -o DIR           New output directory, only with -f; it must not exist.
  --config FILE    User-supplied upstream program configuration.

Key outputs (inside Results_NAME):
  Orthogroups/Orthogroups.tsv
  Orthologs/SPECIES.tsv.gz
  Species_Tree/SpeciesTree_rooted.txt
  Phylogenetic_Hierarchical_Orthogroups/ and Comparative_Genomics_Statistics/
  Version 3.2 uses Orthologs, not the old Orthologues directory spelling.
  Keep the complete result tree and WorkingDirectory when planning a restart.
  Back up old results first: an upstream restart can update them in place.
  --assign creates new Results_* beside the core results; it does not accept -o.

Backend use:
  TAFFISH_CONTAINER_BACKEND=docker taf-orthofinder -f proteomes -o results
  TAFFISH_CONTAINER_BACKEND=podman taf-orthofinder -f proteomes -o results
  TAFFISH_CONTAINER_BACKEND=apptainer taf-orthofinder -f proteomes -o results
  Run from the project directory so inputs and outputs are in the current bind.
  Output files use your UID/GID; choose a directory writable by your account.
  Apptainer needs Linux; on macOS use Docker or Podman.
  Use project, results and core paths without whitespace: upstream rejects
  whitespace in analysis output paths, even when shell quoting is correct.
  Prefer no spaces in utility paths too. Ordinary shell quotes are insufficient.
  For a simple utility output with spaces, keep the inner double quotes literally:
    taf-orthofinder species_tree_alignment results/Results_NAME -o '"species alignment"' --species-names
  This does not allow spaces in analysis/core paths or arbitrary shell characters.

Immediate notes:
  A new -o directory is required. Utility outputs may overwrite files; choose
  a separate destination. split_ortholog_files skips existing files unless -f.
  Development-only --view/--tree-view/--stats-view/--groups-view are disabled
  by upstream in this stable release; use its CLI output tables and trees.
  Large runs need sufficient RAM, disk space and explicitly chosen threads.

More help:
  taf-orthofinder -- --help
  https://github.com/taffish/orthofinder
  https://orthofinder.github.io/OrthoFinder/

Wrapper options:
  taf-orthofinder --help       Show this installed-user help.
  taf-orthofinder --version    Show TAFFISH package identity.
  taf-orthofinder --compile    Print generated wrapper shell.
