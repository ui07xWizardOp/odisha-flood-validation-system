import os
import subprocess
from pathlib import Path
import rasterio
import numpy as np

class HANDCalculator:
    """
    Calculates Height Above Nearest Drainage (HAND) using WhiteboxTools.
    Prerequisite: WhiteboxTools executable must be in PATH or specified.
    """

    def __init__(self, wbt_path: str = "whitebox_tools", temp_dir: str = "data/temp"):
        """
        Args:
            wbt_path (str): Path to whitebox_tools executable. Defaults to 'whitebox_tools' (assumed in PATH).
            temp_dir (str): Directory for intermediate files.
        """
        self.wbt_path = wbt_path
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _run_wbt_command(self, tool_name: str, args: list) -> None:
        """Helper to run a WhiteboxTools command."""
        cmd = [self.wbt_path, f"-r={tool_name}"] + args
        # Add verbose flag if needed: cmd.append("-v")
        
        print(f"Running WBT Tool: {tool_name}...")
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            # print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error running {tool_name}: {e.stderr}")
            raise RuntimeError(f"WhiteboxTools {tool_name} failed.")

    def calculate_hand(self, dem_path: str, output_path: str, stream_threshold: int = 1000) -> None:
        """
        Computes HAND from a DEM.

        Pipeline:
        1. Fill Depressions
        2. D8 Pointer (Flow Direction)
        3. D8 Flow Accumulation
        4. Extract Streams
        5. Elevation Above Stream (HAND)

        Args:
            dem_path (str): Path to input DEM GeoTIFF.
            output_path (str): Path to save HAND GeoTIFF.
            stream_threshold (int): Flow accumulation threshold to define streams.
        """
        dem_path = str(Path(dem_path).absolute())
        output_path = str(Path(output_path).absolute())
        temp_dir = str(self.temp_dir.absolute())

        # Intermediate files
        filled_dem = os.path.join(temp_dir, "filled_dem.tif")
        d8_pointer = os.path.join(temp_dir, "d8_pointer.tif")
        flow_accum = os.path.join(temp_dir, "flow_accum.tif")
        streams = os.path.join(temp_dir, "streams.tif")

        try:
            # 1. Fill Depressions
            self._run_wbt_command("FillDepressions", [f"-i={dem_path}", f"-o={filled_dem}"])

            # 2. D8 Pointer
            self._run_wbt_command("D8Pointer", [f"-i={filled_dem}", f"-o={d8_pointer}"])

            # 3. D8 Flow Accumulation
            self._run_wbt_command("D8FlowAccumulation", [f"-i={d8_pointer}", f"-o={flow_accum}"])

            # 4. Extract Streams
            self._run_wbt_command("ExtractStreams", [f"--flow_accum={flow_accum}", f"-o={streams}", f"--threshold={stream_threshold}"])

            # 5. Elevation Above Stream (HAND)
            # WhiteboxTools tool for HAND is often "ElevationAboveStream"
            self._run_wbt_command("ElevationAboveStream", [f"-i={filled_dem}", f"--streams={streams}", f"-o={output_path}"])

            print(f"HAND calculation complete. Saved to {output_path}")

        except Exception as e:
            print(f"HAND calculation failed: {e}")
            raise

if __name__ == "__main__":
    # Example usage
    # Ensure whitebox_tools is installed and accessible
    # calculator = HANDCalculator()
    # calculator.calculate_hand("data/processed/mahanadi_dem_30m.tif", "data/processed/mahanadi_hand.tif")
    pass
