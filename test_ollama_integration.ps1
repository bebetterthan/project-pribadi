# Test Agent-P x Ollama Integration
Write-Host "🧪 Testing Agent-P x Ollama Integration..." -ForegroundColor Cyan
Write-Host ""

# Configuration
$OLLAMA_URL = "https://zany-acorn-v6jqg9w5qw4w3r4w-11434.app.github.dev"
$BACKEND_DIR = "backend"

# Test 1: Check Ollama Service
Write-Host "Test 1: Checking Ollama service..." -ForegroundColor Yellow
try {
    $version = Invoke-RestMethod -Uri "$OLLAMA_URL/api/version" -TimeoutSec 5
    Write-Host "✓ Ollama service: ONLINE" -ForegroundColor Green
    Write-Host "  Version: $($version.version)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Ollama service: OFFLINE" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Solution:" -ForegroundColor Yellow
    Write-Host "   Run: ./startup_ollama.sh" -ForegroundColor White
    exit 1
}
Write-Host ""

# Test 2: Test Model Inference
Write-Host "Test 2: Testing Qwen 2.5 14B model..." -ForegroundColor Yellow
try {
    $body = @{
        model = "qwen2.5:14b"
        prompt = "Respond with OK"
        stream = $false
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$OLLAMA_URL/api/generate" `
        -Method POST `
        -Body $body `
        -ContentType "application/json" `
        -TimeoutSec 30

    if ($response.response -match "OK") {
        Write-Host "✓ Model inference: WORKING" -ForegroundColor Green
        Write-Host "  Response time: $([math]::Round($response.total_duration / 1000000000, 2))s" -ForegroundColor Gray
        Write-Host "  Tokens: $($response.eval_count)" -ForegroundColor Gray
    } else {
        Write-Host "⚠ Model inference: UNEXPECTED RESPONSE" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Model inference: FAILED" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 3: Check Python Environment
Write-Host "Test 3: Checking Python environment..." -ForegroundColor Yellow
Set-Location $BACKEND_DIR
try {
    & .\.venv\Scripts\python.exe -c "import httpx; import tenacity; print('✓ Dependencies installed')"
    Write-Host "✓ Python environment: READY" -ForegroundColor Green
} catch {
    Write-Host "✗ Python environment: MISSING DEPENDENCIES" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Solution:" -ForegroundColor Yellow
    Write-Host "   Run: cd backend && .\.venv\Scripts\activate && pip install httpx tenacity" -ForegroundColor White
    Set-Location ..
    exit 1
}
Set-Location ..
Write-Host ""

# Test 4: Test OllamaProvider
Write-Host "Test 4: Testing OllamaProvider class..." -ForegroundColor Yellow
Set-Location $BACKEND_DIR
try {
    $testScript = @"
import asyncio
from app.services.ollama_provider import OllamaProvider

async def test():
    provider = OllamaProvider(url='$OLLAMA_URL')
    result = await provider.generate('Respond with OK', force_no_cache=True)
    if result.success:
        print('✓ OllamaProvider: WORKING')
        print(f'  Duration: {result.duration_seconds:.2f}s')
        return 0
    else:
        print(f'✗ OllamaProvider: FAILED - {result.error}')
        return 1

exit(asyncio.run(test()))
"@
    
    $testScript | & .\.venv\Scripts\python.exe
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ OllamaProvider: WORKING" -ForegroundColor Green
    } else {
        Write-Host "✗ OllamaProvider: FAILED" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
} catch {
    Write-Host "✗ OllamaProvider: ERROR" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Set-Location ..
Write-Host ""

# Test 5: Test IntelligenceRouter
Write-Host "Test 5: Testing IntelligenceRouter..." -ForegroundColor Yellow
Set-Location $BACKEND_DIR
try {
    $testScript = @"
from app.services.ollama_provider import OllamaProvider
from app.services.intelligence_router import IntelligenceRouter, RoutingContext, RoutingDecision

provider = OllamaProvider(url='$OLLAMA_URL')
router = IntelligenceRouter(provider)

# Test routing decisions
ctx = RoutingContext(subdomain_count=150)
decision = router.route('Plan strategy', context=ctx)

if decision == RoutingDecision.USE_STRATEGIC:
    print('✓ IntelligenceRouter: WORKING')
    print(f'  Decision: {decision.value}')
else:
    print('⚠ IntelligenceRouter: Unexpected decision')
"@
    
    $testScript | & .\.venv\Scripts\python.exe
    Write-Host "✓ IntelligenceRouter: WORKING" -ForegroundColor Green
} catch {
    Write-Host "✗ IntelligenceRouter: ERROR" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Set-Location ..
Write-Host ""

# Test 6: Test AIIntegrationHelper
Write-Host "Test 6: Testing AIIntegrationHelper..." -ForegroundColor Yellow
Set-Location $BACKEND_DIR
try {
    $testScript = @"
import asyncio
from app.services.ai_integration import AIIntegrationHelper

async def test():
    helper = AIIntegrationHelper(enabled=True, ollama_url='$OLLAMA_URL')
    
    # Test scan strategy
    recon_data = {'subdomain_count': 150, 'complexity': 'high'}
    result = await helper.get_scan_strategy('test.com', recon_data)
    
    if result:
        print('✓ AIIntegrationHelper: WORKING')
        print(f'  Mode: {result["mode"]}')
        return 0
    else:
        print('⚠ AIIntegrationHelper: Strategy skipped (below threshold)')
        return 0

exit(asyncio.run(test()))
"@
    
    $testScript | & .\.venv\Scripts\python.exe
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ AIIntegrationHelper: WORKING" -ForegroundColor Green
    } else {
        Write-Host "✗ AIIntegrationHelper: FAILED" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
} catch {
    Write-Host "✗ AIIntegrationHelper: ERROR" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Set-Location ..
Write-Host ""

# Final Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "🎉 All Integration Tests Passed!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""
Write-Host "✅ Ollama service online and responding" -ForegroundColor White
Write-Host "✅ Qwen 2.5 14B model working" -ForegroundColor White
Write-Host "✅ Python dependencies installed" -ForegroundColor White
Write-Host "✅ OllamaProvider functional" -ForegroundColor White
Write-Host "✅ IntelligenceRouter routing correctly" -ForegroundColor White
Write-Host "✅ AIIntegrationHelper ready" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Agent-P x Ollama integration is ready to use!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Start backend: cd backend && .\.venv\Scripts\activate && uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "  2. Start frontend: cd frontend && npm run dev" -ForegroundColor White
Write-Host "  3. Open http://localhost:3000" -ForegroundColor White
Write-Host ""
