# Research Paper Compilation Guide

## Quick Start

### Option 1: Overleaf (Recommended - No Installation)
1. Go to [overleaf.com](https://www.overleaf.com)
2. Create new project → Upload Project
3. Upload entire `docs/paper/` folder contents:
   - `main.tex`
   - `references.bib`
   - `figures/` folder (with all PNG/PDF files)
4. Click "Recompile" → Download PDF

### Option 2: Local LaTeX (MiKTeX/TeX Live)

**Install MiKTeX (Windows):**
```bash
winget install MiKTeX.MiKTeX
```

**Compile:**
```bash
cd docs/paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

### Option 3: Docker
```bash
docker run --rm -v "${PWD}/docs/paper:/workdir" texlive/texlive:latest \
    bash -c "cd /workdir && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex"
```

## Paper Assets Summary

### LaTeX Files
- `main.tex` - Complete IEEE paper (406 lines)
- `references.bib` - 20 academic citations

### Figures (7 total)
| File | Description | Size |
|------|-------------|------|
| `study_area_map.png` | Mahanadi Delta map | ~200KB |
| `f1_vs_noise.png` | F1 vs noise line chart | ~240KB |
| `precision_recall_bar.png` | P/R comparison | ~115KB |
| `cnn_confusion_matrix.png` | ResNet-50 matrix | ~160KB |
| `latency_breakdown.png` | Component timing | ~195KB |
| `ablation_study.png` | Layer contributions | ~165KB |
| `layer_weights.png` | Weight distribution | ~245KB |

### Tables (5 total)
1. Data Sources
2. Main Results (F1 across noise)
3. Ablation Study
4. Latency Breakdown
5. Decision Thresholds

## Troubleshooting

### Missing `booktabs.sty`
```bash
# MiKTeX: Install via Package Manager
# TeX Live:
tlmgr install booktabs
```

### Figure not found
- Ensure figures/ folder is in same directory as main.tex
- Use relative path: `figures/study_area_map.png`

### Bibliography errors
- Run `bibtex main` after first `pdflatex`
- Then run `pdflatex` twice more to resolve references
