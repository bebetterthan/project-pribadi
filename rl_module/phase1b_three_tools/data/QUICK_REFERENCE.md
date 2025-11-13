# Phase 1B Scenario Quick Reference

## 📊 Distribution (25 Scenarios Total)

| Category       | Count | Nmap Value  | Reward Range (Optimal) |
| -------------- | ----- | ----------- | ---------------------- |
| Web-Only       | 5     | LOW (skip)  | 420-510                |
| Infrastructure | 8     | HIGH (use)  | 760-920                |
| Hybrid         | 7     | CONDITIONAL | 560-640                |
| Edge Cases     | 5     | VARIES      | 680-860                |

## 🎯 Learning Goals

**Core Question**: "WHEN should I use nmap?"

### Agent Must Learn:

1. **Pure web** (80/443/8080) → **SKIP nmap** (efficiency!)
2. **Databases/SSH/Mail** (22/3306/5432) → **USE nmap** (critical!)
3. **Mixed signals** → **CONTEXT matters** (quick vs thorough vs full)
4. **Custom ports** (4000-10000) → **INVESTIGATE** (unknown services)

## 🔢 Port Value Matrix

### 🟢 HIGH Nmap Value (Infrastructure)

- **SSH**: 22
- **Databases**: 3306 (MySQL), 5432 (PostgreSQL), 6379 (Redis), 27017 (MongoDB), 1433 (MSSQL)
- **Windows**: 3389 (RDP), 445 (SMB)
- **Mail**: 25 (SMTP), 587, 143 (IMAP), 993 (IMAPS)
- **Admin**: 9000 (Jenkins), 9090 (Prometheus)

### 🟡 MEDIUM Nmap Value (Hybrid)

- **Monitoring**: 9090 (Prometheus), 3000 (Grafana), 9200 (Elasticsearch)
- **Admin panels**: 8443, 9090
- **Custom ports**: 4000-10000 range

### 🔴 LOW Nmap Value (Web-Only)

- **Web**: 80, 443, 8080, 8443
- **Dev**: 3000 (Node/React), 8081, 8082

## 📋 Scenario List (25)

### WEB-ONLY (5) - Skip Nmap

1. **S1**: Modern Web Startup → 480 optimal, 320 if nmap
2. **S2**: CDN E-commerce → 420 optimal, 280 if nmap
3. **S3**: API Gateway → 490 optimal, 330 if nmap
4. **S4**: Load Balanced Web → 510 optimal, 350 if nmap
5. **S5**: Dev Web Environment → 450 optimal, 310 if nmap

### INFRASTRUCTURE (8) - Use Nmap

6. **S6**: Database Cluster → 820 optimal, 320 if skip
7. **S7**: Mail Server → 780 optimal, 290 if skip
8. **S8**: SSH Infrastructure → 850 optimal, 340 if skip
9. **S9**: Enterprise Windows → 880 optimal, 350 if skip
10. **S10**: Dev Infrastructure → 790 optimal, 330 if skip
11. **S11**: Admin Panels → 760 optimal, 310 if skip
12. **S12**: Monitoring Stack → 840 optimal, 340 if skip
13. **S13**: Full Stack → 920 optimal, 380 if skip

### HYBRID (7) - Conditional

14. **S14**: Web + Monitoring → 580 quick, 450 skip
15. **S15**: Web + Database → 620 thorough, 480 skip
16. **S16**: Web + SSH → 560 quick, 440 skip
17. **S17**: Web + Redis → 610 thorough, 470 skip
18. **S18**: Web + Backends → 640 thorough, 500 skip
19. **S19**: Web + Admin → 570 quick, 450 skip
20. **S20**: Web + Mail → 630 thorough, 490 skip

### EDGE CASES (5) - Varies

21. **S21**: Custom Ports → 680 full, 420 skip
22. **S22**: Pure Backend → 720 service, 350 skip
23. **S23**: Single+Many → 860 service, 440 skip
24. **S24**: Many+Nonstandard → 700 thorough, 520 skip
25. **S25**: Mixed Custom → 750 full, 530 skip

## 🎨 Port Diversity (15+ Unique Patterns)

### Group A: Web-Only Patterns

- Pattern 1: 80, 443, 3000
- Pattern 2: 80, 443, 8080, 8443
- Pattern 3: 443 (CDN only)
- Pattern 4: 443, 8080 (API)
- Pattern 5: 3000, 8080 (Dev)

### Group B: Infrastructure Patterns

- Pattern 6: 80, 443, 3306, 5432, 6379 (Databases)
- Pattern 7: 25, 143, 587, 993, 995 (Mail)
- Pattern 8: 22, 80, 443, 3306 (SSH+DB)
- Pattern 9: 80, 443, 445, 1433, 3389 (Windows)
- Pattern 10: 22, 80, 443, 5432, 8080, 9000 (Dev Infra)
- Pattern 11: 80, 443, 8080, 8443, 9090 (Admin)
- Pattern 12: 80, 443, 3000, 9090, 9093, 9200, 5601 (Monitoring)
- Pattern 13: 22, 80, 443, 3306, 5432, 6379, 8080, 9000 (Full)

### Group C: Hybrid Patterns

- Pattern 14: 80, 443, 9090 (Web+Mon)
- Pattern 15: 80, 443, 3306 (Web+DB)

### Group D: Edge Patterns

- Pattern 16: 4000, 5000, 6000, 8888, 9999 (Custom)
- Pattern 17: 22, 3306, 5432 (Backend only)
- Pattern 18: 8081, 8082, 8083, 8084 (Many custom)

## 🎓 Optimal Strategies

### Web-Only Strategy

```
Subfinder: comprehensive (find all subdomains)
HTTPX: full (discover all endpoints)
Nmap: SKIP (no value, wastes time)
→ Reward: 420-510
```

### Infrastructure Strategy

```
Subfinder: active/comprehensive (find services)
HTTPX: basic/thorough (identify web interfaces)
Nmap: full/service (CRITICAL - version detection!)
→ Reward: 760-920
```

### Hybrid Strategy (CONTEXT-DEPENDENT)

```
If mostly web + 1-2 interesting ports:
  Nmap: quick (fast check)
  → Reward: 560-580

If multiple interesting ports:
  Nmap: thorough (balanced scan)
  → Reward: 610-640
```

### Edge Case Strategy

```
Custom ports: full (identify unknowns)
Pure backend: service (no web = nmap critical)
Single+many: service (all-in-one server)
Many+custom: thorough (microservices)
→ Reward: 680-860
```

## 📈 Expected Training Results

### Baselines

- **Random**: ~200 (discovery by luck)
- **Hardcoded 3-Tool**: ~300 (always comprehensive × 3)
- **Phase 1A Wrapper**: ~365 (good at 2 tools, basic at nmap)

### Target (Trained Phase 1B Agent)

- **Mean Reward**: 475-600
- **vs Phase 1A**: +30% improvement (target: >475)
- **vs Hardcoded**: +50% improvement (target: >450)
- **Variance**: <150 (stable)
- **Intelligent Behavior**: Observable nmap usage patterns

## ✅ Diversity Validation

### Subdomain Counts

- Low: 1-6 (edge cases)
- Medium: 8-14 (typical)
- High: 15-25 (web-heavy)

### Port Counts

- Minimal: 1-3 (focused)
- Moderate: 4-6 (mixed)
- High: 7-12 (complex)

### Technology Coverage

- Web frameworks: React, Vue, Angular, Node.js
- Databases: MySQL, PostgreSQL, Redis, MongoDB, MSSQL
- Mail: Postfix, Dovecot
- Infrastructure: SSH, Docker, Kubernetes
- Monitoring: Prometheus, Grafana, ELK
- Windows: Active Directory, RDP, SMB
- CI/CD: Jenkins, GitLab
- Admin: cPanel, Webmin, Tomcat

### Complexity Distribution

- Low: 2 scenarios
- Medium: 9 scenarios
- High: 10 scenarios
- Very High: 4 scenarios

## 🚦 Success Indicators

Agent has learned successfully if:

- [ ] Uses nmap on infrastructure (S6-S13)
- [ ] Skips nmap on web-only (S1-S5)
- [ ] Chooses appropriate nmap mode on hybrid (quick vs thorough vs full)
- [ ] Investigates custom ports (S21, S24, S25)
- [ ] Mean reward >475 (>30% vs Phase 1A)
- [ ] Variance <150 (stable performance)
- [ ] TensorBoard shows entropy >-0.5 (still exploring)

## 🔄 Day 3 TODO

1. Create `generate_scenarios_phase1b.py`
2. Implement pre-computation for:
   - Subfinder results (subdomain lists)
   - HTTPX results (live endpoints, technologies)
   - Nmap results (ports, services, versions)
3. Generate 20 training scenarios (S1-S20)
4. Generate 5 test scenarios (S21-S25)
5. Validate:
   - Port diversity ≥15 patterns ✓
   - Technology diversity ✓
   - Reward range 420-920 ✓
   - No duplicate scenarios ✓
6. Save as JSON:
   - `phase1b_train.json` (20 scenarios)
   - `phase1b_test.json` (5 scenarios)

**Estimated Time**: 6 hours (Day 3)

---

**Status**: ✅ **SCENARIO DESIGN COMPLETE!**

**Next**: Day 3 - Generate scenarios with full tool results
