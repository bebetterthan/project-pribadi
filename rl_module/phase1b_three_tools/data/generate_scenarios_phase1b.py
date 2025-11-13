"""
Phase 1B Scenario Generator

Generates 25 pre-computed scenarios for 3-tool RL training:
- 20 training scenarios (S1-S20): Web-only, Infrastructure, Hybrid
- 5 test scenarios (S21-S25): Edge cases

Each scenario includes pre-computed results for:
- Subfinder: subdomain lists with complexity
- HTTPX: live endpoints, technologies, response times
- Nmap: open ports, services, versions, timing

Port diversity: 15+ unique patterns
Reward range: 420-920 optimal
"""

import json
import random
from typing import Dict, List, Any
from datetime import datetime


class ScenarioGenerator:
    """Generate realistic pentesting scenarios with pre-computed tool results"""
    
    def __init__(self):
        self.scenarios = []
        
        # Service version databases
        self.service_versions = {
            'mysql': ['8.0.33', '8.0.32', '5.7.42'],
            'postgresql': ['15.2', '14.5', '13.10'],
            'redis': ['7.0.8', '6.2.11', '6.0.16'],
            'mongodb': ['6.0.4', '5.0.15', '4.4.19'],
            'mssql': ['2019 RTM', '2017 CU31', '2016 SP3'],
            'openssh': ['8.9p1', '8.4p1', '8.2p1'],
            'postfix': ['3.7.2', '3.6.7', '3.5.13'],
            'dovecot': ['2.3.19', '2.3.16', '2.3.13'],
            'nginx': ['1.24.0', '1.22.1', '1.20.2'],
            'apache': ['2.4.56', '2.4.54', '2.4.52'],
            'tomcat': ['9.0.70', '9.0.65', '8.5.87'],
            'prometheus': ['2.40.7', '2.38.0', '2.35.0'],
            'grafana': ['9.3.6', '9.1.8', '8.5.15'],
            'elasticsearch': ['8.6.2', '8.5.3', '7.17.9'],
            'jenkins': ['2.387.1', '2.375.3', '2.361.4'],
        }
        
        # Technology stacks by category
        self.tech_stacks = {
            'web': ['React', 'Vue.js', 'Angular', 'Next.js', 'Svelte', 'Node.js', 'Express.js', 
                   'Django', 'Flask', 'FastAPI', 'Laravel', 'WordPress', 'Nginx', 'Apache'],
            'database': ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'MSSQL', 'MariaDB'],
            'infrastructure': ['Docker', 'Kubernetes', 'Terraform', 'Ansible'],
            'monitoring': ['Prometheus', 'Grafana', 'Elasticsearch', 'Kibana', 'Alertmanager'],
            'cicd': ['Jenkins', 'GitLab CI', 'GitHub Actions', 'CircleCI'],
            'mail': ['Postfix', 'Dovecot', 'SpamAssassin', 'ClamAV'],
            'admin': ['cPanel', 'Webmin', 'phpMyAdmin', 'Adminer'],
            'cdn': ['Cloudflare', 'AWS CloudFront', 'Akamai'],
        }
        
    def generate_subdomain(self, base: str, prefix: str) -> str:
        """Generate realistic subdomain"""
        return f"{prefix}.{base}"
    
    def generate_subdomains(self, target: str, count: int, scenario_type: str) -> List[str]:
        """Generate realistic subdomain lists based on scenario type"""
        prefixes = {
            'web': ['www', 'api', 'app', 'dev', 'staging', 'prod', 'web', 'portal', 'dashboard',
                   'cdn', 'static', 'assets', 'media', 'blog', 'shop', 'store', 'checkout',
                   'payment', 'auth', 'login', 'admin', 'panel', 'manage'],
            'infra': ['db', 'database', 'mysql', 'postgres', 'redis', 'mongo', 'cache',
                     'mail', 'smtp', 'imap', 'pop3', 'webmail', 'ssh', 'vpn', 'backup',
                     'ftp', 'sftp', 'monitoring', 'logs', 'metrics'],
            'hybrid': ['www', 'api', 'app', 'db', 'cache', 'admin', 'staging', 'dev',
                      'monitoring', 'mail', 'dashboard', 'portal'],
            'edge': ['custom', 'service', 'node', 'cluster', 'worker', 'task', 'job'],
        }
        
        # Select prefix pool based on scenario type
        if 'web' in scenario_type:
            pool = prefixes['web']
        elif 'infra' in scenario_type or 'database' in scenario_type or 'mail' in scenario_type:
            pool = prefixes['infra']
        elif 'hybrid' in scenario_type:
            pool = prefixes['hybrid']
        else:
            pool = prefixes['edge']
        
        # Generate unique subdomains
        subdomains = []
        used = set()
        
        # Use all prefixes from pool first
        available_prefixes = pool.copy()
        random.shuffle(available_prefixes)
        
        for prefix in available_prefixes:
            if len(subdomains) >= count:
                break
            subdomains.append(self.generate_subdomain(target, prefix))
            used.add(prefix)
        
        # If we need more, add numbered variants
        suffix_num = 1
        while len(subdomains) < count:
            prefix = random.choice(pool)
            numbered_prefix = f"{prefix}{suffix_num}"
            if numbered_prefix not in used:
                subdomains.append(self.generate_subdomain(target, numbered_prefix))
                used.add(numbered_prefix)
                suffix_num += 1
        
        return sorted(subdomains)
    
    def generate_httpx_results(self, subdomains: List[str], ports: List[int],
                               technologies: List[str]) -> Dict[str, Any]:
        """Generate realistic HTTPX scan results"""
        endpoints = []
        
        # Determine live endpoint ratio based on ports
        web_ports = [80, 443, 8080, 8443, 3000, 8081, 8082]
        has_web = any(p in web_ports for p in ports)
        
        if has_web:
            # More endpoints for web-focused scenarios
            live_ratio = random.uniform(0.7, 0.9)
        else:
            # Fewer endpoints for backend-focused
            live_ratio = random.uniform(0.3, 0.5)
        
        live_count = int(len(subdomains) * live_ratio)
        
        for subdomain in random.sample(subdomains, live_count):
            # Pick random web port
            web_port = random.choice([p for p in ports if p in web_ports] or [443])
            
            endpoint = {
                'url': f"https://{subdomain}:{web_port}",
                'status_code': random.choice([200, 200, 200, 301, 302, 403]),
                'title': f"Page on {subdomain}",
                'tech_stack': random.sample(technologies, min(3, len(technologies))),
                'response_time_ms': random.randint(50, 500),
                'content_length': random.randint(1000, 50000),
            }
            endpoints.append(endpoint)
        
        return {
            'total_checked': len(subdomains),
            'live_endpoints': len(endpoints),
            'endpoints': endpoints,
            'execution_time_seconds': random.uniform(10, 60),
        }
    
    def generate_nmap_results(self, ports: List[int], target: str) -> Dict[str, Any]:
        """Generate realistic Nmap scan results with service versions"""
        services = []
        
        # Service mapping
        port_services = {
            22: ('ssh', 'openssh'),
            25: ('smtp', 'postfix'),
            80: ('http', 'nginx'),
            143: ('imap', 'dovecot'),
            443: ('https', 'nginx'),
            445: ('microsoft-ds', None),
            587: ('smtp', 'postfix'),
            993: ('imaps', 'dovecot'),
            995: ('pop3s', 'dovecot'),
            1433: ('ms-sql-s', 'mssql'),
            3000: ('http', None),
            3306: ('mysql', 'mysql'),
            3389: ('ms-wbt-server', None),
            5432: ('postgresql', 'postgresql'),
            6379: ('redis', 'redis'),
            8080: ('http-proxy', 'nginx'),
            8081: ('http-alt', None),
            8082: ('http-alt', None),
            8443: ('https-alt', 'nginx'),
            9000: ('http', 'jenkins'),
            9090: ('http', 'prometheus'),
            9093: ('http', None),
            9200: ('http', 'elasticsearch'),
            27017: ('mongod', 'mongodb'),
        }
        
        for port in ports:
            service_name, version_key = port_services.get(port, ('unknown', None))
            
            # Get version if available
            version = None
            if version_key and version_key in self.service_versions:
                version = random.choice(self.service_versions[version_key])
            
            service = {
                'port': port,
                'protocol': 'tcp',
                'state': 'open',
                'service': service_name,
                'version': version,
            }
            
            # Add extra info for critical services
            if port == 22 and version:
                service['extra_info'] = f'protocol 2.0'
            elif port in [3306, 5432, 6379, 27017] and version:
                service['extra_info'] = 'unauthorized access possible'
            
            services.append(service)
        
        return {
            'target': target,
            'total_ports_scanned': 1000,
            'open_ports': len(ports),
            'services': services,
            'execution_time_seconds': random.uniform(30, 300),
            'scan_type': 'service_detection',
        }
    
    def create_scenario(self, scenario_id: str, name: str, description: str,
                       target: str, complexity: str, subdomain_count: int,
                       ports: List[int], technologies: List[str],
                       optimal_strategy: Dict[str, str],
                       reward_optimal: int, reward_suboptimal: int,
                       scenario_type: str) -> Dict[str, Any]:
        """Create a complete scenario with pre-computed results"""
        
        # Generate subdomains
        subdomains = self.generate_subdomains(target, subdomain_count, scenario_type)
        
        # Generate tool results
        subfinder_results = {
            'target': target,
            'subdomains': subdomains,
            'total_found': len(subdomains),
            'execution_time_seconds': random.uniform(5, 30),
            'sources_used': random.randint(5, 15),
        }
        
        httpx_results = self.generate_httpx_results(subdomains, ports, technologies)
        nmap_results = self.generate_nmap_results(ports, target)
        
        # Count critical services
        critical_services = []
        for service in nmap_results['services']:
            if service['port'] in [22, 3306, 5432, 6379, 27017, 1433, 3389, 445]:
                if service['version']:
                    critical_services.append(f"{service['service']} {service['version']}")
        
        return {
            'id': scenario_id,
            'name': name,
            'description': description,
            'target': target,
            'complexity': complexity,
            'scenario_type': scenario_type,
            
            # Metadata for state calculation
            'metadata': {
                'total_subdomains': len(subdomains),
                'live_endpoints': httpx_results['live_endpoints'],
                'open_ports': len(ports),
                'critical_services': len(critical_services),
                'port_list': ports,
                'technologies': technologies,
            },
            
            # Pre-computed tool results
            'tool_results': {
                'subfinder': subfinder_results,
                'httpx': httpx_results,
                'nmap': nmap_results,
            },
            
            # Optimal strategy
            'optimal_strategy': optimal_strategy,
            
            # Reward benchmarks
            'rewards': {
                'optimal': reward_optimal,
                'suboptimal': reward_suboptimal,
            }
        }
    
    def generate_all_scenarios(self) -> List[Dict[str, Any]]:
        """Generate all 25 scenarios"""
        scenarios = []
        
        # === WEB-ONLY SCENARIOS (5) ===
        
        # S1: Modern Web Startup
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_web_startup',
            name='Modern Web Startup',
            description='SaaS startup with microservices on standard web ports',
            target='startup.example.com',
            complexity='medium',
            subdomain_count=18,
            ports=[80, 443, 3000, 8080],
            technologies=['React', 'Node.js', 'Express.js', 'Nginx', 'Docker'],
            optimal_strategy={
                'subfinder_mode': 'comprehensive',
                'httpx_mode': 'full',
                'nmap_mode': 'skip',
                'reason': 'Pure web stack, no infra services. Nmap wastes time.'
            },
            reward_optimal=480,
            reward_suboptimal=320,
            scenario_type='web_startup'
        ))
        
        # S2: CDN-Heavy E-commerce
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_cdn_ecommerce',
            name='CDN-Heavy E-commerce',
            description='E-commerce site behind Cloudflare, minimal exposed services',
            target='shop.example.com',
            complexity='low',
            subdomain_count=12,
            ports=[443],
            technologies=['Cloudflare', 'WordPress', 'WooCommerce', 'Nginx'],
            optimal_strategy={
                'subfinder_mode': 'active',
                'httpx_mode': 'detailed',
                'nmap_mode': 'skip',
                'reason': 'Only HTTPS behind CDN. Nmap gives no value.'
            },
            reward_optimal=420,
            reward_suboptimal=280,
            scenario_type='web_cdn'
        ))
        
        # S3: API Gateway Architecture
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_api_gateway',
            name='API Gateway Architecture',
            description='Microservices behind API gateway, RESTful APIs',
            target='api.example.com',
            complexity='medium',
            subdomain_count=15,
            ports=[443, 8080],
            technologies=['Kong', 'Express.js', 'GraphQL', 'Node.js', 'Docker'],
            optimal_strategy={
                'subfinder_mode': 'comprehensive',
                'httpx_mode': 'full',
                'nmap_mode': 'skip',
                'reason': 'API-only, no backend services exposed.'
            },
            reward_optimal=490,
            reward_suboptimal=330,
            scenario_type='web_api'
        ))
        
        # S4: Multi-Web-Server Load Balanced
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_load_balanced',
            name='Load Balanced Web Farm',
            description='Multiple web servers behind load balancer',
            target='web.example.com',
            complexity='high',
            subdomain_count=22,
            ports=[80, 443, 8080, 8443],
            technologies=['HAProxy', 'Apache', 'Nginx', 'PHP', 'Laravel'],
            optimal_strategy={
                'subfinder_mode': 'comprehensive',
                'httpx_mode': 'full',
                'nmap_mode': 'skip',
                'reason': 'Load balancer + web servers only. No infra.'
            },
            reward_optimal=510,
            reward_suboptimal=350,
            scenario_type='web_loadbalanced'
        ))
        
        # S5: Development Environment (Web-Only)
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_dev_web',
            name='Development Web Environment',
            description='Development servers for frontend/backend testing',
            target='dev.example.com',
            complexity='medium',
            subdomain_count=16,
            ports=[3000, 8080, 8081],
            technologies=['Vite', 'Webpack', 'Express.js', 'React', 'Vue.js'],
            optimal_strategy={
                'subfinder_mode': 'active',
                'httpx_mode': 'thorough',
                'nmap_mode': 'skip',
                'reason': 'Dev servers, all web-based. No databases exposed.'
            },
            reward_optimal=450,
            reward_suboptimal=310,
            scenario_type='web_dev'
        ))
        
        # === INFRASTRUCTURE SCENARIOS (8) ===
        
        # S6: Database Server Cluster
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_database_cluster',
            name='Database Server Cluster',
            description='Production database servers with multiple DB types',
            target='db.example.com',
            complexity='very_high',
            subdomain_count=8,
            ports=[80, 443, 3306, 5432, 6379, 27017],
            technologies=['MySQL', 'PostgreSQL', 'Redis', 'MongoDB', 'phpMyAdmin'],
            optimal_strategy={
                'subfinder_mode': 'active',
                'httpx_mode': 'basic',
                'nmap_mode': 'service',
                'reason': 'CRITICAL: Need service versions for all databases!'
            },
            reward_optimal=820,
            reward_suboptimal=320,
            scenario_type='infra_database'
        ))
        
        # S7: Mail Server Infrastructure
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_mail_server',
            name='Mail Server Infrastructure',
            description='Enterprise mail server with SMTP/IMAP/POP3',
            target='mail.example.com',
            complexity='high',
            subdomain_count=6,
            ports=[25, 143, 587, 993, 995],
            technologies=['Postfix', 'Dovecot', 'SpamAssassin', 'ClamAV'],
            optimal_strategy={
                'subfinder_mode': 'passive',
                'httpx_mode': 'quick',
                'nmap_mode': 'full',
                'reason': 'Mail services NEED version detection for vulnerabilities.'
            },
            reward_optimal=780,
            reward_suboptimal=290,
            scenario_type='infra_mail'
        ))
        
        # S8: SSH Infrastructure
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_ssh_infra',
            name='SSH Infrastructure',
            description='Server farm with SSH access and backend services',
            target='infra.example.com',
            complexity='high',
            subdomain_count=10,
            ports=[22, 80, 443, 3306, 6379],
            technologies=['OpenSSH', 'MySQL', 'Redis', 'Ubuntu', 'Nginx'],
            optimal_strategy={
                'subfinder_mode': 'comprehensive',
                'httpx_mode': 'thorough',
                'nmap_mode': 'service',
                'reason': 'SSH + databases = need version info!'
            },
            reward_optimal=850,
            reward_suboptimal=340,
            scenario_type='infra_ssh'
        ))
        
        # S9: Enterprise Windows Domain
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_enterprise_windows',
            name='Enterprise Windows Domain',
            description='Windows AD environment with RDP/SMB/MSSQL',
            target='corp.example.com',
            complexity='very_high',
            subdomain_count=12,
            ports=[80, 443, 445, 1433, 3389],
            technologies=['Windows Server', 'Active Directory', 'MSSQL', 'IIS'],
            optimal_strategy={
                'subfinder_mode': 'comprehensive',
                'httpx_mode': 'full',
                'nmap_mode': 'service',
                'reason': 'Windows infrastructure = CRITICAL service detection!'
            },
            reward_optimal=880,
            reward_suboptimal=350,
            scenario_type='infra_windows'
        ))
        
        # S10: Development Infrastructure
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_dev_infra',
            name='Development Infrastructure',
            description='Dev servers with databases and CI/CD',
            target='dev-infra.example.com',
            complexity='high',
            subdomain_count=14,
            ports=[22, 80, 443, 5432, 8080, 9000],
            technologies=['Jenkins', 'PostgreSQL', 'Docker', 'GitLab', 'Nginx'],
            optimal_strategy={
                'subfinder_mode': 'comprehensive',
                'httpx_mode': 'full',
                'nmap_mode': 'full',
                'reason': 'Mix of CI/CD + databases = need full scan!'
            },
            reward_optimal=790,
            reward_suboptimal=330,
            scenario_type='infra_dev'
        ))
        
        # S11: Admin Panel Infrastructure
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_admin_infra',
            name='Admin Panel Infrastructure',
            description='Admin interfaces and control panels',
            target='admin.example.com',
            complexity='high',
            subdomain_count=9,
            ports=[80, 443, 8080, 8443, 9090],
            technologies=['Tomcat', 'cPanel', 'Webmin', 'phpMyAdmin', 'Apache'],
            optimal_strategy={
                'subfinder_mode': 'active',
                'httpx_mode': 'thorough',
                'nmap_mode': 'full',
                'reason': 'Admin panels = need to identify management software versions!'
            },
            reward_optimal=760,
            reward_suboptimal=310,
            scenario_type='infra_admin'
        ))
        
        # S12: Monitoring Stack
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_monitoring',
            name='Monitoring Stack',
            description='Prometheus/Grafana/ELK monitoring infrastructure',
            target='monitor.example.com',
            complexity='very_high',
            subdomain_count=11,
            ports=[80, 443, 3000, 9090, 9093, 9200, 5601],
            technologies=['Prometheus', 'Grafana', 'Elasticsearch', 'Kibana', 'Alertmanager'],
            optimal_strategy={
                'subfinder_mode': 'comprehensive',
                'httpx_mode': 'full',
                'nmap_mode': 'service',
                'reason': 'Monitoring stack = CRITICAL to identify versions!'
            },
            reward_optimal=840,
            reward_suboptimal=340,
            scenario_type='infra_monitoring'
        ))
        
        # S13: Full Stack Infrastructure
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_full_stack',
            name='Full Stack Infrastructure',
            description='Complete infrastructure with all services',
            target='full.example.com',
            complexity='very_high',
            subdomain_count=20,
            ports=[22, 80, 443, 3306, 5432, 6379, 8080, 9000],
            technologies=['Full Stack', 'MySQL', 'PostgreSQL', 'Redis', 'Jenkins', 'Nginx'],
            optimal_strategy={
                'subfinder_mode': 'comprehensive',
                'httpx_mode': 'full',
                'nmap_mode': 'service',
                'reason': 'Everything exposed = MUST scan everything!'
            },
            reward_optimal=920,
            reward_suboptimal=380,
            scenario_type='infra_fullstack'
        ))
        
        # === HYBRID SCENARIOS (7) ===
        
        # S14: Web + Monitoring
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_web_monitoring',
            name='Web + Monitoring',
            description='Web application with Prometheus monitoring',
            target='webapp-mon.example.com',
            complexity='medium',
            subdomain_count=13,
            ports=[80, 443, 9090],
            technologies=['React', 'Express.js', 'Prometheus', 'Nginx'],
            optimal_strategy={
                'subfinder_mode': 'comprehensive',
                'httpx_mode': 'full',
                'nmap_mode': 'quick',
                'reason': 'Mostly web, but Prometheus worth quick check.'
            },
            reward_optimal=580,
            reward_suboptimal=450,
            scenario_type='hybrid_web_monitoring'
        ))
        
        # S15: Web + Database
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_web_database',
            name='Web + Database',
            description='Web application with exposed MySQL',
            target='webapp-db.example.com',
            complexity='high',
            subdomain_count=11,
            ports=[80, 443, 3306],
            technologies=['PHP', 'Laravel', 'MySQL', 'Apache'],
            optimal_strategy={
                'subfinder_mode': 'active',
                'httpx_mode': 'thorough',
                'nmap_mode': 'thorough',
                'reason': 'MySQL exposed = worth thorough scan for version!'
            },
            reward_optimal=620,
            reward_suboptimal=480,
            scenario_type='hybrid_web_database'
        ))
        
        # S16: Web + SSH
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_web_ssh',
            name='Web + SSH',
            description='Web servers with SSH management access',
            target='webapp-ssh.example.com',
            complexity='medium',
            subdomain_count=14,
            ports=[22, 80, 443],
            technologies=['Nginx', 'Django', 'OpenSSH', 'Python'],
            optimal_strategy={
                'subfinder_mode': 'comprehensive',
                'httpx_mode': 'full',
                'nmap_mode': 'quick',
                'reason': 'Mostly web, SSH worth quick version check.'
            },
            reward_optimal=560,
            reward_suboptimal=440,
            scenario_type='hybrid_web_ssh'
        ))
        
        # S17: Web + Redis
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_web_redis',
            name='Web + Redis Cache',
            description='Web application with Redis caching layer',
            target='webapp-cache.example.com',
            complexity='medium',
            subdomain_count=12,
            ports=[80, 443, 6379],
            technologies=['Node.js', 'Redis', 'React', 'Express.js'],
            optimal_strategy={
                'subfinder_mode': 'active',
                'httpx_mode': 'thorough',
                'nmap_mode': 'thorough',
                'reason': 'Redis exposed = worth checking version/config!'
            },
            reward_optimal=610,
            reward_suboptimal=470,
            scenario_type='hybrid_web_redis'
        ))
        
        # S18: Web + Multiple Backends
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_web_backends',
            name='Web + Multiple Backend Services',
            description='Web frontend with multiple backend microservices',
            target='webapp-micro.example.com',
            complexity='high',
            subdomain_count=17,
            ports=[80, 443, 5000, 8080, 9000],
            technologies=['React', 'Flask', 'Go', 'Node.js', 'Docker'],
            optimal_strategy={
                'subfinder_mode': 'comprehensive',
                'httpx_mode': 'full',
                'nmap_mode': 'thorough',
                'reason': 'Multiple custom ports = worth identifying services!'
            },
            reward_optimal=640,
            reward_suboptimal=500,
            scenario_type='hybrid_web_backends'
        ))
        
        # S19: Web + Admin Panel
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_web_admin',
            name='Web + Admin Panel',
            description='Public website with admin control panel',
            target='webapp-admin.example.com',
            complexity='medium',
            subdomain_count=10,
            ports=[80, 443, 8443],
            technologies=['WordPress', 'Admin Panel', 'Nginx', 'PHP'],
            optimal_strategy={
                'subfinder_mode': 'active',
                'httpx_mode': 'thorough',
                'nmap_mode': 'quick',
                'reason': 'Admin panel on 8443 worth quick check.'
            },
            reward_optimal=570,
            reward_suboptimal=450,
            scenario_type='hybrid_web_admin'
        ))
        
        # S20: Web + Mail Services
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_web_mail',
            name='Web + Mail Services',
            description='Corporate website with mail server',
            target='webapp-mail.example.com',
            complexity='high',
            subdomain_count=9,
            ports=[80, 443, 25, 587],
            technologies=['Corporate Site', 'Postfix', 'Nginx', 'WordPress'],
            optimal_strategy={
                'subfinder_mode': 'active',
                'httpx_mode': 'detailed',
                'nmap_mode': 'thorough',
                'reason': 'Mail server = worth thorough version detection!'
            },
            reward_optimal=630,
            reward_suboptimal=490,
            scenario_type='hybrid_web_mail'
        ))
        
        # === EDGE CASE SCENARIOS (5) ===
        
        # S21: Custom Application Ports
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_custom_ports',
            name='Custom Application Ports',
            description='Custom applications on non-standard ports',
            target='custom.example.com',
            complexity='medium',
            subdomain_count=8,
            ports=[4000, 5000, 6000, 8888, 9999],
            technologies=['Custom', 'Go', 'Rust', 'Node.js'],
            optimal_strategy={
                'subfinder_mode': 'active',
                'httpx_mode': 'thorough',
                'nmap_mode': 'full',
                'reason': 'Custom ports = MUST identify what\'s running!'
            },
            reward_optimal=680,
            reward_suboptimal=420,
            scenario_type='edge_custom'
        ))
        
        # S22: Pure Backend (No Web)
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_pure_backend',
            name='Pure Backend Infrastructure',
            description='Backend services only, no web interfaces',
            target='backend.example.com',
            complexity='high',
            subdomain_count=5,
            ports=[22, 3306, 5432],
            technologies=['Backend only', 'MySQL', 'PostgreSQL', 'OpenSSH'],
            optimal_strategy={
                'subfinder_mode': 'passive',
                'httpx_mode': 'skip',
                'nmap_mode': 'service',
                'reason': 'No web = HTTPX useless, nmap critical!'
            },
            reward_optimal=720,
            reward_suboptimal=350,
            scenario_type='edge_backend'
        ))
        
        # S23: Single Subdomain, Many Ports
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_single_many',
            name='Single Subdomain, Many Ports',
            description='One server running many services',
            target='server.example.com',
            complexity='very_high',
            subdomain_count=1,
            ports=[22, 80, 443, 3306, 5432, 6379, 8080, 9000],
            technologies=['All-in-one', 'MySQL', 'PostgreSQL', 'Redis', 'Jenkins', 'Nginx'],
            optimal_strategy={
                'subfinder_mode': 'passive',
                'httpx_mode': 'thorough',
                'nmap_mode': 'service',
                'reason': 'Many services on one host = MUST scan all!'
            },
            reward_optimal=860,
            reward_suboptimal=440,
            scenario_type='edge_single_many'
        ))
        
        # S24: Many Subdomains, No Standard Ports
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_many_nonstandard',
            name='Many Subdomains, Non-Standard Ports',
            description='Microservices on custom ports',
            target='micro.example.com',
            complexity='high',
            subdomain_count=25,
            ports=[8081, 8082, 8083, 8084, 8085],
            technologies=['Microservices', 'Docker', 'Kubernetes', 'Go'],
            optimal_strategy={
                'subfinder_mode': 'comprehensive',
                'httpx_mode': 'full',
                'nmap_mode': 'thorough',
                'reason': 'Many custom ports = worth identifying services!'
            },
            reward_optimal=700,
            reward_suboptimal=520,
            scenario_type='edge_many_nonstandard'
        ))
        
        # S25: Mixed Custom Infrastructure
        scenarios.append(self.create_scenario(
            scenario_id='phase1b_mixed_custom',
            name='Mixed Custom Infrastructure',
            description='Combination of standard and custom services',
            target='mixed.example.com',
            complexity='very_high',
            subdomain_count=15,
            ports=[80, 443, 4567, 5678, 9876],
            technologies=['Mixed', 'Custom', 'Node.js', 'Python', 'Nginx'],
            optimal_strategy={
                'subfinder_mode': 'comprehensive',
                'httpx_mode': 'full',
                'nmap_mode': 'full',
                'reason': 'Custom + standard = need full identification!'
            },
            reward_optimal=750,
            reward_suboptimal=530,
            scenario_type='edge_mixed'
        ))
        
        return scenarios
    
    def save_scenarios(self, scenarios: List[Dict[str, Any]], output_dir: str = '.'):
        """Save scenarios to JSON files"""
        import os
        
        # Split into training (S1-S20) and test (S21-S25)
        train_scenarios = scenarios[:20]
        test_scenarios = scenarios[20:]
        
        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)
        
        # Save training scenarios
        train_path = os.path.join(output_dir, 'phase1b_train.json')
        with open(train_path, 'w') as f:
            json.dump({
                'version': '1.0',
                'generated_at': datetime.now().isoformat(),
                'total_scenarios': len(train_scenarios),
                'scenarios': train_scenarios
            }, f, indent=2)
        
        print(f"✅ Saved {len(train_scenarios)} training scenarios to {train_path}")
        
        # Save test scenarios
        test_path = os.path.join(output_dir, 'phase1b_test.json')
        with open(test_path, 'w') as f:
            json.dump({
                'version': '1.0',
                'generated_at': datetime.now().isoformat(),
                'total_scenarios': len(test_scenarios),
                'scenarios': test_scenarios
            }, f, indent=2)
        
        print(f"✅ Saved {len(test_scenarios)} test scenarios to {test_path}")
        
        return train_path, test_path


def validate_scenarios(scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate scenario diversity and quality"""
    
    # Collect metrics
    port_sets = [tuple(sorted(s['metadata']['port_list'])) for s in scenarios]
    complexities = [s['complexity'] for s in scenarios]
    scenario_types = [s['scenario_type'] for s in scenarios]
    subdomain_counts = [s['metadata']['total_subdomains'] for s in scenarios]
    
    # Calculate diversity
    unique_ports = len(set(port_sets))
    unique_types = len(set(scenario_types))
    
    # Port pattern diversity
    all_ports = set()
    for s in scenarios:
        all_ports.update(s['metadata']['port_list'])
    
    # Reward ranges
    rewards_optimal = [s['rewards']['optimal'] for s in scenarios]
    rewards_suboptimal = [s['rewards']['suboptimal'] for s in scenarios]
    
    validation_report = {
        'total_scenarios': len(scenarios),
        'unique_port_patterns': unique_ports,
        'unique_scenario_types': unique_types,
        'unique_ports_used': len(all_ports),
        'all_ports': sorted(list(all_ports)),
        'complexity_distribution': {
            'low': complexities.count('low'),
            'medium': complexities.count('medium'),
            'high': complexities.count('high'),
            'very_high': complexities.count('very_high'),
        },
        'subdomain_range': {
            'min': min(subdomain_counts),
            'max': max(subdomain_counts),
            'avg': sum(subdomain_counts) / len(subdomain_counts),
        },
        'reward_range_optimal': {
            'min': min(rewards_optimal),
            'max': max(rewards_optimal),
            'avg': sum(rewards_optimal) / len(rewards_optimal),
        },
        'reward_range_suboptimal': {
            'min': min(rewards_suboptimal),
            'max': max(rewards_suboptimal),
            'avg': sum(rewards_suboptimal) / len(rewards_suboptimal),
        },
        'checks': {
            'port_diversity_ok': unique_ports >= 15,
            'type_diversity_ok': unique_types >= 20,
            'reward_range_ok': (min(rewards_optimal) >= 400 and max(rewards_optimal) <= 950),
        }
    }
    
    return validation_report


def main():
    """Generate and validate all scenarios"""
    print("🚀 Phase 1B Scenario Generator")
    print("=" * 60)
    
    # Generate scenarios
    print("\n📝 Generating 25 scenarios...")
    generator = ScenarioGenerator()
    scenarios = generator.generate_all_scenarios()
    print(f"✅ Generated {len(scenarios)} scenarios")
    
    # Validate
    print("\n🔍 Validating scenario diversity...")
    report = validate_scenarios(scenarios)
    
    print(f"\n📊 Validation Report:")
    print(f"   Total scenarios: {report['total_scenarios']}")
    print(f"   Unique port patterns: {report['unique_port_patterns']}")
    print(f"   Unique scenario types: {report['unique_scenario_types']}")
    print(f"   Unique ports used: {report['unique_ports_used']}")
    print(f"   Ports: {report['all_ports']}")
    print(f"\n   Complexity distribution:")
    for k, v in report['complexity_distribution'].items():
        print(f"      {k}: {v}")
    print(f"\n   Subdomain range: {report['subdomain_range']['min']}-{report['subdomain_range']['max']} (avg: {report['subdomain_range']['avg']:.1f})")
    print(f"   Optimal reward range: {report['reward_range_optimal']['min']}-{report['reward_range_optimal']['max']} (avg: {report['reward_range_optimal']['avg']:.1f})")
    print(f"   Suboptimal reward range: {report['reward_range_suboptimal']['min']}-{report['reward_range_suboptimal']['max']} (avg: {report['reward_range_suboptimal']['avg']:.1f})")
    
    print(f"\n✅ Validation Checks:")
    for check, passed in report['checks'].items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}: {passed}")
    
    # Save scenarios
    print("\n💾 Saving scenarios...")
    train_path, test_path = generator.save_scenarios(scenarios, output_dir='.')
    
    # Calculate file sizes
    import os
    train_size = os.path.getsize(train_path) / 1024  # KB
    test_size = os.path.getsize(test_path) / 1024  # KB
    
    print(f"\n📦 File sizes:")
    print(f"   Training: {train_size:.1f} KB")
    print(f"   Test: {test_size:.1f} KB")
    print(f"   Total: {train_size + test_size:.1f} KB")
    
    print("\n" + "=" * 60)
    print("✅ Scenario generation complete!")
    print("\n🎯 Next Steps:")
    print("   1. Review generated JSON files")
    print("   2. Move to Day 4: Implement FullReconEnv")
    print("   3. Test environment can load scenarios")


if __name__ == '__main__':
    main()
