#!/usr/bin/env python3
"""
Set Grafana as Datasource
- Change datasource type to "grafana" (not prometheus)
- Keep noValue as "-"
- Keep decimals as 0
"""

import json
from pathlib import Path

DASHBOARD_DIR = Path("/home/sujan-rathod/Desktop/NMS/NMS project/config/grafana/dashboards")

def update_panel_datasource(panel):
    """Update panel to use grafana datasource"""
    
    # Set datasource to grafana
    panel["datasource"] = {
        "type": "grafana",
        "uid": "-- Grafana --"
    }
    
    # Update targets
    if "targets" in panel:
        for target in panel["targets"]:
            target["datasource"] = {
                "type": "grafana",
                "uid": "-- Grafana --"
            }
    
    return panel

def update_dashboard(filepath):
    """Update dashboard to use grafana datasource"""
    print(f"📝 Updating: {filepath.name}")
    
    try:
        with open(filepath, 'r') as f:
            dashboard = json.load(f)
        
        panel_count = 0
        
        # Update all panels
        if "panels" in dashboard:
            for panel in dashboard["panels"]:
                if panel is None:
                    continue
                
                update_panel_datasource(panel)
                panel_count += 1
                
                # Update nested panels
                if "panels" in panel:
                    for nested_panel in panel["panels"]:
                        if nested_panel is not None:
                            update_panel_datasource(nested_panel)
                            panel_count += 1
        
        print(f"   ✅ Updated {panel_count} panels to use 'grafana' datasource")
        
        # Save
        with open(filepath, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        print(f"   💾 Saved\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False

def main():
    print("=" * 70)
    print("  SETTING DATASOURCE TO GRAFANA")
    print("=" * 70)
    print()
    print("Changing datasource type from 'prometheus' to 'grafana'")
    print()
    
    json_files = sorted(DASHBOARD_DIR.glob("*.json"))
    
    if not json_files:
        print("❌ No JSON files found!")
        return
    
    print(f"Found {len(json_files)} dashboard(s)\n")
    
    success = 0
    for filepath in json_files:
        if update_dashboard(filepath):
            success += 1
    
    print("=" * 70)
    print(f"✅ Updated {success}/{len(json_files)} dashboards")
    print()
    print("Datasource now set to:")
    print('  type: "grafana"')
    print('  uid: "-- Grafana --"')
    print()
    print("Restart Grafana: docker-compose restart grafana")
    print("=" * 70)

if __name__ == "__main__":
    main()
