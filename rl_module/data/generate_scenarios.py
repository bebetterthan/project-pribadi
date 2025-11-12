"""
Generate diverse pentesting scenarios for RL training.

COPILOT PROMPT:
Generate 100 realistic pentesting scenarios with varying complexity.
Each scenario should simulate a real target with:

Structure:
- scenario_id: unique identifier
- difficulty: "easy" (30%), "medium" (50%), "hard" (20%)
- root_domain: realistic domain name (e.g., "example-corp.com")
- subdomains: list of 5-20 subdomains with realistic names
  * Common: www, api, admin, staging, dev, test, mobile, dashboard
  * Email: mail, smtp, webmail, mx1
  * Services: cdn, static, assets, media, images
  * Internal: vpn, intranet, jenkins, gitlab
  
Each subdomain has:
- name: subdomain name
- endpoints: list of 2-10 web paths
  * Common: /, /login, /admin, /api/v1, /api/v2, /dashboard
  * Auth: /signin, /register, /forgot-password, /oauth
  * API: /api/users, /api/products, /graphql, /swagger
  * Admin: /wp-admin, /phpmyadmin, /administrator
- open_ports: list of 1-5 ports
  * Web: 80, 443, 8080, 8443
  * DB: 3306 (MySQL), 5432 (PostgreSQL), 27017 (MongoDB)
  * Other: 22 (SSH), 21 (FTP), 25 (SMTP)
- technologies: list of tech stack
  * Web servers: nginx, apache, iis, express
  * Frameworks: react, vue, angular, django, flask, laravel
  * CMS: wordpress, drupal, joomla
  * Languages: python, php, nodejs, ruby, java
- response_times: dict of path -> latency_ms (50-500ms)

Diversity requirements:
- Mix of scales: small (5-10 subdomains), medium (11-15), large (16-20)
- Mix of architectures: monolith, microservices, hybrid
- Mix of tech stacks: LAMP, MEAN, JAMstack, enterprise Java
- Mix of industries: ecommerce, fintech, healthcare, education

Output: JSON file with list of scenarios
Performance: Should generate all scenarios in <5 seconds

Usage:
    python generate_scenarios.py --count 100 --output data/scenarios/training.json
    python generate_scenarios.py --count 20 --output data/scenarios/test.json --seed 999
"""

import json
import random
import argparse
from typing import Dict, List, Any
from pathlib import Path


# Realistic subdomain name pools
SUBDOMAIN_POOLS = {
    'common': ['www', 'api', 'admin', 'staging', 'dev', 'test', 'demo', 'beta'],
    'email': ['mail', 'smtp', 'webmail', 'mx1', 'mx2', 'imap', 'pop3'],
    'cdn': ['cdn', 'static', 'assets', 'media', 'images', 'files', 'downloads'],
    'internal': ['vpn', 'intranet', 'jenkins', 'gitlab', 'grafana', 'prometheus'],
    'services': ['mobile', 'dashboard', 'portal', 'shop', 'blog', 'forum'],
    'monitoring': ['status', 'health', 'metrics', 'logs', 'monitoring']
}

# Web endpoint pools
ENDPOINT_POOLS = {
    'public': ['/', '/about', '/contact', '/products', '/services', '/pricing'],
    'auth': ['/login', '/signin', '/register', '/signup', '/logout', '/forgot-password'],
    'api': ['/api/v1', '/api/v2', '/api/users', '/api/products', '/graphql', '/swagger'],
    'admin': ['/admin', '/administrator', '/wp-admin', '/phpmyadmin', '/dashboard'],
    'static': ['/css', '/js', '/images', '/fonts', '/assets']
}

# Technology stack combinations
TECH_STACKS = [
    # LAMP Stack
    {'web_server': 'apache', 'framework': 'wordpress', 'language': 'php', 'db': 'mysql'},
    # MEAN Stack
    {'web_server': 'nginx', 'framework': 'express', 'language': 'nodejs', 'db': 'mongodb'},
    # Python Stack
    {'web_server': 'nginx', 'framework': 'django', 'language': 'python', 'db': 'postgresql'},
    # Modern JAMstack
    {'web_server': 'nginx', 'framework': 'react', 'language': 'javascript', 'db': 'none'},
    # Enterprise Java
    {'web_server': 'apache', 'framework': 'spring', 'language': 'java', 'db': 'oracle'},
]

# Port mappings
PORT_MAPPING = {
    'http': [80, 8080, 8000],
    'https': [443, 8443],
    'ssh': [22],
    'ftp': [21],
    'smtp': [25, 587],
    'mysql': [3306],
    'postgresql': [5432],
    'mongodb': [27017],
    'redis': [6379]
}


def generate_subdomain_names(count: int, difficulty: str) -> List[str]:
    """
    Generate realistic subdomain names based on difficulty.
    
    Easy: Mostly common subdomains (www, api, admin)
    Medium: Mix of common + services
    Hard: Complex mix including internal services
    """
    # TODO: Implement subdomain name generation
    # Use SUBDOMAIN_POOLS
    # Ensure no duplicates
    # Scale complexity with difficulty
    pass


def generate_endpoints(subdomain_type: str, count: int) -> List[str]:
    """
    Generate realistic endpoints for subdomain type.
    
    Args:
        subdomain_type: Type of subdomain (www, api, admin, etc.)
        count: Number of endpoints to generate (2-10)
    
    Returns:
        List of endpoint paths
    """
    # TODO: Implement endpoint generation
    # www -> public + auth endpoints
    # api -> API endpoints
    # admin -> admin + auth endpoints
    pass


def generate_open_ports(tech_stack: Dict[str, str], subdomain_type: str) -> List[int]:
    """
    Generate realistic open ports based on tech stack and subdomain.
    
    Args:
        tech_stack: Technology stack dict
        subdomain_type: Type of subdomain
    
    Returns:
        List of open port numbers
    """
    # TODO: Implement port generation
    # Always: 80/443 for web services
    # DB ports: Only if database subdomain or internal
    # SSH: More common on staging/dev subdomains
    pass


def generate_technologies(base_stack: Dict[str, str], subdomain_type: str) -> List[str]:
    """
    Generate technology list for subdomain.
    
    Args:
        base_stack: Base technology stack
        subdomain_type: Type of subdomain
    
    Returns:
        List of technology names
    """
    # TODO: Implement technology generation
    # Convert base_stack dict to flat list
    # Add frontend frameworks for www subdomains
    # Add monitoring tools for internal subdomains
    pass


def generate_response_times(endpoints: List[str]) -> Dict[str, int]:
    """
    Generate realistic response times for endpoints.
    
    Static files: 50-150ms
    Dynamic pages: 150-350ms
    API calls: 100-300ms
    Admin pages: 200-500ms
    """
    # TODO: Implement response time generation
    # Use random.randint() with ranges based on endpoint type
    pass


def generate_single_scenario(scenario_id: int, difficulty: str, seed: int) -> Dict[str, Any]:
    """
    Generate a single complete scenario.
    
    Args:
        scenario_id: Unique scenario identifier
        difficulty: "easy", "medium", or "hard"
        seed: Random seed for reproducibility
    
    Returns:
        Complete scenario dictionary
    """
    random.seed(seed + scenario_id)
    
    # TODO: Implement full scenario generation
    # 1. Generate root domain
    # 2. Determine subdomain count based on difficulty
    # 3. Select tech stack
    # 4. Generate each subdomain with:
    #    - Endpoints
    #    - Open ports
    #    - Technologies
    #    - Response times
    # 5. Return complete scenario dict
    
    scenario = {
        'scenario_id': scenario_id,
        'difficulty': difficulty,
        'root_domain': '',  # TODO: Generate
        'subdomains': [],   # TODO: Generate
        'metadata': {
            'total_endpoints': 0,
            'total_ports': 0,
            'primary_tech_stack': ''
        }
    }
    
    return scenario


def generate_scenarios(count: int, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate multiple scenarios with difficulty distribution.
    
    Distribution:
    - Easy: 30%
    - Medium: 50%
    - Hard: 20%
    
    Args:
        count: Total number of scenarios
        seed: Random seed for reproducibility
    
    Returns:
        List of scenarios
    """
    # Calculate counts per difficulty
    easy_count = int(count * 0.3)
    medium_count = int(count * 0.5)
    hard_count = count - easy_count - medium_count
    
    scenarios = []
    scenario_id = 1
    
    # Generate easy scenarios
    for _ in range(easy_count):
        scenarios.append(generate_single_scenario(scenario_id, 'easy', seed))
        scenario_id += 1
    
    # Generate medium scenarios
    for _ in range(medium_count):
        scenarios.append(generate_single_scenario(scenario_id, 'medium', seed))
        scenario_id += 1
    
    # Generate hard scenarios
    for _ in range(hard_count):
        scenarios.append(generate_single_scenario(scenario_id, 'hard', seed))
        scenario_id += 1
    
    return scenarios


def validate_scenarios(scenarios: List[Dict[str, Any]]) -> bool:
    """
    Validate generated scenarios meet requirements.
    
    Checks:
    - All scenarios have required fields
    - Subdomain counts in range (5-20)
    - Port numbers valid (1-65535)
    - No duplicate scenario IDs
    - Difficulty distribution correct
    """
    # TODO: Implement validation
    # Return True if valid, raise exception with details if invalid
    pass


def save_scenarios(scenarios: List[Dict[str, Any]], output_path: str):
    """Save scenarios to JSON file"""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(scenarios, f, indent=2)
    
    print(f"✅ Saved {len(scenarios)} scenarios to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate pentesting scenarios for RL training')
    parser.add_argument('--count', type=int, default=100, help='Number of scenarios to generate')
    parser.add_argument('--output', type=str, default='data/scenarios/training.json', help='Output file path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    print(f"🔄 Generating {args.count} scenarios...")
    scenarios = generate_scenarios(args.count, args.seed)
    
    print(f"✅ Validating scenarios...")
    validate_scenarios(scenarios)
    
    print(f"💾 Saving to {args.output}...")
    save_scenarios(scenarios, args.output)
    
    print(f"🎉 Done!")


if __name__ == '__main__':
    main()
