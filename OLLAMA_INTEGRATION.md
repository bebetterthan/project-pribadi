# Agent-P x Ollama Integration Guide

## 🎯 Overview

This integration connects Agent-P penetration testing platform with Qwen 2.5 14B running on Ollama, adding intelligent strategic reasoning to security assessments. The AI integration is **completely optional** - Agent-P works normally without it, but becomes smarter when AI is available.

## 🏗️ Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────────────────────┐
│                    Agent-P Workflows                    │
│  (Scan Planning → Tool Execution → Vulnerability        │
│   Prioritization → Report Generation)                   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Intelligence Router                        │
│  • Analyzes query complexity                           │
│  • Routes: Strategic AI vs Tactical Logic              │
│  • Handles fallbacks gracefully                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Ollama Provider                            │
│  • HTTP communication with Ollama API                  │
│  • Timeout & retry handling                            │
│  • Response caching                                    │
│  • Error recovery                                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│         Ollama Service (GitHub Codespaces)             │
│  • Qwen 2.5 14B model                                  │
│  • Port 11434                                          │
│  • Public HTTPS URL                                    │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Start Ollama Service (GitHub Codespaces)

```bash
# Make script executable
chmod +x startup_ollama.sh

# Run startup script
./startup_ollama.sh
```

Expected output:
```
╔══════════════════════════════════════════╗
║  Ollama Startup - Agent-P Integration  ║
╚══════════════════════════════════════════╝

✓ Ollama already running and healthy
✓ Model responding correctly (2.3s)
✓ Public URL accessible

🚀 Ollama startup complete! (Total time: 5s)
```

### 2. Configure Environment

```bash
# Copy template
cp .env.template .env

# Edit configuration (optional - defaults work for Codespaces)
nano .env
```

Key settings:
```bash
# AI Integration Control
ENABLE_AI_INTEGRATION=true

# Ollama Configuration
OLLAMA_URL=https://zany-acorn-v6jqg9w5qw4w3r4w-11434.app.github.dev
OLLAMA_MODEL=qwen2.5:14b
OLLAMA_TIMEOUT=30

# Intelligence Router Thresholds
QWEN_TRIGGER_SUBDOMAIN_COUNT=100  # When to use strategic planning
QWEN_TRIGGER_FINDING_COUNT=20     # When to use AI prioritization
```

### 3. Install Dependencies

```bash
cd backend
.venv/Scripts/activate  # Windows
# or: source .venv/bin/activate  # Linux/Mac

pip install httpx tenacity
```

### 4. Test Integration

```powershell
# Run comprehensive test suite
.\test_ollama_integration.ps1
```

Expected results:
```
🧪 Testing Agent-P x Ollama Integration...

✓ Ollama service: ONLINE
✓ Model inference: WORKING (2.5s)
✓ Python environment: READY
✓ OllamaProvider: WORKING
✓ IntelligenceRouter: WORKING
✓ AIIntegrationHelper: WORKING

🎉 All Integration Tests Passed!
```

### 5. Start Agent-P

```bash
# Terminal 1: Backend
cd backend
.venv/Scripts/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open: http://localhost:3000

## 📋 Integration Points

### 1. Scan Planning (Reconnaissance Phase)

**When triggered:**
- Subdomain count ≥ 100
- Target complexity = "high"
- Query contains strategic keywords: "plan", "strategy", "comprehensive"

**What it does:**
```python
from backend.app.services.ai_integration import get_ai_helper

# After reconnaissance
recon_data = {
    "subdomain_count": 150,
    "technology_stack": ["nginx", "php", "mysql"],
    "open_ports": [80, 443, 8080],
    "complexity": "high"
}

helper = get_ai_helper()
strategy = await helper.get_scan_strategy(
    target="example.com",
    reconnaissance_data=recon_data,
    time_budget=3600
)

if strategy:
    # Use AI-recommended testing phases
    print(strategy["strategy"])
    # "Phase 1: Focus on web application scanning..."
    # "Phase 2: Enumerate database services on port 3306..."
```

**Fallback:** If AI unavailable, continues with default scan phases.

### 2. Vulnerability Prioritization

**When triggered:**
- Finding count ≥ 20
- Query contains: "prioritize", "risk", "business impact"

**What it does:**
```python
findings = [
    {"title": "SQL Injection", "severity": "critical", "location": "login"},
    {"title": "XSS", "severity": "medium", "location": "search"},
    # ... 20+ more findings
]

target_context = {
    "industry": "banking",
    "data_sensitivity": "high"
}

prioritized = await helper.prioritize_findings(
    findings=findings,
    target_context=target_context
)

if prioritized:
    # Findings now include AI prioritization
    for finding in prioritized:
        print(finding["_ai_prioritization"])
    # "Priority 1: SQL Injection - Critical business risk..."
```

**Fallback:** If AI unavailable, uses severity-based sorting.

### 3. Executive Report Generation

**When triggered:**
- Always for report generation phase
- Scan complete with findings

**What it does:**
```python
scan_results = {
    "total_findings": 15,
    "critical": 3,
    "high": 5,
    "medium": 7,
    "key_findings": [...]
}

target_info = {
    "name": "Banking Application",
    "industry": "Finance"
}

summary = await helper.generate_executive_summary(
    scan_results=scan_results,
    target_info=target_info
)

if summary:
    # Business-focused summary for executives
    print(summary)
    # "Executive Summary:
    #  The security assessment identified significant risks...
    #  Immediate actions: 1) Patch SQL injection..."
```

**Fallback:** If AI unavailable, uses standard technical report.

## 🔧 Configuration Details

### Ollama Provider Settings

```python
# backend/app/services/ollama_provider.py

OLLAMA_URL: str
  # Default: Codespaces public URL
  # Purpose: Base URL for Ollama API
  # Example: "https://zany-acorn-v6jqg9w5qw4w3r4w-11434.app.github.dev"

OLLAMA_MODEL: str
  # Default: "qwen2.5:14b"
  # Purpose: Model identifier
  # Alternatives: "qwen2.5:7b" (faster), "qwen2.5:1.5b" (lightweight)

OLLAMA_TIMEOUT: int
  # Default: 30 seconds
  # Range: 10-120 seconds
  # Lower = faster failures, Higher = wait for complex analysis
```

### Intelligence Router Thresholds

```python
# backend/app/services/intelligence_router.py

QWEN_TRIGGER_SUBDOMAIN_COUNT: int
  # Default: 100
  # Purpose: When subdomain count ≥ this, trigger strategic planning
  # Adjust: Lower = more AI usage, Higher = less AI usage

QWEN_TRIGGER_FINDING_COUNT: int
  # Default: 20
  # Purpose: When findings ≥ this, trigger AI prioritization
  # Adjust: Based on typical scan results

ENABLE_RESPONSE_CACHE: bool
  # Default: true
  # Purpose: Cache responses to avoid redundant queries
  # Memory: ~1MB per 100 cached responses
```

## 🧪 Testing

### Unit Tests

```bash
cd backend

# Test Ollama Provider
pytest tests/test_ollama_provider.py -v

# Test Intelligence Router
pytest tests/test_intelligence_router.py -v

# Test AI Integration
pytest tests/test_ai_integration.py -v
```

### Integration Tests

```bash
# Run all tests
pytest tests/ -v --cov=app/services

# Expected coverage: >80% for AI modules
```

### Manual Testing

```python
# Test Ollama connection
curl https://zany-acorn-v6jqg9w5qw4w3r4w-11434.app.github.dev/api/version

# Test model inference
curl -X POST https://zany-acorn-v6jqg9w5qw4w3r4w-11434.app.github.dev/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:14b","prompt":"Test","stream":false}'
```

## 🐛 Troubleshooting

### Issue: Ollama service not responding

**Symptoms:**
```
✗ Ollama service: OFFLINE
Error: Connection refused
```

**Solutions:**
1. Check if Ollama running: `pgrep ollama`
2. Start service: `./startup_ollama.sh`
3. Check logs: `tail -f ~/.ollama/logs/ollama-*.log`
4. Verify port forwarding in Codespaces (port 11434, visibility: Public)

### Issue: Model test fails

**Symptoms:**
```
⚠ Model test failed (may still work for real requests)
```

**Solutions:**
1. Verify model downloaded: `ollama list`
2. Test manually: `ollama run qwen2.5:14b "Test"`
3. Check disk space: `df -h`
4. Pull model if missing: `ollama pull qwen2.5:14b`

### Issue: Strategic analysis not triggering

**Symptoms:**
- High complexity targets use tactical logic
- No AI responses in logs

**Solutions:**
1. Check thresholds: `echo $QWEN_TRIGGER_SUBDOMAIN_COUNT`
2. Lower thresholds in `.env`: `QWEN_TRIGGER_SUBDOMAIN_COUNT=50`
3. Force strategic: Pass `force_strategic=True` in code
4. Check routing logs: `tail -f backend/logs/app.log | grep "Routing"`

### Issue: Timeout errors

**Symptoms:**
```
Request timed out after 30.0s
```

**Solutions:**
1. Increase timeout: `OLLAMA_TIMEOUT=60` in `.env`
2. Check model performance: Run simple inference test
3. Verify Codespaces resources: Check CPU/memory usage
4. Use smaller model: `OLLAMA_MODEL=qwen2.5:7b`

### Issue: Public URL unreachable

**Symptoms:**
```
⚠ Public URL unreachable (local access still works)
```

**Solutions:**
1. Check port visibility in Codespaces UI
2. Use local URL for testing: `OLLAMA_URL=http://localhost:11434`
3. Restart port forwarding in Codespaces
4. Verify URL matches Codespaces assigned URL

## 📊 Performance Tuning

### Response Times

| Operation | Expected Time | Optimization |
|-----------|--------------|--------------|
| Simple query | < 3s | Use cache |
| Strategic analysis | < 15s | Adjust timeout |
| Vulnerability prioritization | < 10s | Limit finding count |
| Executive summary | < 20s | Summarize key findings |

### Resource Usage

| Component | Memory | CPU | Optimization |
|-----------|--------|-----|--------------|
| OllamaProvider | ~10MB | Low | Enable caching |
| IntelligenceRouter | ~5MB | Low | Adjust thresholds |
| Ollama Service | ~8GB | High | Use smaller model |
| Total overhead | ~15MB | Low | Minimal when idle |

### Optimization Strategies

**1. Reduce AI Usage**
```bash
# Increase thresholds
QWEN_TRIGGER_SUBDOMAIN_COUNT=200
QWEN_TRIGGER_FINDING_COUNT=50
```

**2. Faster Responses**
```bash
# Use smaller model
OLLAMA_MODEL=qwen2.5:7b

# Reduce timeout
OLLAMA_TIMEOUT=20
```

**3. Better Caching**
```bash
# Enable cache with longer TTL
ENABLE_RESPONSE_CACHE=true
CACHE_TTL=7200  # 2 hours
```

## 🔒 Security Considerations

### API Key Management
- Ollama runs locally, no API keys needed
- Never log prompts containing sensitive data
- Sanitize user input before sending to AI

### Data Privacy
- All AI processing happens in Codespaces (not sent to cloud)
- No scan data leaves your environment
- Qwen model runs locally on Ollama

### Input Validation
```python
# AI integration sanitizes input automatically
# Max prompt length: 5000 characters
# Context limited to scan metadata only
```

## 📚 API Reference

### OllamaProvider

```python
from backend.app.services.ollama_provider import OllamaProvider

provider = OllamaProvider(
    url="https://...",  # Optional: Override URL
    model="qwen2.5:14b",  # Optional: Override model
    timeout=30  # Optional: Override timeout
)

# Generate response
response = await provider.generate(
    prompt="Analyze vulnerability",
    context={"severity": "high"},  # Optional
    system_prompt="You are a security expert",  # Optional
    force_no_cache=False  # Optional
)

# Check response
if response.success:
    print(response.response)  # AI response text
    print(response.duration_seconds)  # Time taken
    print(response.tokens)  # Token count
else:
    print(response.error)  # Error message
```

### IntelligenceRouter

```python
from backend.app.services.intelligence_router import (
    IntelligenceRouter,
    RoutingContext,
    RoutingDecision
)

router = IntelligenceRouter(
    ollama_provider=provider,
    subdomain_threshold=100,  # Optional
    finding_threshold=20  # Optional
)

# Route query
context = RoutingContext(
    subdomain_count=150,
    finding_count=25,
    target_complexity="high"
)

decision = router.route(
    query="Plan testing strategy",
    context=context,
    force_strategic=False  # Optional
)

if decision == RoutingDecision.USE_STRATEGIC:
    response = await router.get_strategic_response(query, context)
```

### AIIntegrationHelper

```python
from backend.app.services.ai_integration import get_ai_helper

helper = get_ai_helper()

# Scan planning
strategy = await helper.get_scan_strategy(
    target="example.com",
    reconnaissance_data={...},
    time_budget=3600
)

# Vulnerability prioritization
prioritized = await helper.prioritize_findings(
    findings=[...],
    target_context={...}
)

# Report generation
summary = await helper.generate_executive_summary(
    scan_results={...},
    target_info={...}
)
```

## 🎓 Best Practices

1. **Always check AI availability** - Use fallbacks
2. **Log AI decisions** - Track when/how AI used
3. **Monitor performance** - Watch response times
4. **Adjust thresholds** - Based on your use case
5. **Cache responses** - Avoid redundant queries
6. **Handle failures gracefully** - Never crash on AI errors
7. **Test without AI** - Ensure Agent-P works standalone
8. **Document AI insights** - Note in reports when AI used

## 📝 License

Apache 2.0 - See LICENSE file

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md

## 📮 Support

- Issues: GitHub Issues
- Docs: This README
- Logs: `backend/logs/app.log`
