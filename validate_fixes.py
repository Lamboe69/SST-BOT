#!/usr/bin/env python3
"""
Validation Script - Check Trade Execution and Line Chart Configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from line_chart_config import LINE_CHART_CONFIG

def validate_configuration():
    """Validate that all fixes are properly applied"""
    
    print("VALIDATING BOT CONFIGURATION...")
    print("=" * 50)
    
    # Check Line Chart Configuration
    config = LINE_CHART_CONFIG.get_config()
    
    print("LINE CHART CONFIGURATION:")
    print(f"   Line Chart Mode: {config['line_chart_mode']}")
    print(f"   Use Closing Prices Only: {config['use_closing_prices_only']}")
    print(f"   Swing Detection Method: {config['swing_detection_method']}")
    print(f"   Level Break Method: {config['level_break_method']}")
    print(f"   Rejection Detection Method: {config['rejection_detection_method']}")
    
    print("\nTRADE EXECUTION CONFIGURATION:")
    print(f"   Auto Execute Trades: {config['auto_execute_trades']}")
    print(f"   Trade Execution Enabled: {config['trade_execution_enabled']}")
    
    # Validation Results
    print("\n" + "=" * 50)
    print("VALIDATION RESULTS:")
    
    all_good = True
    
    if not config['line_chart_mode']:
        print("   [X] Line Chart Mode is DISABLED")
        all_good = False
    else:
        print("   [OK] Line Chart Mode is ENABLED")
    
    if not config['auto_execute_trades']:
        print("   [X] Auto Execute Trades is DISABLED")
        all_good = False
    else:
        print("   [OK] Auto Execute Trades is ENABLED")
    
    if not config['trade_execution_enabled']:
        print("   [X] Trade Execution is DISABLED")
        all_good = False
    else:
        print("   [OK] Trade Execution is ENABLED")
    
    if not config['use_closing_prices_only']:
        print("   [X] Not using closing prices only")
        all_good = False
    else:
        print("   [OK] Using closing prices only (Line Chart)")
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("SUCCESS: ALL FIXES APPLIED!")
        print("   - Trade execution is ENABLED")
        print("   - Line chart mode is ACTIVE")
        print("   - Bot will use closing prices only")
        print("   - Trades will be executed automatically")
    else:
        print("WARNING: SOME ISSUES FOUND - Check configuration")
    
    return all_good

if __name__ == "__main__":
    validate_configuration()