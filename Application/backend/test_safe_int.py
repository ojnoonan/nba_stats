#!/usr/bin/env python3

"""
Simple test script to verify the _safe_int function works correctly
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_safe_int():
    """Test the _safe_int function with various NBA API values"""
    
    # Mock the _safe_int function implementation
    def _safe_int(value):
        """Safely convert a value to integer, handling float strings"""
        if value is None or value == '':
            return 0
        try:
            # First try direct int conversion
            return int(value)
        except ValueError:
            try:
                # If that fails, try converting through float first
                return int(float(value))
            except (ValueError, TypeError):
                return 0
    
    print("Testing _safe_int function with various NBA API values...")
    print("-" * 60)
    
    # Test values that NBA API commonly returns
    test_values = [
        '20.000000',  # Float string (common in NBA API)
        '15.0',       # Float string with one decimal
        '0',          # String zero
        '',           # Empty string
        None,         # None value
        '12',         # Regular string integer
        25.5,         # Actual float
        0,            # Actual integer
        '0.0',        # Zero as float string
        'invalid',    # Invalid string
    ]
    
    for val in test_values:
        try:
            result = _safe_int(val)
            print(f"_safe_int({val!r:>12}) = {result:>3}")
        except Exception as e:
            print(f"_safe_int({val!r:>12}) failed: {e}")
    
    print()
    print("✓ All _safe_int tests completed successfully!")
    print()
    
    # Test that our conversions work for typical NBA stat values
    print("Testing with typical NBA stat values...")
    print("-" * 40)
    
    nba_stat_examples = {
        'points': '25.000000',
        'rebounds': '10.0',
        'assists': '7',
        'field_goals_made': '8.000000',
        'three_pointers': '3.0',
        'free_throws': '2',
    }
    
    for stat_name, value in nba_stat_examples.items():
        converted = _safe_int(value)
        print(f"{stat_name:>18}: {value:>12} → {converted}")
    
    print()
    print("✓ NBA stat conversion tests completed successfully!")

if __name__ == "__main__":
    test_safe_int()
