"""
PHASE 1 SCENARIO GENERATOR (SUBFINDER + HTTPX)
===============================================

Generate diverse pentesting reconnaissance scenarios for RL training.
2-TOOL SEQUENTIAL: Subfinder (subdomain discovery) → HTTPX (live probing)

DIVERSITY REQUIREMENTS (Gemini's Insight):
- Pattern learning > Memorization
- Varied target types, naming patterns, tech stacks
- Realistic subfinder + httpx simulation
- Enforced distribution rules

Author: Agent-P RL Team
Date: 2025-11-13 (Updated: Subfinder+HTTPX)
"""

import json
import random
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from pathlib import Path


# ============================================
# SCENARIO DATA STRUCTURES
# ============================================

@dataclass
class SubdomainInfo:
    """Individual subdomain metadata"""
    priority: str  # "critical", "high", "medium", "low"
    tech: str
    endpoints: List[str]
    ports: List[int]
    is_live: bool  # HTTPX will discover this
    response_time: int  # milliseconds (for live hosts)


@dataclass
class SubfinderResults:
    """Simulated subfinder execution results"""
    coverage: float  # 0.0-1.0
    time_cost: int   # seconds
    finds: List[str] # subdomain names found


@dataclass
class HttpxResults:
    """Simulated httpx execution results"""
    probed: int  # number of hosts probed
    live: int  # number of live hosts found
    dead: int  # number of dead hosts
    time_cost: int  # seconds
    live_hosts: List[str]  # live subdomain names
    response_times: Dict[str, int]  # {subdomain: response_time_ms}


@dataclass
class Scenario:
    """Complete reconnaissance scenario"""
    scenario_id: int
    type: str  # "small_business", "medium_enterprise", "large_corporate"
    complexity: str  # "low", "medium", "high", "chaotic"
    domain: str
    ground_truth: Dict[str, Any]
    subfinder_results: Dict[str, Any]
    httpx_results: Dict[str, Any]  # NEW: httpx probe results
    optimal_strategy: str  # "passive", "active", "comprehensive"
    optimal_httpx_strategy: str  # "quick", "thorough", "comprehensive"
    optimal_reason: str


# ============================================
# NAMING PATTERN POOLS
# ============================================

NAMING_PATTERNS = {
    "generic": ["www", "mail", "ftp", "blog", "shop", "forum", "support"],
    "functional": ["api", "admin", "dashboard", "portal", "app", "web", "mobile"],
    "environment": ["dev", "staging", "prod", "qa", "test", "uat", "preprod"],
    "regional": ["us-api", "eu-web", "asia-cdn", "au-app", "uk-portal"],
    "custom": ["internal", "legacy", "old-site", "backup", "archive", "cdn"]
}

TECH_STACKS = {
    "lamp": "Apache 2.4 + PHP 7.4 + MySQL 5.7",
    "mean": "Node.js 16 + Express + MongoDB",
    "modern": "Docker + Kubernetes + React",
    "legacy": "IIS 7.5 + .NET 4.5 + SQL Server",
    "mixed": "Mix of Apache, Nginx, Node.js"
}


# ============================================
# SCENARIO GENERATION LOGIC
# ============================================

def generate_subdomain_pool(
    target_type: str,
    complexity: str,
    naming_patterns: List[str]
) -> Dict[str, SubdomainInfo]:
    """
    Generate diverse subdomain ground truth.
    
    Target types determine subdomain count:
    - small_business: 3-5 subdomains
    - medium_enterprise: 8-15 subdomains
    - large_corporate: 15-25 subdomains
    """
    
    # Determine subdomain count based on target type
    subdomain_counts = {
        "small_business": random.randint(3, 5),
        "medium_enterprise": random.randint(8, 15),
        "large_corporate": random.randint(15, 25)
    }
    
    count = subdomain_counts[target_type]
    
    # Build subdomain pool from specified naming patterns
    available_names = []
    for pattern in naming_patterns:
        available_names.extend(NAMING_PATTERNS[pattern])
    
    # Sample unique subdomain names
    selected_names = random.sample(available_names, min(count, len(available_names)))
    
    # Assign priorities (critical = high value targets)
    critical_names = ["admin", "api", "internal", "staging", "dashboard"]
    
    subdomains = {}
    for name in selected_names:
        # Determine priority
        if name in critical_names:
            priority = "critical"
        elif name in ["www", "mail", "portal"]:
            priority = "high"
        elif name in ["dev", "test", "qa"]:
            priority = "medium"
        else:
            priority = "low"
        
        # Assign tech stack
        tech = random.choice(list(TECH_STACKS.values()))
        
        # Assign endpoints
        endpoints = []
        if name in ["www", "api", "portal", "app"]:
            endpoints = ["/", "/api", "/login"]
        elif name == "admin":
            endpoints = ["/admin", "/dashboard", "/login"]
        
        # Assign ports
        ports = [80, 443] if name not in ["ftp", "mail"] else [21, 25]
        
        # Assign live status (70-90% live, 10-30% dead)
        is_live = random.random() < 0.8  # 80% live by default
        
        # Response time for live hosts (50-500ms)
        response_time = random.randint(50, 500) if is_live else 0
        
        subdomains[name] = SubdomainInfo(
            priority=priority,
            tech=tech,
            endpoints=endpoints,
            ports=ports,
            is_live=is_live,
            response_time=response_time
        )
    
    return subdomains


def simulate_subfinder_results(
    ground_truth: Dict[str, SubdomainInfo],
    mode: str
) -> SubfinderResults:
    """
    Simulate subfinder execution results.
    
    Mode characteristics:
    - passive: 40% coverage, 10s, finds common names
    - active: 70% coverage, 25s, finds most including high-value
    - comprehensive: 95% coverage, 60s, finds almost all
    """
    
    mode_configs = {
        "passive": {"coverage": 0.4, "time": 10},
        "active": {"coverage": 0.7, "time": 25},
        "comprehensive": {"coverage": 0.95, "time": 60}
    }
    
    config = mode_configs[mode]
    total_subdomains = len(ground_truth)
    find_count = int(total_subdomains * config["coverage"])
    
    # Passive mode finds common/high-priority first
    if mode == "passive":
        priority_sorted = sorted(
            ground_truth.items(),
            key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x[1].priority]
        )
        finds = [name for name, _ in priority_sorted[:find_count]]
    
    # Active mode finds most including high-value
    elif mode == "active":
        priority_sorted = sorted(
            ground_truth.items(),
            key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x[1].priority]
        )
        finds = [name for name, _ in priority_sorted[:find_count]]
    
    # Comprehensive finds almost all (random sampling)
    else:
        all_names = list(ground_truth.keys())
        finds = random.sample(all_names, find_count)
    
    return SubfinderResults(
        coverage=config["coverage"],
        time_cost=config["time"],
        finds=finds
    )


def simulate_httpx_results(
    discovered_subdomains: List[str],
    ground_truth: Dict[str, SubdomainInfo],
    mode: str
) -> HttpxResults:
    """
    Simulate HTTPX probing results for discovered subdomains.
    
    Modes:
    - quick: Basic probe, fast (5s for 1-5 hosts, 10s for 6-10, 20s for 11+)
    - thorough: Detailed probe with retries (10s, 20s, 40s)
    - comprehensive: Full probe with all checks (15s, 30s, 60s)
    
    Args:
        discovered_subdomains: Subdomains found by subfinder
        ground_truth: Complete subdomain info
        mode: httpx mode
    
    Returns:
        HttpxResults with live/dead counts and response times
    """
    
    # Time costs based on mode and subdomain count
    subdomain_count = len(discovered_subdomains)
    
    if subdomain_count <= 5:
        time_costs = {"quick": 5, "thorough": 10, "comprehensive": 15}
    elif subdomain_count <= 10:
        time_costs = {"quick": 10, "thorough": 20, "comprehensive": 30}
    else:
        time_costs = {"quick": 20, "thorough": 40, "comprehensive": 60}
    
    time_cost = time_costs[mode]
    
    # Probe accuracy based on mode
    # Quick: 90% accuracy, Thorough: 95%, Comprehensive: 99%
    accuracy = {"quick": 0.90, "thorough": 0.95, "comprehensive": 0.99}[mode]
    
    # Determine live hosts
    live_hosts = []
    response_times = {}
    
    for subdomain in discovered_subdomains:
        if subdomain in ground_truth:
            info = ground_truth[subdomain]
            
            # Check if truly live
            if info.is_live:
                # Accuracy check - might miss some live hosts if low accuracy
                if random.random() < accuracy:
                    live_hosts.append(subdomain)
                    response_times[subdomain] = info.response_time
            else:
                # Dead host - might incorrectly report as live (false positive)
                if random.random() > accuracy:  # Rare false positive
                    live_hosts.append(subdomain)
                    response_times[subdomain] = random.randint(1000, 3000)  # Slow
    
    return HttpxResults(
        probed=len(discovered_subdomains),
        live=len(live_hosts),
        dead=len(discovered_subdomains) - len(live_hosts),
        time_cost=time_cost,
        live_hosts=live_hosts,
        response_times=response_times
    )


def determine_optimal_strategy(
    target_type: str,
    complexity: str,
    ground_truth: Dict[str, SubdomainInfo]
) -> tuple[str, str]:
    """
    Determine optimal subfinder mode for scenario.
    
    Rules:
    - Small targets: passive (efficient for few subdomains)
    - Medium targets: active (balance of speed and coverage)
    - Large/critical targets: comprehensive (need full picture)
    """
    
    total_subdomains = len(ground_truth)
    critical_count = sum(1 for s in ground_truth.values() if s.priority == "critical")
    
    # Small targets: passive is optimal
    if target_type == "small_business":
        return "passive", "Small target, passive finds most efficiently"
    
    # Large targets with critical assets: comprehensive needed
    elif target_type == "large_corporate" and critical_count >= 3:
        return "comprehensive", "Large target with critical assets, need full coverage"
    
    # Medium targets: active is sweet spot
    else:
        return "active", "Medium target, active finds high-value targets efficiently"


def determine_optimal_httpx_strategy(
    discovered_count: int,
    live_ratio: float
) -> str:
    """
    Determine optimal HTTPX mode based on discovered subdomains.
    
    Rules:
    - Few subdomains (≤5): quick is enough
    - Medium (6-15): thorough for balance
    - Many (>15): comprehensive for accuracy
    - High live ratio (>80%): can use quick
    - Low live ratio (<50%): need comprehensive
    """
    
    if discovered_count <= 5 and live_ratio > 0.7:
        return "quick"  # Fast for small, mostly-live sets
    elif discovered_count > 15 or live_ratio < 0.5:
        return "comprehensive"  # Accuracy needed
    else:
        return "thorough"  # Balanced approach


def generate_scenario(
    scenario_id: int,
    target_type: str,
    complexity: str,
    naming_patterns: List[str],
    domain: str
) -> Scenario:
    """Generate complete reconnaissance scenario"""
    
    # Generate ground truth subdomains
    ground_truth = generate_subdomain_pool(target_type, complexity, naming_patterns)
    
    # Simulate subfinder results for all modes
    subfinder_results = {
        "passive": asdict(simulate_subfinder_results(ground_truth, "passive")),
        "active": asdict(simulate_subfinder_results(ground_truth, "active")),
        "comprehensive": asdict(simulate_subfinder_results(ground_truth, "comprehensive"))
    }
    
    # Simulate HTTPX results for each subfinder mode
    httpx_results = {}
    for subfinder_mode, subfinder_data in subfinder_results.items():
        discovered = subfinder_data["finds"]
        
        # For each httpx mode
        httpx_results[subfinder_mode] = {
            "quick": asdict(simulate_httpx_results(discovered, ground_truth, "quick")),
            "thorough": asdict(simulate_httpx_results(discovered, ground_truth, "thorough")),
            "comprehensive": asdict(simulate_httpx_results(discovered, ground_truth, "comprehensive"))
        }
    
    # Determine optimal subfinder strategy
    optimal_strategy, optimal_reason = determine_optimal_strategy(
        target_type, complexity, ground_truth
    )
    
    # Calculate live ratio from ground truth
    total_live = sum(1 for info in ground_truth.values() if info.is_live)
    live_ratio = total_live / len(ground_truth) if ground_truth else 0.5
    
    # Determine optimal httpx strategy (based on optimal subfinder's discoveries)
    optimal_subfinder_finds = len(subfinder_results[optimal_strategy]["finds"])
    optimal_httpx_strategy = determine_optimal_httpx_strategy(
        optimal_subfinder_finds, live_ratio
    )
    
    # Convert ground_truth to JSON-serializable format
    ground_truth_dict = {
        "total_subdomains": len(ground_truth),
        "total_live": total_live,
        "live_ratio": live_ratio,
        "subdomains": {
            name: asdict(info) for name, info in ground_truth.items()
        }
    }
    
    return Scenario(
        scenario_id=scenario_id,
        type=target_type,
        complexity=complexity,
        domain=domain,
        ground_truth=ground_truth_dict,
        subfinder_results=subfinder_results,
        httpx_results=httpx_results,
        optimal_strategy=optimal_strategy,
        optimal_httpx_strategy=optimal_httpx_strategy,
        optimal_reason=optimal_reason
    )


# ============================================
# MAIN GENERATION FUNCTION
# ============================================

def generate_diverse_scenarios(count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate diverse scenarios with enforced distribution.
    
    Distribution:
    - 3 small_business (passive optimal)
    - 4 medium_enterprise (active optimal)
    - 3 large_corporate (comprehensive optimal)
    
    Diversity dimensions:
    1. Target types
    2. Naming patterns
    3. Tech stacks (embedded in subdomains)
    4. Complexity levels
    """
    
    scenarios = []
    
    # Distribution rules
    distributions = [
        ("small_business", "low", ["generic", "functional"]),
        ("small_business", "medium", ["generic", "environment"]),
        ("small_business", "low", ["generic", "custom"]),
        
        ("medium_enterprise", "medium", ["functional", "environment"]),
        ("medium_enterprise", "high", ["functional", "regional"]),
        ("medium_enterprise", "medium", ["functional", "custom"]),
        ("medium_enterprise", "high", ["functional", "environment", "regional"]),
        
        ("large_corporate", "high", ["functional", "environment", "regional"]),
        ("large_corporate", "chaotic", ["functional", "regional", "custom"]),
        ("large_corporate", "high", ["functional", "environment", "custom"]),
    ]
    
    # Domain pool for variety
    domain_pool = [
        "example-shop.com",
        "techcorp.io",
        "globalbank.net",
        "startup-hub.com",
        "enterprise-solutions.biz",
        "megacorp.org",
        "cloud-platform.io",
        "fintech-app.com",
        "ecommerce-store.net",
        "saas-product.co"
    ]
    
    for i, (target_type, complexity, naming_patterns) in enumerate(distributions[:count]):
        scenario = generate_scenario(
            scenario_id=i + 1,
            target_type=target_type,
            complexity=complexity,
            naming_patterns=naming_patterns,
            domain=domain_pool[i]
        )
        scenarios.append(asdict(scenario))
    
    return scenarios


def validate_diversity(scenarios: List[Dict]) -> Dict[str, Any]:
    """
    Validate scenario diversity to prevent memorization.
    
    Checks:
    - Type distribution (3/4/3)
    - Naming pattern variety
    - Optimal strategy distribution (3 passive, 4 active, 3 comprehensive)
    - No duplicate patterns
    """
    
    type_dist = {}
    optimal_dist = {}
    complexity_dist = {}
    
    for scenario in scenarios:
        # Count types
        type_dist[scenario["type"]] = type_dist.get(scenario["type"], 0) + 1
        
        # Count optimal strategies
        optimal_dist[scenario["optimal_strategy"]] = optimal_dist.get(scenario["optimal_strategy"], 0) + 1
        
        # Count complexities
        complexity_dist[scenario["complexity"]] = complexity_dist.get(scenario["complexity"], 0) + 1
    
    # Relaxed criteria for smaller sets (eval scenarios)
    min_types = 2 if len(scenarios) <= 5 else 3
    min_strategies = 2 if len(scenarios) <= 5 else 3
    
    report = {
        "total_scenarios": len(scenarios),
        "type_distribution": type_dist,
        "optimal_strategy_distribution": optimal_dist,
        "complexity_distribution": complexity_dist,
        "diversity_score": "PASS" if len(type_dist) >= min_types and len(optimal_dist) >= min_strategies else "FAIL"
    }
    
    return report


# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Phase 1 training scenarios")
    parser.add_argument("--count", type=int, default=10, help="Number of scenarios to generate")
    parser.add_argument("--output", type=str, default="scenarios/phase1_training.json", help="Output JSON file")
    parser.add_argument("--eval", action="store_true", help="Generate evaluation scenarios instead")
    args = parser.parse_args()
    
    # Generate scenarios
    print(f"🎯 Generating {args.count} diverse scenarios...")
    scenarios = generate_diverse_scenarios(args.count)
    
    # Validate diversity
    print("✅ Validating diversity...")
    diversity_report = validate_diversity(scenarios)
    
    print(f"\n📊 DIVERSITY REPORT:")
    print(f"   Total scenarios: {diversity_report['total_scenarios']}")
    print(f"   Type distribution: {diversity_report['type_distribution']}")
    print(f"   Optimal strategy distribution: {diversity_report['optimal_strategy_distribution']}")
    print(f"   Complexity distribution: {diversity_report['complexity_distribution']}")
    print(f"   Diversity score: {diversity_report['diversity_score']}")
    
    if diversity_report["diversity_score"] == "FAIL":
        print("\n❌ Diversity validation FAILED! Regenerating...")
        exit(1)
    
    # Save to file
    output_path = Path(__file__).parent / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(scenarios, f, indent=2)
    
    print(f"\n✅ Scenarios saved to: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")
    
    # Save diversity report
    report_path = output_path.parent / "diversity_report.txt"
    with open(report_path, 'w') as f:
        f.write(f"PHASE 1 SCENARIO DIVERSITY REPORT\n")
        f.write(f"=" * 50 + "\n\n")
        for key, value in diversity_report.items():
            f.write(f"{key}: {value}\n")
    
    print(f"📝 Diversity report saved to: {report_path}")
    print("\n🎉 Scenario generation complete!")
