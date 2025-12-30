
import math

def create_svg_plot(results, output_path):
    width, height = 800, 400
    padding = 50
    graph_w = width - 2 * padding
    graph_h = height - 2 * padding
    
    # Results is list of (noise, prec, rec, f1)
    # X axis: Noise (5 to 30)
    # Y axis: Score (0 to 1)
    
    x_min, x_max = 0, 35
    y_min, y_max = 0.5, 1.0
    
    def scale_x(val): return padding + (val - x_min) / (x_max - x_min) * graph_w
    def scale_y(val): return height - padding - (val - y_min) / (y_max - y_min) * graph_h
    
    svg = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']
    svg.append('<rect width="100%" height="100%" fill="white"/>')
    
    # Grid and Axes
    svg.append(f'<line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" stroke="black"/>') # X axis
    svg.append(f'<line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height-padding}" stroke="black"/>') # Y axis
    
    # X labels
    for x in [5, 15, 30]:
        px = scale_x(x)
        svg.append(f'<text x="{px}" y="{height-padding+20}" text-anchor="middle">{x}%</text>')
        svg.append(f'<line x1="{px}" y1="{height-padding}" x2="{px}" y2="{height-padding+5}" stroke="black"/>')
    svg.append(f'<text x="{width/2}" y="{height-10}" text-anchor="middle" font-weight="bold">Noise Level</text>')
    
    # Y labels
    for y in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        py = scale_y(y)
        svg.append(f'<text x="{padding-10}" y="{py+5}" text-anchor="end">{y}</text>')
        svg.append(f'<line x1="{padding-5}" y1="{py}" x2="{padding}" y2="{py}" stroke="black"/>')
        svg.append(f'<line x1="{padding}" y1="{py}" x2="{width-padding}" y2="{py}" stroke="#ddd"/>') # Grid
        
    # Plot Lines
    colors = {'F1': 'blue', 'Precision': 'green', 'Recall': 'red'}
    indices = {'F1': 3, 'Precision': 1, 'Recall': 2}
    
    for metric, idx in indices.items():
        pts = ""
        for row in results:
            noise = row[0]
            val = row[idx]
            pts += f"{scale_x(noise)},{scale_y(val)} "
        
        svg.append(f'<polyline points="{pts}" fill="none" stroke="{colors[metric]}" stroke-width="3"/>')
        
        # Dots
        for row in results:
            noise = row[0]
            val = row[idx]
            svg.append(f'<circle cx="{scale_x(noise)}" cy="{scale_y(val)}" r="4" fill="{colors[metric]}"/>')

    # Legend
    svg.append('<rect x="650" y="50" width="100" height="80" fill="white" stroke="#ccc"/>')
    y_leg = 70
    for metric, color in colors.items():
        svg.append(f'<line x1="660" y1="{y_leg}" x2="680" y2="{y_leg}" stroke="{color}" stroke-width="3"/>')
        svg.append(f'<text x="690" y="{y_leg+4}" font-size="12">{metric}</text>')
        y_leg += 20
        
    svg.append('</svg>')
    
    with open(output_path, 'w') as f:
        f.write("\n".join(svg))
    print(f"📈 Plot saved to {output_path}")

if __name__ == "__main__":
    # Load results
    import csv
    results = []
    try:
        with open("results/experiments/results.csv", 'r') as f:
            reader = csv.reader(f)
            next(reader) # skip header
            for row in reader:
                results.append((float(row[0]), float(row[1]), float(row[2]), float(row[3])))
        
        create_svg_plot(results, "results/plots/f1_vs_noise.svg")
    except Exception as e:
        print(f"Error creating plot: {e}")
