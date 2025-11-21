#!/usr/bin/env python3
"""
Update Grafana Dashboards - Final Configuration
- Set datasource to "grafana" (default)
- Set noValue to "-" (dash)
- Set decimals to 0 for all numerical data
"""

import json
import os
from pathlib import Path

DASHBOARD_DIR = Path("/home/sujan-rathod/Desktop/NMS/NMS project/config/grafana/dashboards")

def update_panel(panel):
    """Update a single panel with specified configuration"""
    
    # 1. Set datasource to default (grafana)
    panel["datasource"] = {
        "type": "prometheus",
        "uid": "${DS_PROMETHEUS}"
    }
    
    # 2. Update targets datasource
    if "targets" in panel:
        for target in panel["targets"]:
            target["datasource"] = {
                "type": "prometheus",
                "uid": "${DS_PROMETHEUS}"
            }
    
    # 3. Configure fieldConfig
    if "fieldConfig" not in panel:
        panel["fieldConfig"] = {"defaults": {}, "overrides": []}
    
    if "defaults" not in panel["fieldConfig"]:
        panel["fieldConfig"]["defaults"] = {}
    
    defaults = panel["fieldConfig"]["defaults"]
    
    # Set decimals to 0 for numerical data
    defaults["decimals"] = 0
    
    # Set noValue to "-" (dash)
    defaults["noValue"] = "-"
    
    # Ensure color and thresholds exist
    if "color" not in defaults:
        defaults["color"] = {"mode": "palette-classic"}
    
    if "thresholds" not in defaults:
        defaults["thresholds"] = {
            "mode": "absolute",
            "steps": [
                {"color": "green", "value": None},
                {"color": "yellow", "value": 70},
                {"color": "red", "value": 90}
            ]
        }
    
    # 4. Update panel options
    if "options" in panel:
        options = panel["options"]
        
        # For stat panels
        if panel.get("type") == "stat":
            options["colorMode"] = "value"
            options["graphMode"] = "area"
            options["textMode"] = "value"
            
            if "reduceOptions" not in options:
                options["reduceOptions"] = {}
            options["reduceOptions"]["calcs"] = ["lastNotNull"]
            options["reduceOptions"]["fields"] = ""
            options["reduceOptions"]["values"] = False
        
        # For timeseries panels
        elif panel.get("type") == "timeseries":
            if "legend" not in options:
                options["legend"] = {}
            options["legend"]["displayMode"] = "list"
            options["legend"]["placement"] = "bottom"
            options["legend"]["showLegend"] = True
            
            if "tooltip" not in options:
                options["tooltip"] = {}
            options["tooltip"]["mode"] = "multi"
            options["tooltip"]["sort"] = "none"
    
    return panel

def update_dashboard(filepath):
    """Update a dashboard JSON file"""
    print(f"📝 Processing: {filepath.name}")
    
    try:
        with open(filepath, 'r') as f:
            dashboard = json.load(f)
        
        # Update each panel
        if "panels" in dashboard:
            panel_count = 0
            for panel in dashboard["panels"]:
                if panel is None:
                    continue
                
                # Update main panel
                update_panel(panel)
                panel_count += 1
                
                # Update nested panels (for row panels)
                if "panels" in panel:
                    for nested_panel in panel["panels"]:
                        if nested_panel is not None:
                            update_panel(nested_panel)
                            panel_count += 1
            
            print(f"   ✅ Updated {panel_count} panels")
        
        # Set dashboard-level configuration
        dashboard["editable"] = True
        dashboard["refresh"] = "30s"
        
        if "time" not in dashboard:
            dashboard["time"] = {
                "from": "now-15m",
                "to": "now"
            }
        
        # Add templating for datasource variable
        if "templating" not in dashboard:
            dashboard["templating"] = {"list": []}
        
        # Check if DS_PROMETHEUS variable exists
        has_ds_var = False
        for var in dashboard["templating"]["list"]:
            if var.get("name") == "DS_PROMETHEUS":
                has_ds_var = True
                break
        
        if not has_ds_var:
            dashboard["templating"]["list"].insert(0, {
                "current": {
                    "selected": False,
                    "text": "Prometheus",
                    "value": "Prometheus"
                },
                "hide": 0,
                "includeAll": False,
                "label": "Datasource",
                "multi": False,
                "name": "DS_PROMETHEUS",
                "options": [],
                "query": "prometheus",
                "refresh": 1,
                "regex": "",
                "skipUrlSync": False,
                "type": "datasource"
            })
        
        # Save updated dashboard
        with open(filepath, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        print(f"   💾 Saved: {filepath.name}\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False

def main():
    print("=" * 70)
    print("  GRAFANA DASHBOARD UPDATER - FINAL CONFIGURATION")
    print("=" * 70)
    print()
    print("Settings to apply:")
    print("  • Datasource: ${DS_PROMETHEUS} (Grafana default)")
    print("  • No Value: '-' (dash)")
    print("  • Decimals: 0")
    print()
    print("=" * 70)
    print()
    
    # Find all JSON files
    json_files = sorted(DASHBOARD_DIR.glob("*.json"))
    
    if not json_files:
        print("❌ No JSON files found!")
        return
    
    print(f"Found {len(json_files)} dashboard file(s):\n")
    
    success_count = 0
    for filepath in json_files:
        if update_dashboard(filepath):
            success_count += 1
    
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"Total files: {len(json_files)}")
    print(f"Successfully updated: {success_count}")
    print(f"Failed: {len(json_files) - success_count}")
    print()
    
    if success_count == len(json_files):
        print("✅ ALL DASHBOARDS UPDATED SUCCESSFULLY!")
        print()
        print("Configuration applied:")
        print("  ✓ Datasource: Grafana default (${DS_PROMETHEUS})")
        print("  ✓ No value displays: '-'")
        print("  ✓ Decimals: 0 (whole numbers only)")
        print("  ✓ Auto-refresh: 30 seconds")
        print()
        print("Next steps:")
        print("  1. Restart Grafana:")
        print("     docker-compose restart grafana")
        print()
        print("  2. Open Grafana: http://localhost:3000")
        print("     Login: admin / admin")
        print()
        print("  3. Navigate to Dashboards and verify")
        print()
    else:
        print("⚠️  Some files had errors. Check output above.")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
