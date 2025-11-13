"""
Analyze reward ceiling and identify optimization opportunities
"""
import sys
sys.path.append('d:\\Project pribadi\\AI_Pentesting\\rl_module\\phase1b_three_tools')

from envs.full_recon_env import FullReconEnv
import json

def analyze_scenario_potential(env, scenario_idx):
    """Analyze maximum possible reward for a scenario"""
    env.reset()
    env.current_scenario_idx = scenario_idx
    env.current_scenario = env.scenarios[scenario_idx]
    
    scenario = env.current_scenario
    metadata = scenario['metadata']
    
    print(f"\n{'='*70}")
    print(f"SCENARIO: {scenario['name']}")
    print(f"{'='*70}")
    print(f"Target: {scenario['target']}")
    print(f"Ports: {metadata['port_list']}")
    
    # Identify scenario type
    web_ports = [80, 443, 8080, 8443, 3000, 5000]
    infrastructure_ports = [22, 25, 445, 1433, 3306, 3389, 5432, 6379, 27017, 9200, 9092]
    
    has_web = any(p in web_ports for p in metadata['port_list'])
    has_infra = any(p in infrastructure_ports for p in metadata['port_list'])
    infra_count = len([p for p in metadata['port_list'] if p in infrastructure_ports])
    
    web_only = has_web and not has_infra
    infra_heavy = infra_count >= 2
    hybrid = has_web and has_infra and infra_count < 2
    
    scenario_type = "WEB-ONLY" if web_only else ("INFRASTRUCTURE" if infra_heavy else "HYBRID")
    print(f"Type: {scenario_type}")
    
    # Simulate optimal path
    total_reward = 0
    breakdown = {'discovery': 0, 'completion': 0, 'strategic': 0, 'efficiency': 0}
    
    # Step 1: Subfinder (always comprehensive)
    subdomains = len(scenario['tool_results']['subfinder']['subdomains'])
    subdomain_reward = subdomains * 15
    total_reward += subdomain_reward
    breakdown['discovery'] += subdomain_reward
    print(f"\nStep 1 (Subfinder comprehensive): +{subdomain_reward} ({subdomains} subdomains × 15)")
    
    # Step 2: HTTPX (thorough for infra, comprehensive for web)
    if infra_heavy:
        httpx_mode = 'thorough'
    else:
        httpx_mode = 'comprehensive'
    
    live_endpoints = scenario['tool_results']['httpx']['live_endpoints']
    endpoint_reward = live_endpoints * 10
    total_reward += endpoint_reward
    breakdown['discovery'] += endpoint_reward
    print(f"Step 2 (HTTPX {httpx_mode}): +{endpoint_reward} ({live_endpoints} endpoints × 10)")
    
    # Step 3: Nmap or Skip
    if web_only:
        # Optimal: SKIP
        print(f"Step 3 (SKIP nmap): +700 (strategic bonus)")
        total_reward += 700
        breakdown['strategic'] += 700
        print(f"\n[OK] OPTIMAL PATH: Skip nmap on web-only")
        
    elif infra_heavy:
        # Optimal: USE NMAP SERVICE
        nmap_results = scenario['tool_results']['nmap']
        
        # Get ports from services list
        ports = [s['port'] for s in nmap_results['services']]
        
        # Discovery rewards
        web_port_count = len([p for p in ports if p in web_ports])
        infra_port_count = len([p for p in ports if p not in web_ports])
        
        port_reward = (web_port_count * 10) + (infra_port_count * 30)
        service_reward = nmap_results.get('critical_services', 0) * 50
        version_reward = len([s for s in nmap_results['services'] if s.get('version')]) * 25
        
        discovery = port_reward + service_reward + version_reward
        total_reward += discovery
        breakdown['discovery'] += discovery
        
        print(f"Step 3 (NMAP service):")
        print(f"  - Ports: +{port_reward} ({web_port_count} web×10 + {infra_port_count} infra×30)")
        print(f"  - Services: +{service_reward} ({nmap_results.get('critical_services', 0)} × 50)")
        print(f"  - Versions: +{version_reward} ({len([s for s in nmap_results['services'] if s.get('version')])} × 25)")
        
        # Completion bonus
        completion = 150
        total_reward += completion
        breakdown['completion'] += completion
        print(f"  - Completion bonus: +{completion}")
        
        # Strategic bonus (service mode)
        strategic = 500
        total_reward += strategic
        breakdown['strategic'] += strategic
        print(f"  - Strategic bonus: +{strategic}")
        
        # 3-tool completion bonus
        three_tool_bonus = 900
        total_reward += three_tool_bonus
        breakdown['strategic'] += three_tool_bonus
        print(f"  - 3-tool bonus: +{three_tool_bonus}")
        
        print(f"\n[OK] OPTIMAL PATH: Use nmap service on infrastructure")
    
    else:  # Hybrid
        # Optimal: USE NMAP QUICK
        nmap_results = scenario['tool_results']['nmap']
        
        # Get ports from services list
        ports = [s['port'] for s in nmap_results['services']]
        
        web_port_count = len([p for p in ports if p in web_ports])
        infra_port_count = len([p for p in ports if p not in web_ports])
        
        port_reward = (web_port_count * 10) + (infra_port_count * 30)
        total_reward += port_reward
        breakdown['discovery'] += port_reward
        
        print(f"Step 3 (NMAP quick): +{port_reward} ({web_port_count} web×10 + {infra_port_count} infra×30)")
        
        # Completion
        completion = 100
        total_reward += completion
        breakdown['completion'] += completion
        print(f"  - Completion bonus: +{completion}")
        
        # Strategic
        strategic = 150
        total_reward += strategic
        breakdown['strategic'] += strategic
        print(f"  - Strategic bonus: +{strategic}")
        
        print(f"\n[OK] OPTIMAL PATH: Use nmap quick on hybrid")
    
    print(f"\n{'-'*70}")
    print(f"TOTAL REWARD: {total_reward}")
    print(f"Breakdown: {breakdown}")
    print(f"{'-'*70}")
    
    return {
        'name': scenario['name'],
        'type': scenario_type,
        'optimal_reward': total_reward,
        'breakdown': breakdown
    }

def main():
    print("="*70)
    print("REWARD CEILING ANALYSIS - Phase 1B")
    print("="*70)
    
    env = FullReconEnv(scenarios_path='d:\\Project pribadi\\AI_Pentesting\\rl_module\\phase1b_three_tools\\data\\phase1b_train.json')
    
    results = []
    for idx in range(len(env.scenarios)):
        result = analyze_scenario_potential(env, idx)
        results.append(result)
    
    print("\n" + "="*70)
    print("SUMMARY - ALL SCENARIOS")
    print("="*70)
    
    web_only_rewards = [r['optimal_reward'] for r in results if r['type'] == 'WEB-ONLY']
    infra_rewards = [r['optimal_reward'] for r in results if r['type'] == 'INFRASTRUCTURE']
    hybrid_rewards = [r['optimal_reward'] for r in results if r['type'] == 'HYBRID']
    
    print(f"\nWEB-ONLY Scenarios ({len(web_only_rewards)}):")
    if web_only_rewards:
        print(f"  Mean: {sum(web_only_rewards)/len(web_only_rewards):.0f}")
        print(f"  Range: [{min(web_only_rewards)}, {max(web_only_rewards)}]")
    
    print(f"\nINFRASTRUCTURE Scenarios ({len(infra_rewards)}):")
    if infra_rewards:
        print(f"  Mean: {sum(infra_rewards)/len(infra_rewards):.0f}")
        print(f"  Range: [{min(infra_rewards)}, {max(infra_rewards)}]")
    
    print(f"\nHYBRID Scenarios ({len(hybrid_rewards)}):")
    if hybrid_rewards:
        print(f"  Mean: {sum(hybrid_rewards)/len(hybrid_rewards):.0f}")
        print(f"  Range: [{min(hybrid_rewards)}, {max(hybrid_rewards)}]")
    
    all_rewards = [r['optimal_reward'] for r in results]
    overall_mean = sum(all_rewards) / len(all_rewards)
    
    print(f"\n{'='*70}")
    print(f"OVERALL OPTIMAL MEAN: {overall_mean:.0f}")
    print(f"CURRENT V10 MEAN: 1631")
    print(f"TARGET: 2079")
    print(f"{'='*70}")
    print(f"\nGAP ANALYSIS:")
    print(f"  Current vs Optimal: {1631/overall_mean*100:.1f}% efficiency")
    print(f"  Current vs Target: {1631/2079*100:.1f}% of target")
    print(f"  Optimal vs Target: {overall_mean/2079*100:.1f}% of target")
    
    if overall_mean < 2079:
        print(f"\n[!] REWARD CEILING TOO LOW!")
        print(f"  Maximum possible: {overall_mean:.0f}")
        print(f"  Need to increase: {2079 - overall_mean:.0f} points")
        print(f"\n[*] RECOMMENDATION:")
        print(f"  Amplify all reward components by {(2079/overall_mean):.2f}x")
    else:
        print(f"\n[OK] REWARD CEILING SUFFICIENT")
        print(f"  Agent just needs better policy learning")

if __name__ == '__main__':
    main()
