"""
Study Area Map Generator
Generates Figure 2: Mahanadi Delta Study Area Map
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from pathlib import Path

# Output directory
OUTPUT_DIR = Path("docs/paper/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_study_area_map():
    """Generate study area map for Mahanadi Delta"""
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Mahanadi Delta approximate boundary (simplified polygon)
    # Bounding box: 19.5°N - 21.5°N, 84.5°E - 87.0°E
    
    # Create a stylized map representation
    # Background - Bay of Bengal
    ax.fill([84.5, 87.5, 87.5, 84.5], [19.0, 19.0, 22.0, 22.0], 
            color='#e3f2fd', alpha=0.5, label='Bay of Bengal')
    
    # Odisha state outline (simplified)
    odisha_x = [84.5, 85.0, 85.5, 86.5, 87.0, 86.8, 86.0, 85.5, 84.8, 84.5]
    odisha_y = [21.8, 22.0, 21.8, 21.5, 21.0, 20.0, 19.5, 19.8, 20.5, 21.8]
    ax.fill(odisha_x, odisha_y, color='#c8e6c9', alpha=0.7, edgecolor='#2e7d32', linewidth=2)
    
    # Mahanadi Delta (study area) - highlighted
    delta_x = [85.8, 86.0, 86.5, 86.8, 86.5, 86.0, 85.5, 85.3, 85.8]
    delta_y = [20.8, 21.0, 20.8, 20.2, 19.8, 19.6, 19.8, 20.3, 20.8]
    ax.fill(delta_x, delta_y, color='#ffab91', alpha=0.8, edgecolor='#bf360c', 
            linewidth=3, label='Study Area')
    
    # Mahanadi River (main channel)
    river_x = [84.8, 85.2, 85.5, 85.8, 86.0, 86.3, 86.5]
    river_y = [21.5, 21.2, 20.9, 20.6, 20.3, 20.0, 19.7]
    ax.plot(river_x, river_y, color='#1565c0', linewidth=4, label='Mahanadi River')
    
    # Distributaries
    for offset in [-0.1, 0.1, 0.2]:
        dist_x = [86.0, 86.2, 86.4]
        dist_y = [20.3 + offset, 20.0 + offset*0.5, 19.7 + offset*0.3]
        ax.plot(dist_x, dist_y, color='#42a5f5', linewidth=2, alpha=0.7)
    
    # Key cities/districts
    cities = {
        'Cuttack': (85.9, 20.45),
        'Bhubaneswar': (85.83, 20.27),
        'Puri': (85.85, 19.8),
        'Kendrapara': (86.42, 20.5),
        'Bhadrak': (86.5, 21.05),
        'Paradip': (86.6, 20.3),
    }
    
    for city, (lon, lat) in cities.items():
        ax.plot(lon, lat, 'ko', markersize=8)
        ax.annotate(city, (lon, lat), xytext=(5, 5), textcoords='offset points',
                    fontsize=9, fontweight='bold')
    
    # Add scale and north arrow
    ax.annotate('N', xy=(87.2, 21.7), fontsize=16, fontweight='bold', ha='center')
    ax.annotate('↑', xy=(87.2, 21.5), fontsize=24, ha='center')
    
    # Scale bar
    ax.plot([84.7, 85.2], [19.2, 19.2], 'k-', linewidth=3)
    ax.annotate('50 km', xy=(84.95, 19.1), fontsize=10, ha='center')
    
    # Bounding box annotation
    bbox_text = "Study Area:\n19.5°N - 21.5°N\n84.5°E - 87.0°E\n~9,500 km²"
    ax.text(84.6, 21.5, bbox_text, fontsize=10, 
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    # Labels
    ax.set_xlabel('Longitude (°E)', fontsize=12)
    ax.set_ylabel('Latitude (°N)', fontsize=12)
    ax.set_title('Study Area: Mahanadi Delta, Odisha, India', fontsize=14, fontweight='bold')
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='#c8e6c9', edgecolor='#2e7d32', label='Odisha State'),
        mpatches.Patch(facecolor='#ffab91', edgecolor='#bf360c', label='Study Area (Delta)'),
        plt.Line2D([0], [0], color='#1565c0', linewidth=3, label='Mahanadi River'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='black', 
                   markersize=8, label='Major Cities'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=9)
    
    # Set limits
    ax.set_xlim(84.4, 87.5)
    ax.set_ylim(19.0, 22.2)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add "Bay of Bengal" label
    ax.text(87.0, 19.3, 'Bay of\nBengal', fontsize=12, 
            fontstyle='italic', color='#1565c0', ha='center')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'study_area_map.pdf', bbox_inches='tight', dpi=300)
    plt.savefig(OUTPUT_DIR / 'study_area_map.png', bbox_inches='tight', dpi=300)
    print(f"✓ Saved: study_area_map.pdf")
    plt.close()


if __name__ == "__main__":
    print("Generating study area map...")
    generate_study_area_map()
    print("Done!")
