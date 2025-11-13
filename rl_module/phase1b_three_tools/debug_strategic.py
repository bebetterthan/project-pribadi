"""Debug strategic bonus calculation"""
import sys
sys.path.append('.')
from envs.full_recon_env import FullReconEnv

env = FullReconEnv('data/phase1b_train.json', 180, 3)

# Find database cluster
target_idx = None
for i, s in enumerate(env.scenarios):
    if s['id'] == 'phase1b_database_cluster':
        target_idx = i
        print(f"Found at index: {i}")
        print(f"Scenario: {s['id']}")
        print(f"Ports: {s['metadata']['port_list']}")
        break

env.reset()
# Manually set to database cluster scenario
env.current_scenario_idx = target_idx
env.current_scenario = env.scenarios[target_idx]

print(f"\nAfter manual set, current scenario: {env.current_scenario['id']}")
print(f"Current ports: {env.current_scenario['metadata']['port_list']}")

ports = env.current_scenario['metadata']['port_list']
web_ports = [80, 443, 8080, 8443, 3000, 5000]
infrastructure_ports = [22, 25, 445, 1433, 3306, 3389, 5432, 6379, 27017, 9200, 9092]

has_web = any(p in web_ports for p in ports)
has_infra = any(p in infrastructure_ports for p in ports)
infra_count = len([p for p in ports if p in infrastructure_ports])
web_only = has_web and not has_infra
infra_heavy = infra_count >= 2

print(f"\nAnalysis:")
print(f"  has_web: {has_web}")
print(f"  has_infra: {has_infra}")
print(f"  infra_count: {infra_count}")
print(f"  web_only: {web_only}")
print(f"  infra_heavy: {infra_heavy}")

# Test skip
env.step(0)  # subfinder
env.step(3)  # httpx
env.step(9)  # skip

print(f"\nReward breakdown: {env.reward_breakdown}")
print(f"Strategic bonus should be: -300 (penalty for skip on infra)")
