#!/usr/bin/env bash
# =============================================================================
# Mermaid to PDF Export Script
# Exports Mermaid diagrams to publication-ready figures
# =============================================================================

# Requirements:
# npm install -g @mermaid-js/mermaid-cli
# OR: npx @mermaid-js/mermaid-cli

DIAGRAMS_DIR="results/figures/diagrams"
OUTPUT_DIR="docs/paper/figures"
mkdir -p "$OUTPUT_DIR"

echo "=============================================="
echo "Exporting Mermaid Diagrams to PDF/SVG"
echo "=============================================="

# Key diagrams for the paper
declare -A DIAGRAMS=(
    ["16_paper_figure_system.md"]="fig1_system_overview"
    ["01_system_architecture.md"]="fig4_full_architecture"
    ["03_validation_algorithm.md"]="fig5_validation_algorithm"
    ["09_trust_score_flow.md"]="fig6_trust_score"
    ["08_ml_model_architecture.md"]="fig7_ml_architecture"
    ["14_dbscan_clustering.md"]="fig8_dbscan"
    ["13_geospatial_processing.md"]="fig3_geospatial"
)

for diagram in "${!DIAGRAMS[@]}"; do
    input="$DIAGRAMS_DIR/$diagram"
    output_name="${DIAGRAMS[$diagram]}"
    
    if [ -f "$input" ]; then
        echo "Processing: $diagram -> $output_name"
        
        # Export to SVG (vector, best for papers)
        npx -y @mermaid-js/mermaid-cli mmdc \
            -i "$input" \
            -o "$OUTPUT_DIR/${output_name}.svg" \
            -b white \
            -t default \
            --width 1200
        
        # Export to PNG (300 DPI equivalent)
        npx -y @mermaid-js/mermaid-cli mmdc \
            -i "$input" \
            -o "$OUTPUT_DIR/${output_name}.png" \
            -b white \
            -t default \
            --width 2400 \
            --scale 2
        
        echo "  ✓ Saved: ${output_name}.svg, ${output_name}.png"
    else
        echo "  ✗ Not found: $input"
    fi
done

echo ""
echo "=============================================="
echo "Export complete! Files saved to: $OUTPUT_DIR"
echo "=============================================="
echo ""
echo "To convert SVG to PDF for LaTeX, use:"
echo "  inkscape file.svg --export-pdf=file.pdf"
echo ""
echo "Or use ImageMagick:"
echo "  convert -density 300 file.svg file.pdf"
