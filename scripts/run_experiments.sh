#!/bin/bash
# =============================================================================
# Experiment Runner Shell Script
# Odisha Flood Validation System
# =============================================================================

set -e

echo "========================================"
echo "Running Validation Experiments"
echo "========================================"

# Activate conda environment
# conda activate flood-validation

# Change to project directory
cd "$(dirname "$0")/.."

# Create results directories
mkdir -p results/experiments
mkdir -p results/plots
mkdir -p results/tables

# =============================================================================
# Step 1: Generate Synthetic Datasets
# =============================================================================
echo ""
echo "📊 Step 1/3: Generating synthetic datasets..."
echo "-------------------------------------------"

python -c "
from src.experiments.data_generator import SyntheticDataGenerator
generator = SyntheticDataGenerator()
generator.generate_all_datasets('data/synthetic')
print('✅ Synthetic datasets generated')
"

# =============================================================================
# Step 2: Run Experiments
# =============================================================================
echo ""
echo "🧪 Step 2/3: Running noise sensitivity experiments..."
echo "-------------------------------------------"

python -c "
from src.experiments.runner import ExperimentRunner
runner = ExperimentRunner()
results = runner.run_noise_sensitivity_analysis()
print()
print('📊 Results Summary (15% noise):')
print(runner.generate_summary_table(results))
"

# =============================================================================
# Step 3: Generate Plots
# =============================================================================
echo ""
echo "📈 Step 3/3: Generating publication figures..."
echo "-------------------------------------------"

python -c "
from src.experiments.plotting import generate_all_plots
generate_all_plots()
"

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "========================================"
echo "✅ Experiments Complete!"
echo "========================================"
echo ""
echo "Results saved to:"
echo "  - results/experiments/noise_sensitivity_summary.csv"
echo "  - results/plots/f1_vs_noise.png"
echo "  - results/plots/iou_comparison.png"
echo "  - results/plots/precision_recall.png"
echo ""
