# Phase 1B Scenario Design Strategy

## 🎯 Core Objective

Train agent to answer: **"WHEN should I use nmap?"**

Not just "how to use nmap" but **"is it worth it?"**

---

## 📊 Distribution Strategy (Total: 25 Scenarios)

### Category 1: Web-Only (5 scenarios) - **Nmap LOW Value**

**Learning Goal**: Agent learns to SKIP nmap (efficiency!)

**Characteristics**:

- Only ports: 80, 443, 8080, 8443, 3000
- High subdomain count (15-25 subdomains)
- High live endpoint count (10-20 endpoints)
- Technologies: Web frameworks, CDN, load balancers
- **Optimal Strategy**: Subfinder comprehensive → HTTPX full → **SKIP nmap** (or quick at most)
- **Reward Range**: 400-500 if skip, 300-400 if use nmap (wasted time!)

**Port Patterns**:

1. Web startup: 80, 443, 3000
2. Multiple web servers: 80, 443, 8080, 8443
3. CDN-only: 443 (Cloudflare)
4. API gateway: 443, 8080
5. Development: 3000, 8080

### Category 2: Infrastructure (8 scenarios) - **Nmap HIGH Value**

**Learning Goal**: Agent learns to USE nmap (critical discovery!)

**Characteristics**:

- Mixed ports: Web + database + admin + mail
- Port diversity: 15-20 different ports
- Services that NEED version detection
- Critical services: SSH, RDP, databases, mail servers
- **Optimal Strategy**: Subfinder active/comprehensive → HTTPX thorough → **USE nmap full/service**
- **Reward Range**: 600-800 if use nmap, 300-400 if skip (missed discoveries!)

**Port Patterns**:

1. Database server: 80, 443, 3306 (MySQL), 5432 (PostgreSQL), 6379 (Redis)
2. Mail server: 25 (SMTP), 143 (IMAP), 993 (IMAPS), 587 (SMTP-submission)
3. SSH infrastructure: 22 (SSH), 80, 443, 3306
4. Enterprise: 80, 443, 3389 (RDP), 445 (SMB), 1433 (MSSQL)
5. Development servers: 22, 80, 443, 8080, 9000 (Jenkins), 5432
6. Admin panels: 80, 443, 8443, 8080 (admin), 9090 (control panel)
7. Monitoring stack: 80, 443, 9090 (Prometheus), 3000 (Grafana), 9200 (Elasticsearch)
8. Full stack: 22, 80, 443, 3306, 6379, 5432, 9000, 8080

### Category 3: Hybrid (7 scenarios) - **Nmap CONDITIONAL**

**Learning Goal**: Agent learns CONTEXT matters!

**Characteristics**:

- Mixed signals: Some web, some infrastructure
- Moderate port diversity: 5-10 different ports
- Decision depends on subdomain count vs port types
- **Optimal Strategy**: DEPENDS on balance!
  - If web-heavy with 1-2 interesting ports → nmap quick
  - If infra-heavy → nmap full
  - If balanced → nmap thorough
- **Reward Range**: 500-650 if correct decision

**Port Patterns**:

1. Web + monitoring: 80, 443, 9090 (Prometheus) → nmap quick on monitoring
2. Web + database: 80, 443, 3306 → nmap thorough on database
3. Web + SSH: 80, 443, 22 → nmap quick on SSH
4. Web + Redis: 80, 443, 6379 → nmap thorough on Redis
5. Web + multiple backends: 80, 443, 8080, 9000, 5000 → nmap thorough
6. Web + admin: 80, 443, 8443 (admin panel) → nmap quick on admin
7. Web + mail: 80, 443, 25, 587 → nmap thorough on mail

### Category 4: Edge Cases (5 scenarios)

**Learning Goal**: Agent handles unusual patterns!

**Characteristics**:

- Unusual port combinations
- Very high or very low subdomain counts
- Unusual technologies
- Custom ports (4000-10000 range)
- **Optimal Strategy**: VARIES!

**Port Patterns**:

1. Custom app ports: 4000, 5000, 6000, 8888, 9999
2. No web ports: 22, 3306, 5432 (pure backend)
3. Single subdomain, many ports: 22, 80, 443, 3306, 6379, 5432, 8080, 9000
4. Many subdomains, no standard ports: 8081, 8082, 8083, 8084
5. Mixed custom: 80, 443, 4567, 5678, 9876

---

## 🎨 Port Diversity Matrix (15+ Unique Patterns)

### Web Ports (Common)

- 80 (HTTP)
- 443 (HTTPS)
- 8080 (HTTP-alt)
- 8443 (HTTPS-alt)
- 3000 (Node.js/React dev)
- 8081, 8082, 8083 (Multiple instances)

### Infrastructure Ports (High Nmap Value)

- 22 (SSH) - **Version matters!**
- 3306 (MySQL) - **Critical!**
- 5432 (PostgreSQL) - **Critical!**
- 6379 (Redis) - **Critical!**
- 27017 (MongoDB) - **Critical!**
- 1433 (MSSQL) - **Critical!**

### Admin/Management Ports (Medium-High Value)

- 3389 (RDP) - **Critical!**
- 445 (SMB) - **Critical!**
- 8443 (Admin panels)
- 9090 (Prometheus/Control panels)
- 9000 (Jenkins/Sonarqube)

### Mail Ports (Medium Value)

- 25 (SMTP)
- 587 (SMTP-submission)
- 143 (IMAP)
- 993 (IMAPS)
- 110 (POP3)
- 995 (POP3S)

### Monitoring/Logging Ports (Medium Value)

- 9090 (Prometheus)
- 3000 (Grafana)
- 9200 (Elasticsearch)
- 5601 (Kibana)
- 9093 (Alertmanager)

### Custom/Dev Ports (Low-Medium Value)

- 4000-10000 range (custom apps)
- 5000 (Flask default)
- 8888 (Jupyter)
- 9999 (Custom services)

---

## 📋 Detailed Scenario Specifications

### WEB-ONLY Scenarios (5)

#### S1: Modern Web Startup

```json
{
  "id": "phase1b_web_startup",
  "name": "Modern Web Startup",
  "description": "SaaS startup with microservices on standard web ports",
  "target": "startup.example.com",
  "complexity": "medium",
  "subdomain_count": 18,
  "live_endpoints": 15,
  "open_ports": [80, 443, 3000, 8080],
  "critical_services": [],
  "technologies": ["React", "Node.js", "Nginx", "Docker"],
  "optimal_strategy": {
    "subfinder_mode": "comprehensive",
    "httpx_mode": "full",
    "nmap_mode": "skip",
    "reason": "Pure web stack, no infra services. Nmap wastes time."
  },
  "reward_if_optimal": 480,
  "reward_if_nmap_used": 320
}
```

#### S2: CDN-Heavy E-commerce

```json
{
  "id": "phase1b_cdn_ecommerce",
  "name": "CDN-Heavy E-commerce",
  "description": "E-commerce site behind Cloudflare, minimal exposed services",
  "target": "shop.example.com",
  "complexity": "low",
  "subdomain_count": 12,
  "live_endpoints": 10,
  "open_ports": [443],
  "critical_services": [],
  "technologies": ["Cloudflare", "WordPress", "WooCommerce"],
  "optimal_strategy": {
    "subfinder_mode": "active",
    "httpx_mode": "detailed",
    "nmap_mode": "skip",
    "reason": "Only HTTPS behind CDN. Nmap gives no value."
  },
  "reward_if_optimal": 420,
  "reward_if_nmap_used": 280
}
```

#### S3: API Gateway Architecture

```json
{
  "id": "phase1b_api_gateway",
  "name": "API Gateway Architecture",
  "description": "Microservices behind API gateway, RESTful APIs",
  "target": "api.example.com",
  "complexity": "medium",
  "subdomain_count": 15,
  "live_endpoints": 20,
  "open_ports": [443, 8080],
  "critical_services": [],
  "technologies": ["Kong", "Express.js", "GraphQL"],
  "optimal_strategy": {
    "subfinder_mode": "comprehensive",
    "httpx_mode": "full",
    "nmap_mode": "skip",
    "reason": "API-only, no backend services exposed."
  },
  "reward_if_optimal": 490,
  "reward_if_nmap_used": 330
}
```

#### S4: Multi-Web-Server Load Balanced

```json
{
  "id": "phase1b_load_balanced",
  "name": "Load Balanced Web Farm",
  "description": "Multiple web servers behind load balancer",
  "target": "web.example.com",
  "complexity": "high",
  "subdomain_count": 22,
  "live_endpoints": 18,
  "open_ports": [80, 443, 8080, 8443],
  "critical_services": [],
  "technologies": ["HAProxy", "Apache", "Nginx"],
  "optimal_strategy": {
    "subfinder_mode": "comprehensive",
    "httpx_mode": "full",
    "nmap_mode": "skip",
    "reason": "Load balancer + web servers only. No infra."
  },
  "reward_if_optimal": 510,
  "reward_if_nmap_used": 350
}
```

#### S5: Development Environment (Web-Only)

```json
{
  "id": "phase1b_dev_web",
  "name": "Development Web Environment",
  "description": "Development servers for frontend/backend testing",
  "target": "dev.example.com",
  "complexity": "medium",
  "subdomain_count": 16,
  "live_endpoints": 14,
  "open_ports": [3000, 8080, 8081],
  "critical_services": [],
  "technologies": ["Vite", "Webpack", "Express"],
  "optimal_strategy": {
    "subfinder_mode": "active",
    "httpx_mode": "thorough",
    "nmap_mode": "skip",
    "reason": "Dev servers, all web-based. No databases exposed."
  },
  "reward_if_optimal": 450,
  "reward_if_nmap_used": 310
}
```

---

### INFRASTRUCTURE Scenarios (8)

#### S6: Database Server Cluster

```json
{
  "id": "phase1b_database_cluster",
  "name": "Database Server Cluster",
  "description": "Production database servers with multiple DB types",
  "target": "db.example.com",
  "complexity": "very_high",
  "subdomain_count": 8,
  "live_endpoints": 5,
  "open_ports": [80, 443, 3306, 5432, 6379, 27017],
  "critical_services": [
    "MySQL 8.0.33",
    "PostgreSQL 15.2",
    "Redis 7.0",
    "MongoDB 6.0"
  ],
  "technologies": ["MySQL", "PostgreSQL", "Redis", "MongoDB"],
  "optimal_strategy": {
    "subfinder_mode": "active",
    "httpx_mode": "basic",
    "nmap_mode": "service",
    "reason": "CRITICAL: Need service versions for all databases!"
  },
  "reward_if_optimal": 820,
  "reward_if_skip_nmap": 320
}
```

#### S7: Mail Server Infrastructure

```json
{
  "id": "phase1b_mail_server",
  "name": "Mail Server Infrastructure",
  "description": "Enterprise mail server with SMTP/IMAP/POP3",
  "target": "mail.example.com",
  "complexity": "high",
  "subdomain_count": 6,
  "live_endpoints": 4,
  "open_ports": [25, 143, 587, 993, 995],
  "critical_services": ["Postfix 3.7.2", "Dovecot 2.3.19"],
  "technologies": ["Postfix", "Dovecot", "SpamAssassin"],
  "optimal_strategy": {
    "subfinder_mode": "passive",
    "httpx_mode": "quick",
    "nmap_mode": "full",
    "reason": "Mail services NEED version detection for vulnerabilities."
  },
  "reward_if_optimal": 780,
  "reward_if_skip_nmap": 290
}
```

#### S8: SSH Infrastructure

```json
{
  "id": "phase1b_ssh_infra",
  "name": "SSH Infrastructure",
  "description": "Server farm with SSH access and backend services",
  "target": "infra.example.com",
  "complexity": "high",
  "subdomain_count": 10,
  "live_endpoints": 7,
  "open_ports": [22, 80, 443, 3306, 6379],
  "critical_services": ["OpenSSH 8.9p1", "MySQL 8.0.32", "Redis 6.2"],
  "technologies": ["OpenSSH", "MySQL", "Redis", "Ubuntu"],
  "optimal_strategy": {
    "subfinder_mode": "comprehensive",
    "httpx_mode": "thorough",
    "nmap_mode": "service",
    "reason": "SSH + databases = need version info!"
  },
  "reward_if_optimal": 850,
  "reward_if_skip_nmap": 340
}
```

#### S9: Enterprise Windows Domain

```json
{
  "id": "phase1b_enterprise_windows",
  "name": "Enterprise Windows Domain",
  "description": "Windows AD environment with RDP/SMB/MSSQL",
  "target": "corp.example.com",
  "complexity": "very_high",
  "subdomain_count": 12,
  "live_endpoints": 8,
  "open_ports": [80, 443, 445, 1433, 3389],
  "critical_services": ["MSSQL 2019", "SMB 3.1.1", "RDP"],
  "technologies": ["Windows Server", "Active Directory", "MSSQL"],
  "optimal_strategy": {
    "subfinder_mode": "comprehensive",
    "httpx_mode": "full",
    "nmap_mode": "service",
    "reason": "Windows infrastructure = CRITICAL service detection!"
  },
  "reward_if_optimal": 880,
  "reward_if_skip_nmap": 350
}
```

#### S10: Development Infrastructure

```json
{
  "id": "phase1b_dev_infra",
  "name": "Development Infrastructure",
  "description": "Dev servers with databases and CI/CD",
  "target": "dev-infra.example.com",
  "complexity": "high",
  "subdomain_count": 14,
  "live_endpoints": 11,
  "open_ports": [22, 80, 443, 5432, 8080, 9000],
  "critical_services": ["PostgreSQL 14.5", "Jenkins 2.387"],
  "technologies": ["Jenkins", "PostgreSQL", "Docker", "GitLab"],
  "optimal_strategy": {
    "subfinder_mode": "comprehensive",
    "httpx_mode": "full",
    "nmap_mode": "full",
    "reason": "Mix of CI/CD + databases = need full scan!"
  },
  "reward_if_optimal": 790,
  "reward_if_skip_nmap": 330
}
```

#### S11: Admin Panel Infrastructure

```json
{
  "id": "phase1b_admin_infra",
  "name": "Admin Panel Infrastructure",
  "description": "Admin interfaces and control panels",
  "target": "admin.example.com",
  "complexity": "high",
  "subdomain_count": 9,
  "live_endpoints": 7,
  "open_ports": [80, 443, 8080, 8443, 9090],
  "critical_services": ["Tomcat 9.0.70", "Control Panel"],
  "technologies": ["Tomcat", "cPanel", "Webmin"],
  "optimal_strategy": {
    "subfinder_mode": "active",
    "httpx_mode": "thorough",
    "nmap_mode": "full",
    "reason": "Admin panels = need to identify management software versions!"
  },
  "reward_if_optimal": 760,
  "reward_if_skip_nmap": 310
}
```

#### S12: Monitoring Stack

```json
{
  "id": "phase1b_monitoring",
  "name": "Monitoring Stack",
  "description": "Prometheus/Grafana/ELK monitoring infrastructure",
  "target": "monitor.example.com",
  "complexity": "very_high",
  "subdomain_count": 11,
  "live_endpoints": 9,
  "open_ports": [80, 443, 3000, 9090, 9093, 9200, 5601],
  "critical_services": ["Prometheus 2.40", "Grafana 9.3", "Elasticsearch 8.6"],
  "technologies": ["Prometheus", "Grafana", "Elasticsearch", "Kibana"],
  "optimal_strategy": {
    "subfinder_mode": "comprehensive",
    "httpx_mode": "full",
    "nmap_mode": "service",
    "reason": "Monitoring stack = CRITICAL to identify versions!"
  },
  "reward_if_optimal": 840,
  "reward_if_skip_nmap": 340
}
```

#### S13: Full Stack Infrastructure

```json
{
  "id": "phase1b_full_stack",
  "name": "Full Stack Infrastructure",
  "description": "Complete infrastructure with all services",
  "target": "full.example.com",
  "complexity": "very_high",
  "subdomain_count": 20,
  "live_endpoints": 16,
  "open_ports": [22, 80, 443, 3306, 5432, 6379, 8080, 9000],
  "critical_services": [
    "OpenSSH 8.9",
    "MySQL 8.0",
    "PostgreSQL 15",
    "Redis 7.0",
    "Jenkins 2.387"
  ],
  "technologies": ["Full Stack"],
  "optimal_strategy": {
    "subfinder_mode": "comprehensive",
    "httpx_mode": "full",
    "nmap_mode": "service",
    "reason": "Everything exposed = MUST scan everything!"
  },
  "reward_if_optimal": 920,
  "reward_if_skip_nmap": 380
}
```

---

### HYBRID Scenarios (7)

#### S14: Web + Monitoring

```json
{
  "id": "phase1b_web_monitoring",
  "name": "Web + Monitoring",
  "description": "Web application with Prometheus monitoring",
  "target": "webapp-mon.example.com",
  "complexity": "medium",
  "subdomain_count": 13,
  "live_endpoints": 11,
  "open_ports": [80, 443, 9090],
  "critical_services": ["Prometheus 2.40"],
  "technologies": ["React", "Express", "Prometheus"],
  "optimal_strategy": {
    "subfinder_mode": "comprehensive",
    "httpx_mode": "full",
    "nmap_mode": "quick",
    "reason": "Mostly web, but Prometheus worth quick check."
  },
  "reward_if_optimal": 580,
  "reward_if_suboptimal": 450
}
```

#### S15: Web + Database

```json
{
  "id": "phase1b_web_database",
  "name": "Web + Database",
  "description": "Web application with exposed MySQL",
  "target": "webapp-db.example.com",
  "complexity": "high",
  "subdomain_count": 11,
  "live_endpoints": 9,
  "open_ports": [80, 443, 3306],
  "critical_services": ["MySQL 8.0.33"],
  "technologies": ["PHP", "Laravel", "MySQL"],
  "optimal_strategy": {
    "subfinder_mode": "active",
    "httpx_mode": "thorough",
    "nmap_mode": "thorough",
    "reason": "MySQL exposed = worth thorough scan for version!"
  },
  "reward_if_optimal": 620,
  "reward_if_suboptimal": 480
}
```

#### S16: Web + SSH

```json
{
  "id": "phase1b_web_ssh",
  "name": "Web + SSH",
  "description": "Web servers with SSH management access",
  "target": "webapp-ssh.example.com",
  "complexity": "medium",
  "subdomain_count": 14,
  "live_endpoints": 12,
  "open_ports": [22, 80, 443],
  "critical_services": ["OpenSSH 8.9p1"],
  "technologies": ["Nginx", "Django", "OpenSSH"],
  "optimal_strategy": {
    "subfinder_mode": "comprehensive",
    "httpx_mode": "full",
    "nmap_mode": "quick",
    "reason": "Mostly web, SSH worth quick version check."
  },
  "reward_if_optimal": 560,
  "reward_if_suboptimal": 440
}
```

#### S17: Web + Redis

```json
{
  "id": "phase1b_web_redis",
  "name": "Web + Redis Cache",
  "description": "Web application with Redis caching layer",
  "target": "webapp-cache.example.com",
  "complexity": "medium",
  "subdomain_count": 12,
  "live_endpoints": 10,
  "open_ports": [80, 443, 6379],
  "critical_services": ["Redis 7.0.8"],
  "technologies": ["Node.js", "Redis", "React"],
  "optimal_strategy": {
    "subfinder_mode": "active",
    "httpx_mode": "thorough",
    "nmap_mode": "thorough",
    "reason": "Redis exposed = worth checking version/config!"
  },
  "reward_if_optimal": 610,
  "reward_if_suboptimal": 470
}
```

#### S18: Web + Multiple Backends

```json
{
  "id": "phase1b_web_backends",
  "name": "Web + Multiple Backend Services",
  "description": "Web frontend with multiple backend microservices",
  "target": "webapp-micro.example.com",
  "complexity": "high",
  "subdomain_count": 17,
  "live_endpoints": 14,
  "open_ports": [80, 443, 5000, 8080, 9000],
  "critical_services": ["Custom services"],
  "technologies": ["React", "Flask", "Go", "Node.js"],
  "optimal_strategy": {
    "subfinder_mode": "comprehensive",
    "httpx_mode": "full",
    "nmap_mode": "thorough",
    "reason": "Multiple custom ports = worth identifying services!"
  },
  "reward_if_optimal": 640,
  "reward_if_suboptimal": 500
}
```

#### S19: Web + Admin Panel

```json
{
  "id": "phase1b_web_admin",
  "name": "Web + Admin Panel",
  "description": "Public website with admin control panel",
  "target": "webapp-admin.example.com",
  "complexity": "medium",
  "subdomain_count": 10,
  "live_endpoints": 8,
  "open_ports": [80, 443, 8443],
  "critical_services": ["Admin Panel"],
  "technologies": ["WordPress", "Admin Panel"],
  "optimal_strategy": {
    "subfinder_mode": "active",
    "httpx_mode": "thorough",
    "nmap_mode": "quick",
    "reason": "Admin panel on 8443 worth quick check."
  },
  "reward_if_optimal": 570,
  "reward_if_suboptimal": 450
}
```

#### S20: Web + Mail Services

```json
{
  "id": "phase1b_web_mail",
  "name": "Web + Mail Services",
  "description": "Corporate website with mail server",
  "target": "webapp-mail.example.com",
  "complexity": "high",
  "subdomain_count": 9,
  "live_endpoints": 7,
  "open_ports": [80, 443, 25, 587],
  "critical_services": ["Postfix 3.7.2"],
  "technologies": ["Corporate Site", "Postfix"],
  "optimal_strategy": {
    "subfinder_mode": "active",
    "httpx_mode": "detailed",
    "nmap_mode": "thorough",
    "reason": "Mail server = worth thorough version detection!"
  },
  "reward_if_optimal": 630,
  "reward_if_suboptimal": 490
}
```

---

### EDGE CASE Scenarios (5)

#### S21: Custom Application Ports

```json
{
  "id": "phase1b_custom_ports",
  "name": "Custom Application Ports",
  "description": "Custom applications on non-standard ports",
  "target": "custom.example.com",
  "complexity": "medium",
  "subdomain_count": 8,
  "live_endpoints": 6,
  "open_ports": [4000, 5000, 6000, 8888, 9999],
  "critical_services": ["Custom apps"],
  "technologies": ["Custom"],
  "optimal_strategy": {
    "subfinder_mode": "active",
    "httpx_mode": "thorough",
    "nmap_mode": "full",
    "reason": "Custom ports = MUST identify what's running!"
  },
  "reward_if_optimal": 680,
  "reward_if_suboptimal": 420
}
```

#### S22: Pure Backend (No Web)

```json
{
  "id": "phase1b_pure_backend",
  "name": "Pure Backend Infrastructure",
  "description": "Backend services only, no web interfaces",
  "target": "backend.example.com",
  "complexity": "high",
  "subdomain_count": 5,
  "live_endpoints": 2,
  "open_ports": [22, 3306, 5432],
  "critical_services": ["OpenSSH 8.9", "MySQL 8.0", "PostgreSQL 15"],
  "technologies": ["Backend only"],
  "optimal_strategy": {
    "subfinder_mode": "passive",
    "httpx_mode": "skip",
    "nmap_mode": "service",
    "reason": "No web = HTTPX useless, nmap critical!"
  },
  "reward_if_optimal": 720,
  "reward_if_suboptimal": 350
}
```

#### S23: Single Subdomain, Many Ports

```json
{
  "id": "phase1b_single_many",
  "name": "Single Subdomain, Many Ports",
  "description": "One server running many services",
  "target": "server.example.com",
  "complexity": "very_high",
  "subdomain_count": 1,
  "live_endpoints": 8,
  "open_ports": [22, 80, 443, 3306, 5432, 6379, 8080, 9000],
  "critical_services": ["Many services"],
  "technologies": ["All-in-one server"],
  "optimal_strategy": {
    "subfinder_mode": "passive",
    "httpx_mode": "thorough",
    "nmap_mode": "service",
    "reason": "Many services on one host = MUST scan all!"
  },
  "reward_if_optimal": 860,
  "reward_if_suboptimal": 440
}
```

#### S24: Many Subdomains, No Standard Ports

```json
{
  "id": "phase1b_many_nonstandard",
  "name": "Many Subdomains, Non-Standard Ports",
  "description": "Microservices on custom ports",
  "target": "micro.example.com",
  "complexity": "high",
  "subdomain_count": 25,
  "live_endpoints": 20,
  "open_ports": [8081, 8082, 8083, 8084, 8085],
  "critical_services": ["Microservices"],
  "technologies": ["Microservices"],
  "optimal_strategy": {
    "subfinder_mode": "comprehensive",
    "httpx_mode": "full",
    "nmap_mode": "thorough",
    "reason": "Many custom ports = worth identifying services!"
  },
  "reward_if_optimal": 700,
  "reward_if_suboptimal": 520
}
```

#### S25: Mixed Custom Infrastructure

```json
{
  "id": "phase1b_mixed_custom",
  "name": "Mixed Custom Infrastructure",
  "description": "Combination of standard and custom services",
  "target": "mixed.example.com",
  "complexity": "very_high",
  "subdomain_count": 15,
  "live_endpoints": 12,
  "open_ports": [80, 443, 4567, 5678, 9876],
  "critical_services": ["Custom services"],
  "technologies": ["Mixed"],
  "optimal_strategy": {
    "subfinder_mode": "comprehensive",
    "httpx_mode": "full",
    "nmap_mode": "full",
    "reason": "Custom + standard = need full identification!"
  },
  "reward_if_optimal": 750,
  "reward_if_suboptimal": 530
}
```

---

## 🎯 Learning Objectives Summary

**After training on these 25 scenarios, agent should learn**:

### Pattern 1: Pure Web → Skip Nmap

- **Indicators**: Only 80/443/8080/8443/3000
- **High subdomain count** (15-25)
- **Technologies**: React, Angular, Vue, CDN
- **Decision**: Use subfinder + httpx, **SKIP nmap** (or quick at most)

### Pattern 2: Infrastructure → Use Nmap

- **Indicators**: Databases, SSH, mail, RDP, SMB
- **Ports**: 22, 25, 445, 1433, 3306, 3389, 5432, 6379
- **Decision**: Use nmap **full or service** (critical!)

### Pattern 3: Hybrid → Context-Dependent

- **If**: 1-2 interesting ports among mostly web
- **Decision**: nmap quick
- **If**: Multiple interesting ports
- **Decision**: nmap thorough or full

### Pattern 4: Custom Ports → Investigate

- **Indicators**: Ports 4000-10000 range
- **Decision**: nmap thorough or full (identify unknown services)

### Pattern 5: Single Host, Many Services → Deep Scan

- **Indicators**: Low subdomain count, high port count
- **Decision**: nmap service (all-in-one server)

---

## 📊 Expected Reward Ranges (Validation)

| Scenario Type  | Optimal Reward | Suboptimal Reward | Delta    |
| -------------- | -------------- | ----------------- | -------- |
| Web-Only       | 420-510        | 280-350           | ~150     |
| Infrastructure | 760-920        | 290-380           | ~450     |
| Hybrid         | 560-640        | 440-520           | ~80-120  |
| Edge Cases     | 680-860        | 350-530           | ~150-330 |

**Overall Range**: 420-920 optimal, 280-530 suboptimal

**Agent Target**: Learn to consistently choose optimal (>600 mean reward)

---

## ✅ Validation Checklist

Before generating scenarios:

- [ ] 25 total scenarios designed
- [ ] Distribution: 5 web, 8 infra, 7 hybrid, 5 edge ✅
- [ ] Port diversity: 15+ unique patterns ✅
- [ ] Reward ranges realistic (420-920) ✅
- [ ] Clear optimal strategy per scenario ✅
- [ ] Technologies diverse ✅
- [ ] Nmap value clearly differentiated ✅
- [ ] Edge cases cover unusual patterns ✅

**Status**: ✅ **DESIGN COMPLETE** - Ready for Day 3 (Generation)!

---

## 🚀 Next Steps (Day 3)

1. Create `generate_scenarios_phase1b.py`
2. Generate full JSON with pre-computed tool results
3. Split: 20 training (S1-S20) + 5 test (S21-S25)
4. Validate diversity metrics
5. Test environment can load scenarios

**Timeline**: 6 hours on Day 3
