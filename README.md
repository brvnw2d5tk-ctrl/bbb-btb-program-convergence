# Blood–brain and blood–testis barrier program convergence

This repository contains the Python renderers and shared styling code for the five main figures accompanying a computational comparison of independently learned blood–brain and blood–testis barrier gene-expression programs. The renderers use prepared figure source tables; they do not rerun the upstream analyses or regenerate the underlying statistics.

## Requirements

Python 3.12 is recommended. Install the pinned plotting dependencies with:

```bash
python -m pip install -r requirements.txt
```

A Conda environment is also defined in `environment.yml`.

## Data

The code reads prepared panel tables from `<data-root>/figure_source_data/`. The tables are not included because they are submission source data. Raw and third-party data are not redistributed; obtain them from their original repositories.

Relevant GEO accessions include GSE254315, GSE106487, GSE142585, GSE256493, GSE163577 (NCI subset), and GSE335898. Disease-expression candidate datasets were GSE154535, GSE253279, GSE224929, GSE149512, and GSE202647. GSE169062 was reviewed as a candidate but not analyzed. The genetic analyses used GWAS Catalog records GCST90483468, GCST90472808, GCST90472810, GCST90472809, GCST90244151, and GCST90104543, plus the published microbleeds and lacunar-stroke releases KNOL2020-BMB-ANY and TRAYLOR2021-LAC-EUR. GCST90558279 was not evaluable. Linkage-disequilibrium references were 1000 Genomes Phase 3 European and East Asian panels.

Set the data root with `--data-root` or `BBB_BTB_DATA_ROOT`. The root must contain `figure_source_data/` with the CSV files named by each renderer. For example:

```bash
python src/renderers/figure_1.py --data-root YOUR_DATA_ROOT
```

## Run

Render a figure by running one of `src/renderers/figure_1.py` through `figure_5.py` after setting the data root. Check the input configuration without rendering with:

```bash
python src/renderers/figure_1.py --dry-run --data-root YOUR_DATA_ROOT
```

## Outputs

Each renderer writes PDF, SVG, PNG (300 dpi), and TIFF (600 dpi) files under `<data-root>/figures/main/`, plus a small render record under `<data-root>/runs/figure_render/logs/`.

## Reproducibility notes

The supplied code reproduces figure rendering from prepared source tables; it does not reproduce the upstream single-cell, program-discovery, or genetic analyses. The historical source-control commit for cNMF 1.7.1 and some stage-specific environments were not recorded. Renderer inputs must be reconstructed separately from the public accessions and documented analysis outputs.

## Citation

Citation details will be added when a public DOI is assigned.

## License

No licence has been selected. The author must choose a licence before public release; see `LICENSE`.
