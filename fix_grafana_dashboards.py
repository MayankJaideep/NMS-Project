#!/usr/bin/env python3
"""
Fix Grafana Dashboards
- Set proper datasource (Prometheus)
- Handle "No Value" scenarios
- Set decimals to 0
"""

import json
import os
from pathlib import Path

DASHBOARD_DIR = Path("/home/sujan-rathod/Desktop/NMS/NMS project/config/grafana/dashboards")

def fix_panel(panel):
    """Fix a single panel configuration"""
    
    # 1. Set datasource to Prometheus
    if "datasource" not in panel or panel["datasource"] is None:
        panel["datasource"] = {
            "type": "prometheus",
            "uid": "prometheus"
        }
    elif isinstance(panel["datasource"], dict):
        panel["datasource"]["type"] = "prometheus"
        if "uid" not in panel["datasource"]:
            panel["datasource"]["uid"] = "prometheus"
    
    # 2. Fix targets (queries) datasource
    if "targets" in panel:
        for target in panel["targets"]:
            if "datasource" not in target or target["datasource"] is None:
                target["datasource"] = {
                    "type": "prometheus",
                    "uid": "prometheus"
                }
            elif isinstance(target["datasource"], dict):
                target["datasource"]["type"] = "prometheus"
                if "uid" not in target["datasource"]:
                    target["datasource"]["uid"] = "prometheus"
    
    # 3. Add fieldConfig with decimals and noValue handling
    if "fieldConfig" not in panel:
        panel["fieldConfig"] = {"defaults": {}, "overrides": []}
    
    if "defaults" not in panel["fieldConfig"]:
        panel["fieldConfig"]["defaults"] = {}
    
    defaults = panel["fieldConfig"]["defaults"]
    
    # Set decimals to 0
    defaults["decimals"] = 0
    
    # Handle no value
    defaults["noValue"] = "0"
    
    # Add unit if not present (for better display)
    if "unit" not in defaults:
        # Determine unit based on panel title or leave as default
        title = panel.get("title", "").lower()
        if "percent" in title or "utilization" in title or "cpu" in title or "memory" in title:
            defaults["unit"] = "percent"
        elif "mbps" in title or "bandwidth" in title:
            defaults["unit"] = "Mbps"
        elif "latency" in title or "seconds" in title:
            defaults["unit"] = "s"
    
    # Ensure thresholds exist
    if "thresholds" not in defaults:
        defaults["thresholds"] = {
            "mode": "absolute",
            "steps": [
                {"color": "green", "value": None}
            ]
        }
    
    # 4. Fix options for better display
    if "options" in panel:
        options = panel["options"]
        
        # For stat panels
        if panel.get("type") == "stat":
            if "reduceOptions" not in options:
                options["reduceOptions"] = {}
            if "calcs" not in options["reduceOptions"]:
                options["reduceOptions"]["calcs"] = ["lastNotNull"]
            
            # Show value
            options["textMode"] = "value"
            options["colorMode"] = "value"
        
        # For time series panels
        if panel.get("type") == "timeseries":
            if "legend" not in options:
                options["legend"] = {}
            options["legend"]["displayMode"] = "list"
            options["legend"]["placement"] = "bottom"
            options["legend"]["showLegend"] = True
            
            if "tooltip" not in options:
                options["tooltip"] = {}
            options["tooltip"]["mode"] = "multi"
    
    return panel

def fix_dashboard(filepath):
    """Fix a dashboard JSON file"""
    print(f"Processing: {filepath.name}")
    
    try:
        with open(filepath, 'r') as f:
            dashboard = json.load(f)
        
        # Fix each panel
        if "panels" in dashboard:
            for panel in dashboard["panels"]:
                if panel is None:
                    continue
                
                # Fix main panel
                fix_panel(panel)
                
                # Fix nested panels (row panels)
                if "panels" in panel:
                    for nested_panel in panel["panels"]:
                        if nested_panel is not None:
                            fix_panel(nested_panel)
        
        # Set dashboard-level defaults
        if "editable" not in dashboard:
            dashboard["editable"] = True
        
        # Set refresh interval
        if "refresh" not in dashboard:
            dashboard["refresh"] = "30s"
        
        # Set time range
        if "time" not in dashboard:
            dashboard["time"] = {
                "from": "now-15m",
                "to": "now"
            }
        
        # Save fixed dashboard
        with open(filepath, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        print(f"  ✅ Fixed: {filepath.name}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error fixing {filepath.name}: {e}")
        return False

def main():
    print("=" * 70)
    print("  GRAFANA DASHBOARD FIXER")
    print("=" * 70)
    print()
    
    # Find all JSON files in dashboard directory
    json_files = list(DASHBOARD_DIR.glob("*.json"))
    
    if not json_files:
        print("❌ No JSON files found in dashboard directory")
        return
    
    print(f"Found {len(json_files)} dashboard(s):\n")
    
    success_count = 0
    for filepath in json_files:
        if fix_dashboard(filepath):
            success_count += 1
        print()
    
    print("=" * 70)
    print(f"  SUMMARY")
    print("=" * 70)
    print(f"Total dashboards: {len(json_files)}")
    print(f"Successfully fixed: {success_count}")
    print(f"Failed: {len(json_files) - success_count}")
    print()
    
    if success_count == len(json_files):
        print("✅ All dashboards fixed successfully!")
        print()
        print("Changes applied:")
        print("  • Set datasource to Prometheus")
        print("  • Decimals set to 0")
        print("  • No value displays as '0'")
        print("  • Proper units configured")
        print("  • Refresh interval: 30s")
        print()
        print("Next steps:")
        print("  1. Restart Grafana: docker-compose restart grafana")
        print("  2. Reload dashboards in Grafana")
        print("  3. Check that data is displayed")
    else:
        print("⚠️  Some dashboards had errors. Check output above.")
    
    print()

if __name__ == "__main__":
    main()
