#!/bin/bash

###############################################################################
# Ollama Startup Script for GitHub Codespaces
#
# Purpose: Ensure Ollama service running and healthy before Agent-P starts
# Features:
#   - Detects current Ollama state (running/stopped/zombie)
#   - Auto-starts if not running
#   - Verifies Qwen model accessible
#   - Confirms public URL working
#   - Clear error messages with troubleshooting steps
#   - Fast execution (target < 30 seconds)
#
# Usage: ./startup_ollama.sh [--verbose|--quiet]
###############################################################################

set -e  # Exit on error

# Configuration
OLLAMA_URL="https://zany-acorn-v6jqg9w5qw4w3r4w-11434.app.github.dev"
LOCAL_URL="http://localhost:11434"
MODEL_NAME="qwen2.5:14b"
LOG_DIR="$HOME/.ollama/logs"
LOG_FILE="$LOG_DIR/ollama-$(date +%Y%m%d-%H%M%S).log"
MAX_WAIT_ATTEMPTS=15
POLL_INTERVAL=2

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Verbosity level (default: normal)
VERBOSE=false
QUIET=false

# Parse command line arguments
for arg in "$@"; do
    case $arg in
        --verbose|-v)
            VERBOSE=true
            ;;
        --quiet|-q)
            QUIET=true
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v    Show detailed progress"
            echo "  --quiet, -q      Show only errors and final status"
            echo "  --help, -h       Show this help message"
            exit 0
            ;;
    esac
done

###############################################################################
# Helper Functions
###############################################################################

log_info() {
    if [ "$QUIET" = false ]; then
        echo -e "${CYAN}ℹ ${NC}$1"
    fi
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_debug() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}  →${NC} $1"
    fi
}

show_header() {
    if [ "$QUIET" = false ]; then
        echo ""
        echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
        echo -e "${CYAN}║${NC}  Ollama Startup - Agent-P Integration  ${CYAN}║${NC}"
        echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
        echo ""
    fi
}

show_elapsed_time() {
    local start_time=$1
    local end_time=$(date +%s)
    local elapsed=$((end_time - start_time))
    log_debug "Time: ${elapsed}s"
}

###############################################################################
# Step 1: Detect Current State
###############################################################################

detect_ollama_state() {
    log_info "Step 1/7: Detecting Ollama state..."
    
    # Check if process running
    if pgrep -x "ollama" > /dev/null; then
        log_debug "Process found, checking responsiveness..."
        
        # Test if responding
        if curl -s --max-time 3 "$LOCAL_URL/api/version" > /dev/null 2>&1; then
            log_success "Ollama already running and healthy"
            return 0  # Already running
        else
            log_warning "Ollama process exists but not responding (zombie)"
            return 1  # Zombie process
        fi
    else
        log_info "Ollama not running"
        return 2  # Not running
    fi
}

###############################################################################
# Step 2: Clean Previous State
###############################################################################

cleanup_zombie() {
    log_info "Step 2/7: Cleaning up zombie process..."
    
    local pid=$(pgrep -x "ollama")
    if [ -n "$pid" ]; then
        log_debug "Sending SIGTERM to PID $pid..."
        kill -TERM "$pid" 2>/dev/null || true
        
        # Wait for graceful shutdown
        sleep 3
        
        # Force kill if still running
        if pgrep -x "ollama" > /dev/null; then
            log_debug "Forcing kill..."
            kill -KILL "$pid" 2>/dev/null || true
            sleep 1
        fi
        
        log_success "Zombie process cleaned"
    fi
    
    # Clean up large log files (> 100MB)
    if [ -d "$LOG_DIR" ]; then
        find "$LOG_DIR" -name "*.log" -size +100M -delete 2>/dev/null || true
    fi
}

###############################################################################
# Step 3: Start Ollama Service
###############################################################################

start_ollama() {
    log_info "Step 3/7: Starting Ollama service..."
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    
    # Start Ollama in background
    log_debug "Launching ollama serve..."
    nohup ollama serve > "$LOG_FILE" 2>&1 &
    local ollama_pid=$!
    
    sleep 2
    
    # Verify process started
    if ps -p $ollama_pid > /dev/null 2>&1; then
        log_success "Ollama process started (PID: $ollama_pid)"
        log_debug "Logs: $LOG_FILE"
        return 0
    else
        log_error "Failed to start Ollama process"
        log_error "Check logs: $LOG_FILE"
        
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo "Last 20 lines of log:"
            tail -n 20 "$LOG_FILE"
        fi
        
        exit 1
    fi
}

###############################################################################
# Step 4: Wait for Ready State
###############################################################################

wait_for_ready() {
    log_info "Step 4/7: Waiting for service ready..."
    
    local attempt=1
    local backoff=1
    
    while [ $attempt -le $MAX_WAIT_ATTEMPTS ]; do
        log_debug "Attempt $attempt/$MAX_WAIT_ATTEMPTS (backoff: ${backoff}s)..."
        
        if curl -s --max-time 3 "$LOCAL_URL/api/version" > /dev/null 2>&1; then
            log_success "Ollama service ready!"
            return 0
        fi
        
        sleep $backoff
        attempt=$((attempt + 1))
        
        # Exponential backoff (1s → 2s → 4s → 8s max)
        backoff=$((backoff * 2))
        if [ $backoff -gt 8 ]; then
            backoff=8
        fi
    done
    
    log_error "Service failed to become ready after ${MAX_WAIT_ATTEMPTS} attempts"
    log_error "Timeout waiting for Ollama service"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check logs: tail -f $LOG_FILE"
    echo "2. Verify disk space: df -h"
    echo "3. Check memory: free -h"
    echo "4. Manual test: curl $LOCAL_URL/api/version"
    echo "5. Restart Codespace if persistent"
    exit 1
}

###############################################################################
# Step 5: Verify Model Accessibility
###############################################################################

test_model() {
    log_info "Step 5/7: Testing model accessibility..."
    
    local start_time=$(date +%s)
    
    # Test inference with simple prompt
    local response=$(curl -s --max-time 10 "$LOCAL_URL/api/generate" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$MODEL_NAME\",\"prompt\":\"Respond with OK\",\"stream\":false}" \
        2>/dev/null)
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if echo "$response" | grep -q "response"; then
        log_success "Model responding correctly (${duration}s)"
        log_debug "Model: $MODEL_NAME"
        return 0
    else
        log_warning "Model test failed (may still work for real requests)"
        log_debug "Response: $response"
        
        echo ""
        echo "Model test failed, but continuing..."
        echo "Manual test: curl -X POST $LOCAL_URL/api/generate \\"
        echo "  -H 'Content-Type: application/json' \\"
        echo "  -d '{\"model\":\"$MODEL_NAME\",\"prompt\":\"Test\",\"stream\":false}'"
        return 1
    fi
}

###############################################################################
# Step 6: Display Status Summary
###############################################################################

show_status() {
    log_info "Step 6/7: Service status..."
    
    local pid=$(pgrep -x "ollama")
    
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}                    Ollama Status                        ${CYAN}║${NC}"
    echo -e "${CYAN}╠═══════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC} Service:      ${GREEN}Running${NC} (PID: $pid)"
    echo -e "${CYAN}║${NC} Model:        ${GREEN}$MODEL_NAME${NC}"
    echo -e "${CYAN}║${NC} Public URL:   ${YELLOW}$OLLAMA_URL${NC}"
    echo -e "${CYAN}║${NC} Local URL:    ${YELLOW}$LOCAL_URL${NC}"
    echo -e "${CYAN}║${NC} Logs:         $LOG_FILE"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo "Quick test command:"
    echo -e "${YELLOW}curl $LOCAL_URL/api/version${NC}"
    echo ""
}

###############################################################################
# Step 7: Health Check Public URL
###############################################################################

health_check() {
    log_info "Step 7/7: Health check public URL..."
    
    # Test public URL
    if curl -s --max-time 5 "$OLLAMA_URL/api/version" > /dev/null 2>&1; then
        log_success "Public URL accessible"
        return 0
    else
        log_warning "Public URL unreachable (local access still works)"
        echo ""
        echo "External access may not be working:"
        echo "1. Verify local access works: curl $LOCAL_URL/api/version"
        echo "2. Check Codespace port forwarding status"
        echo "3. Ensure port 11434 visibility set to Public"
        echo "4. Alternative: Use local URL within Codespace"
        return 1
    fi
}

###############################################################################
# Main Execution Flow
###############################################################################

main() {
    local script_start=$(date +%s)
    
    show_header
    
    # Step 1: Detect state
    detect_ollama_state
    local state=$?
    
    case $state in
        0)
            # Already running
            log_info "Skipping steps 2-4 (already running)"
            ;;
        1)
            # Zombie process
            cleanup_zombie
            start_ollama
            wait_for_ready
            ;;
        2)
            # Not running
            log_info "Skipping step 2 (no zombie process)"
            start_ollama
            wait_for_ready
            ;;
    esac
    
    # Step 5: Test model
    test_model || true  # Don't fail on model test
    
    # Step 6: Show status
    show_status
    
    # Step 7: Health check
    health_check || true  # Don't fail on public URL check
    
    # Final summary
    local script_end=$(date +%s)
    local total_time=$((script_end - script_start))
    
    echo ""
    log_success "Ollama startup complete! (Total time: ${total_time}s)"
    
    if [ $total_time -gt 60 ]; then
        log_warning "Startup took longer than expected (>${total_time}s)"
    fi
    
    echo ""
}

# Run main function
main "$@"
