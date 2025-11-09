# Test Qwen 2.5 14B Model on GitHub Codespaces
Write-Host "🤖 Testing Qwen 2.5 14B Model..." -ForegroundColor Cyan
Write-Host ""

$body = @{
    model = "qwen2.5:14b"
    prompt = "Found SQL injection in banking app login form. Give 3 immediate actions considering: 1) Production environment 2) PCI-DSS compliance 3) Customer data at risk. Be concise."
    stream = $false
} | ConvertTo-Json

try {
    Write-Host "📡 Sending request to Codespaces..." -ForegroundColor Yellow
    
    $response = Invoke-RestMethod -Uri "https://zany-acorn-v6jqg9w5qw4w3r4w-11434.app.github.dev/api/generate" `
        -Method POST `
        -Body $body `
        -ContentType "application/json" `
        -TimeoutSec 120
    
    Write-Host ""
    Write-Host "✅ Response received!" -ForegroundColor Green
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "Qwen 2.5 14B Response:" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host $response.response -ForegroundColor White
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "⏱️  Response time: $([math]::Round($response.total_duration / 1000000000, 2)) seconds" -ForegroundColor Gray
    Write-Host "🔢 Total tokens: $($response.eval_count)" -ForegroundColor Gray
    Write-Host "⚡ Tokens/sec: $([math]::Round($response.eval_count / ($response.eval_duration / 1000000000), 2))" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "❌ Error:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Pastikan:" -ForegroundColor Yellow
    Write-Host "   1. Codespaces masih running" -ForegroundColor White
    Write-Host "   2. Port 11434 sudah forwarded dengan visibility Public" -ForegroundColor White
    Write-Host "   3. Ollama service sudah running di Codespaces" -ForegroundColor White
    Write-Host ""
}
