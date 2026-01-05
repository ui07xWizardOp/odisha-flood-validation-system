"""
External Data Loader for Flood Data Ecosystem.

Loads data from CivicDataLab's flood-data-ecosystem-Odisha repository:
- OSDMA losses and damages (2019-2024)
- Odisha administrative boundaries (GeoJSON)
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class FloodDataLoader:
    """
    Loads external flood data from CivicDataLab repository.
    
    Data sources:
    - OSDMA: Losses and damages by district (2019-2024)
    - Maps: District/subdistrict GeoJSON boundaries
    """
    
    DATA_DIR = Path("data/external")
    
    def __init__(self):
        self.losses_damages_df = None
        self.subdistricts_geojson = None
    
    def load_osdma_losses(self) -> pd.DataFrame:
        """
        Load OSDMA district-level losses and damages data.
        
        Returns:
            DataFrame with columns: District, timeperiod, Population Affected,
            House Damage Total, Crop Loss Total, etc.
        """
        if self.losses_damages_df is not None:
            return self.losses_damages_df
        
        csv_path = self.DATA_DIR / "osdma_losses_damages.csv"
        
        if not csv_path.exists():
            logger.warning(f"OSDMA data not found: {csv_path}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(csv_path)
            
            # Clean district names
            df['District'] = df['District'].str.strip().str.title()
            
            # Parse numeric columns (handle commas in numbers)
            numeric_cols = [
                'No. of person evacuated', 'No. of Persons Rescued',
                'Population Affected', 'Total Livestock Lost',
                'House Damage Total', 'Cultivated Area affected in Hectare',
                'Crop Loss Total in hact.', 'Total No. Of Death of Humans In Flood & Cyclone'
            ]
            
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(',', '').str.strip(),
                        errors='coerce'
                    ).fillna(0).astype(int)
            
            self.losses_damages_df = df
            logger.info(f"Loaded OSDMA data: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load OSDMA data: {e}")
            return pd.DataFrame()
    
    def get_district_summary(self, district: str) -> Dict:
        """
        Get flood impact summary for a specific district.
        
        Args:
            district: District name (e.g., "Kendrapara", "Puri")
            
        Returns:
            Dict with aggregated statistics
        """
        df = self.load_osdma_losses()
        
        if df.empty:
            return {"error": "No data available"}
        
        district = district.strip().title()
        district_data = df[df['District'] == district]
        
        if district_data.empty:
            return {"error": f"District '{district}' not found"}
        
        return {
            "district": district,
            "years_covered": district_data['timeperiod'].unique().tolist(),
            "total_population_affected": int(district_data['Population Affected'].sum()),
            "total_houses_damaged": int(district_data['House Damage Total'].sum()),
            "total_evacuated": int(district_data['No. of person evacuated'].sum()),
            "total_rescued": int(district_data['No. of Persons Rescued'].sum()),
            "total_crop_loss_hectares": float(district_data['Crop Loss Total in hact.'].sum()),
            "total_deaths": int(district_data['Total No. Of Death of Humans In Flood & Cyclone'].sum()),
            "cyclone_fani_affected": int(district_data['Population Affected in Cyclone Fani '].sum()) if 'Population Affected in Cyclone Fani ' in district_data.columns else 0
        }
    
    def get_high_impact_districts(self, top_n: int = 10) -> pd.DataFrame:
        """
        Get districts ranked by total flood impact.
        
        Args:
            top_n: Number of top districts to return
            
        Returns:
            DataFrame with district rankings
        """
        df = self.load_osdma_losses()
        
        if df.empty:
            return pd.DataFrame()
        
        # Aggregate by district
        summary = df.groupby('District').agg({
            'Population Affected': 'sum',
            'House Damage Total': 'sum',
            'Total No. Of Death of Humans In Flood & Cyclone': 'sum'
        }).reset_index()
        
        summary.columns = ['District', 'Total_Population_Affected', 'Total_Houses_Damaged', 'Total_Deaths']
        
        # Calculate impact score
        summary['Impact_Score'] = (
            summary['Total_Population_Affected'] / 1000000 * 0.5 +
            summary['Total_Houses_Damaged'] / 100000 * 0.3 +
            summary['Total_Deaths'] / 100 * 0.2
        )
        
        return summary.sort_values('Impact_Score', ascending=False).head(top_n)
    
    def load_subdistricts_geojson(self) -> Optional[Dict]:
        """
        Load Odisha subdistricts GeoJSON.
        
        Returns:
            GeoJSON dict with subdistrict boundaries
        """
        if self.subdistricts_geojson is not None:
            return self.subdistricts_geojson
        
        geojson_path = self.DATA_DIR / "odisha_subdistricts.geojson"
        
        if not geojson_path.exists():
            logger.warning(f"GeoJSON not found: {geojson_path}")
            return None
        
        try:
            with open(geojson_path, 'r', encoding='utf-8') as f:
                self.subdistricts_geojson = json.load(f)
            
            feature_count = len(self.subdistricts_geojson.get('features', []))
            logger.info(f"Loaded GeoJSON with {feature_count} subdistricts")
            return self.subdistricts_geojson
            
        except Exception as e:
            logger.error(f"Failed to load GeoJSON: {e}")
            return None
    
    def get_yearly_trend(self, district: Optional[str] = None) -> pd.DataFrame:
        """
        Get yearly flood impact trend.
        
        Args:
            district: Optional district filter
            
        Returns:
            DataFrame with yearly statistics
        """
        df = self.load_osdma_losses()
        
        if df.empty:
            return pd.DataFrame()
        
        if district:
            df = df[df['District'] == district.strip().title()]
        
        yearly = df.groupby('timeperiod').agg({
            'District': 'count',
            'Population Affected': 'sum',
            'House Damage Total': 'sum',
            'Total No. Of Death of Humans In Flood & Cyclone': 'sum'
        }).reset_index()
        
        yearly.columns = ['Year', 'Districts_Reporting', 'Population_Affected', 'Houses_Damaged', 'Deaths']
        
        return yearly


# Singleton instance
flood_data_loader = FloodDataLoader()


if __name__ == "__main__":
    print("📊 Flood Data Loader")
    print("-" * 40)
    
    # Load data
    df = flood_data_loader.load_osdma_losses()
    print(f"Loaded {len(df)} records")
    
    # Get high impact districts
    print("\n🔥 High Impact Districts:")
    high_impact = flood_data_loader.get_high_impact_districts(5)
    print(high_impact.to_string())
    
    # Get Kendrapara summary
    print("\n📍 Kendrapara Summary:")
    summary = flood_data_loader.get_district_summary("Kendrapara")
    for key, value in summary.items():
        print(f"  {key}: {value:,}" if isinstance(value, (int, float)) else f"  {key}: {value}")
