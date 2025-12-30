import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

def plot_f1_vs_noise(results_df: pd.DataFrame, output_path: str = "results/plots/f1_vs_noise.png"):
    """
    Plot F1-score vs Noise Level for all methods.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(10, 6))
    
    methods = results_df['method'].unique()
    colors = {'no_validation': '#ff6b6b', 'random': '#feca57', 
              'dem_only': '#48dbfb', 'pure_ml': '#a55eea', 'proposed': '#1dd1a1'}
    markers = {'no_validation': 's', 'random': '^', 
               'dem_only': 'o', 'pure_ml': 'd', 'proposed': '*'}
    
    for method in methods:
        method_data = results_df[results_df['method'] == method].sort_values('noise_level')
        plt.plot(
            method_data['noise_level'], 
            method_data['f1'] * 100,
            marker=markers.get(method, 'o'),
            color=colors.get(method, '#333'),
            linewidth=2,
            markersize=10 if method == 'proposed' else 7,
            label=method.replace('_', ' ').title()
        )
    
    plt.xlabel('Noise Level (%)', fontsize=12)
    plt.ylabel('F1 Score (%)', fontsize=12)
    plt.title('Validation Performance vs. Noise Level', fontsize=14, fontweight='bold')
    plt.legend(loc='lower left', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 35)
    plt.ylim(50, 100)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved: {output_path}")


def plot_iou_comparison(results_df: pd.DataFrame, output_path: str = "results/plots/iou_comparison.png"):
    """
    Bar chart comparing IoU at 15% noise.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df = results_df[results_df['noise_level'] == 15].copy()
    df = df.sort_values('iou', ascending=True)
    
    colors = ['#ff6b6b', '#feca57', '#48dbfb', '#a55eea', '#1dd1a1']
    
    plt.figure(figsize=(10, 6))
    bars = plt.barh(df['method'].str.replace('_', ' ').str.title(), 
                    df['iou'] * 100, 
                    color=colors[:len(df)])
    
    # Add value labels
    for bar, val in zip(bars, df['iou']):
        plt.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                 f'{val*100:.1f}%', va='center', fontsize=10)
    
    plt.xlabel('IoU (%)', fontsize=12)
    plt.title('Flood Extent Accuracy (IoU) at 15% Noise', fontsize=14, fontweight='bold')
    plt.xlim(0, 100)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved: {output_path}")


def plot_precision_recall_tradeoff(results_df: pd.DataFrame, output_path: str = "results/plots/precision_recall.png"):
    """
    Precision vs Recall scatter for all methods at 15% noise.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df = results_df[results_df['noise_level'] == 15].copy()
    
    plt.figure(figsize=(8, 8))
    
    colors = {'no_validation': '#ff6b6b', 'random': '#feca57', 
              'dem_only': '#48dbfb', 'pure_ml': '#a55eea', 'proposed': '#1dd1a1'}
    
    for _, row in df.iterrows():
        plt.scatter(row['recall'] * 100, row['precision'] * 100, 
                    s=200 if row['method'] == 'proposed' else 100,
                    c=colors.get(row['method'], '#333'),
                    label=row['method'].replace('_', ' ').title(),
                    edgecolors='black', linewidth=1)
    
    plt.xlabel('Recall (%)', fontsize=12)
    plt.ylabel('Precision (%)', fontsize=12)
    plt.title('Precision-Recall Trade-off', fontsize=14, fontweight='bold')
    plt.xlim(50, 105)
    plt.ylim(50, 100)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved: {output_path}")


def generate_all_plots(results_csv: str = "results/experiments/noise_sensitivity_summary.csv"):
    """Generate all plots for the paper."""
    df = pd.read_csv(results_csv)
    plot_f1_vs_noise(df)
    plot_iou_comparison(df)
    plot_precision_recall_tradeoff(df)
    print("\n✅ All plots generated!")


if __name__ == "__main__":
    generate_all_plots()
