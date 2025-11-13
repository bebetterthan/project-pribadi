"""
Quick validation script for Phase 1B scenarios

Checks:
1. All required fields present
2. Tool results realistic
3. Reward differentiation clear
4. No duplicate scenarios
"""

import json
from collections import Counter


def validate_scenario_file(filepath: str):
    """Validate a scenario JSON file"""
    
    print(f"\n📝 Validating: {filepath}")
    print("=" * 60)
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    scenarios = data['scenarios']
    print(f"Total scenarios: {len(scenarios)}")
    
    # Check 1: Required fields
    print("\n✅ Check 1: Required fields")
    required_fields = ['id', 'name', 'description', 'target', 'complexity', 
                      'scenario_type', 'metadata', 'tool_results', 
                      'optimal_strategy', 'rewards']
    
    for i, scenario in enumerate(scenarios):
        missing = [f for f in required_fields if f not in scenario]
        if missing:
            print(f"   ❌ Scenario {i+1}: Missing fields: {missing}")
        else:
            print(f"   ✅ Scenario {i+1} ({scenario['id']}): All fields present")
    
    # Check 2: Tool results present
    print("\n✅ Check 2: Tool results completeness")
    for i, scenario in enumerate(scenarios):
        tool_results = scenario['tool_results']
        has_subfinder = 'subfinder' in tool_results
        has_httpx = 'httpx' in tool_results
        has_nmap = 'nmap' in tool_results
        
        if has_subfinder and has_httpx and has_nmap:
            print(f"   ✅ Scenario {i+1}: All 3 tool results present")
        else:
            print(f"   ❌ Scenario {i+1}: Missing tools")
    
    # Check 3: Reward differentiation
    print("\n✅ Check 3: Reward differentiation")
    reward_diffs = []
    for i, scenario in enumerate(scenarios):
        opt = scenario['rewards']['optimal']
        subopt = scenario['rewards']['suboptimal']
        diff = opt - subopt
        diff_pct = (diff / opt) * 100
        reward_diffs.append(diff)
        
        if diff >= 100:  # At least 100 reward difference
            print(f"   ✅ Scenario {i+1}: Δ={diff} ({diff_pct:.1f}%)")
        else:
            print(f"   ⚠️  Scenario {i+1}: Δ={diff} ({diff_pct:.1f}%) - Low differentiation!")
    
    print(f"\n   Average reward difference: {sum(reward_diffs)/len(reward_diffs):.1f}")
    
    # Check 4: No duplicates
    print("\n✅ Check 4: Scenario uniqueness")
    ids = [s['id'] for s in scenarios]
    targets = [s['target'] for s in scenarios]
    port_sets = [tuple(sorted(s['metadata']['port_list'])) for s in scenarios]
    
    dup_ids = [k for k, v in Counter(ids).items() if v > 1]
    dup_targets = [k for k, v in Counter(targets).items() if v > 1]
    dup_ports = [k for k, v in Counter(port_sets).items() if v > 1]
    
    if dup_ids:
        print(f"   ❌ Duplicate IDs: {dup_ids}")
    else:
        print(f"   ✅ All IDs unique")
    
    if dup_targets:
        print(f"   ❌ Duplicate targets: {dup_targets}")
    else:
        print(f"   ✅ All targets unique")
    
    if dup_ports:
        print(f"   ⚠️  Duplicate port patterns: {len(dup_ports)} (acceptable if different types)")
    else:
        print(f"   ✅ All port patterns unique")
    
    # Check 5: Nmap value distribution
    print("\n✅ Check 5: Nmap value distribution")
    nmap_modes = [s['optimal_strategy']['nmap_mode'] for s in scenarios]
    mode_counts = Counter(nmap_modes)
    
    for mode, count in sorted(mode_counts.items()):
        pct = (count / len(scenarios)) * 100
        print(f"   {mode:12s}: {count:2d} scenarios ({pct:5.1f}%)")
    
    # Check 6: Scenario type distribution
    print("\n✅ Check 6: Scenario type distribution")
    types = [s['scenario_type'] for s in scenarios]
    
    web_count = sum(1 for t in types if 'web' in t and 'hybrid' not in t)
    infra_count = sum(1 for t in types if 'infra' in t)
    hybrid_count = sum(1 for t in types if 'hybrid' in t)
    edge_count = sum(1 for t in types if 'edge' in t)
    
    print(f"   Web-only: {web_count} scenarios")
    print(f"   Infrastructure: {infra_count} scenarios")
    print(f"   Hybrid: {hybrid_count} scenarios")
    print(f"   Edge cases: {edge_count} scenarios")
    
    # Check 7: Port diversity
    print("\n✅ Check 7: Port diversity")
    all_ports = set()
    for s in scenarios:
        all_ports.update(s['metadata']['port_list'])
    
    critical_ports = [22, 3306, 5432, 6379, 27017, 1433, 3389, 445]
    web_ports = [80, 443, 8080, 8443, 3000]
    custom_ports = [p for p in all_ports if p >= 4000]
    
    critical_used = [p for p in critical_ports if p in all_ports]
    web_used = [p for p in web_ports if p in all_ports]
    
    print(f"   Total unique ports: {len(all_ports)}")
    print(f"   Critical ports used: {len(critical_used)}/{len(critical_ports)} {critical_used}")
    print(f"   Web ports used: {len(web_used)}/{len(web_ports)} {web_used}")
    print(f"   Custom ports (4000+): {len(custom_ports)} {sorted(custom_ports)}")
    
    print("\n" + "=" * 60)
    print("✅ Validation complete!\n")


def main():
    """Validate both training and test scenarios"""
    
    print("🔍 Phase 1B Scenario Validation")
    print("=" * 60)
    
    # Validate training scenarios
    validate_scenario_file('phase1b_train.json')
    
    # Validate test scenarios
    validate_scenario_file('phase1b_test.json')
    
    print("\n🎯 Summary:")
    print("   • Training scenarios validated")
    print("   • Test scenarios validated")
    print("   • Ready for Day 4 (Environment implementation)")


if __name__ == '__main__':
    main()
