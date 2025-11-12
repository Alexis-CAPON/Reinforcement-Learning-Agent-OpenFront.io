#!/usr/bin/env python3
"""
Crop Map Tool
Creates a new smaller map by cropping a region from an existing map
"""

import os
import json
import struct
import argparse
from pathlib import Path


def read_map_binary(map_path: Path, manifest_path: Path) -> tuple[int, int, list[int]]:
    """Read map binary file and return width, height, and terrain data"""
    # Read dimensions from manifest.json (binary has NO header!)
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        width = manifest['map']['width']
        height = manifest['map']['height']

    # Read raw terrain data (NO header, just width*height bytes)
    with open(map_path, 'rb') as f:
        terrain = []
        byte_values = {}  # Debug: count byte values

        for i in range(width * height):
            byte = f.read(1)
            if not byte:
                raise ValueError(f"Map file too short! Expected {width*height} bytes")

            byte_val = byte[0]
            byte_values[byte_val] = byte_values.get(byte_val, 0) + 1

            # Store the actual byte value (preserves terrain type, elevation, etc.)
            terrain.append(byte_val)

        # Debug output
        print(f"Debug: Byte values found in map: {byte_values}")

    return width, height, terrain


def write_map_binary(map_path: Path, width: int, height: int, terrain: list[int]):
    """Write map binary file (NO header, just raw terrain data)"""
    with open(map_path, 'wb') as f:
        # Write terrain data (preserve actual byte values)
        for byte_val in terrain:
            f.write(bytes([byte_val]))


def crop_map(source_map: str, output_name: str, x: int, y: int, width: int, height: int, base_game_dir: Path):
    """Crop a map and save as new map"""

    # Paths
    source_dir = base_game_dir / "map-generator" / "generated" / "maps" / source_map
    output_dir = base_game_dir / "map-generator" / "generated" / "maps" / output_name

    if not source_dir.exists():
        print(f"Error: Source map not found at {source_dir}")
        return False

    print(f"Reading source map: {source_map}")

    # Read source map
    source_bin = source_dir / "map.bin"
    source_manifest = source_dir / "manifest.json"
    source_width, source_height, source_terrain = read_map_binary(source_bin, source_manifest)

    print(f"Source map dimensions: {source_width}x{source_height}")
    print(f"Cropping region: x={x}, y={y}, width={width}, height={height}")

    # Debug: Sample some tiles from the source map to verify it has land
    sample_land_count = sum(1 for byte_val in source_terrain if byte_val & 128)
    print(f"Source map total land tiles: {sample_land_count} / {len(source_terrain)} ({sample_land_count/len(source_terrain)*100:.1f}%)")

    # Validate crop region
    if x < 0 or y < 0 or x + width > source_width or y + height > source_height:
        print(f"Error: Crop region out of bounds!")
        print(f"Valid range: x=[0, {source_width-width}], y=[0, {source_height-height}]")
        return False

    # Extract cropped terrain
    cropped_terrain = []
    num_land_tiles = 0

    # Debug: Sample center tile
    center_x = x + width // 2
    center_y = y + height // 2
    center_idx = center_y * source_width + center_x
    center_byte = source_terrain[center_idx] if center_idx < len(source_terrain) else 0
    center_is_land = bool(center_byte & 128)
    print(f"Debug: Center tile at ({center_x}, {center_y}) is {'LAND' if center_is_land else 'WATER'}")

    for crop_y in range(height):
        for crop_x in range(width):
            # Map crop coordinates to source coordinates
            source_x = x + crop_x
            source_y = y + crop_y
            source_idx = source_y * source_width + source_x

            byte_val = source_terrain[source_idx]
            cropped_terrain.append(byte_val)
            if byte_val & 128:  # Check bit 7 for land
                num_land_tiles += 1

    print(f"Cropped map has {num_land_tiles} land tiles ({num_land_tiles/(width*height)*100:.1f}% land)")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write cropped map binary
    output_bin = output_dir / "map.bin"
    write_map_binary(output_bin, width, height, cropped_terrain)
    print(f"Wrote: {output_bin}")

    # Generate mini map (half resolution)
    mini_width = width // 2
    mini_height = height // 2
    mini_terrain = []
    mini_land_tiles = 0

    for mini_y in range(mini_height):
        for mini_x in range(mini_width):
            # Sample 2x2 region from full cropped map
            sample_x = mini_x * 2
            sample_y = mini_y * 2

            # Check if any of the 4 pixels in 2x2 region is land
            is_land = False
            land_byte_val = 0
            for dy in range(2):
                for dx in range(2):
                    if sample_y + dy < height and sample_x + dx < width:
                        idx = (sample_y + dy) * width + (sample_x + dx)
                        byte_val = cropped_terrain[idx]
                        if byte_val & 128:  # Check bit 7 for land
                            is_land = True
                            land_byte_val = byte_val  # Use first land value found
                            break
                if is_land:
                    break

            # Use the land byte value if found, otherwise use water (63)
            mini_terrain.append(land_byte_val if is_land else 63)
            if is_land:
                mini_land_tiles += 1

    # Write mini map binary
    mini_output_bin = output_dir / "mini_map.bin"
    write_map_binary(mini_output_bin, mini_width, mini_height, mini_terrain)
    print(f"Wrote: {mini_output_bin}")

    # Create manifest.json
    manifest = {
        "name": output_name,
        "map": {
            "width": width,
            "height": height,
            "num_land_tiles": num_land_tiles
        },
        "mini_map": {
            "width": mini_width,
            "height": mini_height,
            "num_land_tiles": mini_land_tiles
        },
        "nations": [],
        "source": {
            "original_map": source_map,
            "crop_region": {
                "x": x,
                "y": y,
                "width": width,
                "height": height
            }
        }
    }

    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote: {manifest_path}")

    print(f"\n✅ Created new map: {output_name}")
    print(f"   Location: {output_dir}")
    print(f"   Map: {width}x{height} ({num_land_tiles} land tiles)")
    print(f"   Mini map: {mini_width}x{mini_height} ({mini_land_tiles} land tiles)")

    return True


def main():
    parser = argparse.ArgumentParser(description='Crop a map to create a smaller map')
    parser.add_argument('--source', type=str, required=True, help='Source map name (e.g., australia)')
    parser.add_argument('--output', type=str, required=True, help='Output map name (e.g., australia_small)')
    parser.add_argument('--x', type=int, required=True, help='Crop X coordinate')
    parser.add_argument('--y', type=int, required=True, help='Crop Y coordinate')
    parser.add_argument('--width', type=int, required=True, help='Crop width')
    parser.add_argument('--height', type=int, required=True, help='Crop height')
    parser.add_argument('--base-game-dir', type=str, help='Path to base-game directory')

    args = parser.parse_args()

    # Default base-game directory
    if args.base_game_dir:
        base_game_dir = Path(args.base_game_dir)
    else:
        # Assume we're in phase4-implementation/tools
        base_game_dir = Path(__file__).parent.parent.parent / "base-game"

    if not base_game_dir.exists():
        print(f"Error: base-game directory not found at {base_game_dir}")
        print("Use --base-game-dir to specify the correct path")
        return 1

    success = crop_map(
        source_map=args.source,
        output_name=args.output,
        x=args.x,
        y=args.y,
        width=args.width,
        height=args.height,
        base_game_dir=base_game_dir
    )

    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
