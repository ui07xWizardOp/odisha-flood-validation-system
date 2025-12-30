import csv
import random
import math
import os
from datetime import datetime, timedelta

# Configuration same as main app
MIN_LAT, MAX_LAT = 19.5, 21.5
MIN_LON, MAX_LON = 84.5, 87.0
CUTTACK = (20.4625, 85.8830)

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

class LiteGenerator:
    def __init__(self, seed=42):
        random.seed(seed)
        self.users = self._generate_users(100)
        
    def _generate_users(self, n):
        users = {}
        for i in range(n):
            uid = i + 1
            if i < 70: score, cat = 0.9, 'reliable'
            elif i < 90: score, cat = 0.7, 'average'
            else: score, cat = 0.3, 'unreliable'
            users[uid] = {'id': uid, 'trust_score': 0.5, 'category': cat, 'accuracy': score}
        return users

    def generate_report(self, report_id, is_flood_event, noise_pct):
        # Determine if this report is "noisy" (malicious/erroneous) based on noise_pct
        is_noise = random.random() < (noise_pct / 100.0)
        
        # Pick a user (unreliable users more likely to be noise)
        if is_noise:
            # Pick from unreliable pool if possible
            u_pool = [u for u in self.users.values() if u['category'] == 'unreliable']
            if not u_pool: u_pool = list(self.users.values())
        else:
            u_pool = [u for u in self.users.values() if u['category'] != 'unreliable']
            if not u_pool: u_pool = list(self.users.values())
            
        user = random.choice(u_pool)
        
        # Ground Truth
        # Simple circular flood zone around Cuttack (15km radius)
        # Lat/Lon is generated. 
        # If is_flood_event=True, we target inside zone. Else outside.
        
        # Cuttack center
        cy, cx = CUTTACK
        
        if is_flood_event:
            # Generate point near Cuttack
            lat = cy + random.uniform(-0.1, 0.1)
            lon = cx + random.uniform(-0.1, 0.1)
            ground_truth = True
        else:
            # Generate point far away
            lat = cy + random.uniform(0.2, 0.5) * (1 if random.random()>0.5 else -1)
            lon = cx + random.uniform(0.2, 0.5) * (1 if random.random()>0.5 else -1)
            ground_truth = False
            
        # User claim
        if is_noise:
            claims_flood = not ground_truth # Lie
        else:
            claims_flood = ground_truth # Truth
            
        return {
            'report_id': report_id,
            'user_id': user['id'],
            'latitude': lat,
            'longitude': lon,
            'depth_meters': random.uniform(0.5, 3.0) if claims_flood else 0.0,
            'claims_flood': claims_flood,
            'ground_truth': ground_truth,
            'report_type': 'TP' if (claims_flood and ground_truth) else
                           'TN' if (not claims_flood and not ground_truth) else
                           'FP' if (claims_flood and not ground_truth) else 'FN'
        }

class LiteValidator:
    def validate(self, report, neighbors):
        # 1. Physical (Mock)
        # Assume flood zone is defined by distance to Cuttack < 15km (approx 0.15 deg)
        # In reality this uses DEM. Here we simulate "High Risk Zone" check.
        dist = haversine_km(report['latitude'], report['longitude'], *CUTTACK)
        in_risk_zone = dist < 20.0 # 20km
        
        l1 = 0.9 if in_risk_zone else 0.2
        if report['depth_meters'] > 5.0: l1 = 0.1 # Impossible depth
        
        # 2. Statistical
        # Check consensus with neighbors
        spatial = 0.5
        if neighbors:
            agree = sum(1 for n in neighbors if n['claims_flood'] == report['claims_flood'])
            spatial = agree / len(neighbors)
        l2 = spatial
        
        # 3. Reputation
        # Mock assumption: valid users have higher implicit score in this simulation
        # In prod this comes from DB
        l3 = 0.5 # Neutral start
        
        final = 0.4*l1 + 0.4*l2 + 0.2*l3
        return {'status': 'validated' if final >= 0.6 else 'flagged', 'score': final}

def run_lite_experiments():
    print("🧪 Running LITE Experiments (No Pandas)...")
    
    noise_levels = [5, 15, 30]
    results_summary = []
    
    gen = LiteGenerator()
    validator = LiteValidator()
    
    experiment_dir = os.path.join("results", "experiments")
    header = ["noise_level", "precision", "recall", "f1_score"]
    
    # Ensure dir exists
    if not os.path.exists(experiment_dir):
        os.makedirs(experiment_dir)
        
    csv_path = os.path.join(experiment_dir, "results.csv")
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for noise in noise_levels:
            # Generate batch
            reports = []
            for i in range(200): # 200 reports per level
                is_flood = i % 2 == 0 # 50/50 split
                r = gen.generate_report(i, is_flood, noise)
                reports.append(r)
            
            # Validate
            tp, fp, fn = 0, 0, 0
            for r in reports:
                # Find neighbors (naive O(N^2))
                neighbors = [n for n in reports 
                             if n['report_id'] != r['report_id'] 
                             and haversine_km(r['latitude'], r['longitude'], n['latitude'], n['longitude']) < 5.0]
                
                res = validator.validate(r, neighbors)
                pred_valid = (res['status'] == 'validated')
                
                # Only care about positive claims (flood reports)
                if r['claims_flood']:
                    if r['ground_truth'] and pred_valid: tp += 1
                    elif not r['ground_truth'] and pred_valid: fp += 1
                    elif r['ground_truth'] and not pred_valid: fn += 1
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            print(f"   Noise {noise}%: F1={f1:.3f} | Prec={precision:.3f} | Rec={recall:.3f}")
            results_summary.append((noise, precision, recall, f1))
            writer.writerow([noise, precision, recall, f1])

    print(f"✅ Results saved to {csv_path}")
    return results_summary

if __name__ == "__main__":
    run_lite_experiments()
