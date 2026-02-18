#!/usr/bin/env python3
"""
global_dedupe.py - Deduplicate data across all collected repositories.

Usage:
    python3 scripts/global_dedupe.py --data-dir ./autotrain_repos --output ./start_training_data.jsonl
"""

import argparse
import hashlib
import json
import os
import sys
from glob import glob
from tqdm import tqdm

# Add project root to sys.path to allow importing heidi_engine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_hash(obj):
    """Generate a hash for the sample content (instruction + input + output)."""
    # specific fields to check for dupe (we might ignore metadata)
    content = f"{obj.get('instruction', '')}|{obj.get('input', '')}|{obj.get('output', '')}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Deduplicate JSONL files recursively")
    parser.add_argument("--data-dir", type=str, required=True, help="Root directory containing repo outputs")
    parser.add_argument("--output", type=str, required=True, help="Output file for merged dataset")
    args = parser.parse_args()

    # Find all clean_round_*.jsonl files
    print(f"Scanning {args.data_dir} for data files...")
    files = glob(os.path.join(args.data_dir, "**", "clean_round_*.jsonl"), recursive=True)
    
    if not files:
        # Fallback to look for tested or raw if clean not found? user wants 'clean' usually.
        print("No clean_round_*.jsonl files found.")
        return

    print(f"Found {len(files)} files.")
    
    seen_hashes = set()
    total_samples = 0
    unique_samples = 0
    
    with open(args.output, 'w') as out_f:
        for jsonl_file in tqdm(files, desc="Processing files"):
            try:
                with open(jsonl_file, 'r') as in_f:
                    for line in in_f:
                        line = line.strip()
                        if not line: continue
                        
                        try:
                            data = json.loads(line)
                            start_count = total_samples
                            total_samples += 1
                            
                            h = get_hash(data)
                            if h not in seen_hashes:
                                seen_hashes.add(h)
                                out_f.write(line + "\n")
                                unique_samples += 1
                                
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"Error reading {jsonl_file}: {e}")

    print(f"Finished.")
    print(f"Total processed: {total_samples}")
    print(f"Unique saved:    {unique_samples}")
    print(f"Duplicates:      {total_samples - unique_samples}")
    print(f"Output:          {args.output}")

if __name__ == "__main__":
    main()
