from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Application settings - centralized configuration
    All hardcoded values should be moved here
    """

    # =========================================================================
    # API Configuration
    # =========================================================================
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "AI Pentest Agent"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development, staging, production

    # =========================================================================
    # Database Configuration
    # =========================================================================
    DATABASE_URL: str = "sqlite:///./pentest.db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30  # seconds

    # =========================================================================
    # CORS Configuration
    # =========================================================================
    CORS_ORIGINS: str = "http://localhost:3000"

    # =========================================================================
    # Logging Configuration
    # =========================================================================
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_ROTATION: str = "100 MB"
    LOG_RETENTION: str = "30 days"
    LOG_FORMAT: str = "json"  # json or text

    # =========================================================================
    # Tools Configuration
    # =========================================================================
    USE_MOCK_TOOLS: bool = False  # DISABLED: Use real tools that are installed
    MOCK_SCAN_DELAY: int = 2
    
    # Tool Timeouts (seconds)
    NMAP_TIMEOUT: int = 300      # 5 minutes
    NUCLEI_TIMEOUT: int = 600    # 10 minutes
    WHATWEB_TIMEOUT: int = 120   # 2 minutes
    SSLSCAN_TIMEOUT: int = 120   # 2 minutes
    DEFAULT_TOOL_TIMEOUT: int = 300  # 5 minutes

    # =========================================================================
    # AI Configuration
    # =========================================================================
    USE_SAFE_AI_MODE: bool = True
    
    # Ollama Configuration (Primary AI Provider)
    # URL for Ollama service (GitHub Codespaces or local)
    OLLAMA_URL: str = "https://zany-acorn-v6jqg9w5qw4w3r4w-11434.app.github.dev"
    
    # Model selection - Qwen 2.5 14B for strategic reasoning
    OLLAMA_MODEL: str = "qwen2.5:14b"
    
    # Request timeout in seconds (10-120 recommended)
    OLLAMA_TIMEOUT: int = 30
    
    # Enable/disable AI integration globally
    ENABLE_AI_INTEGRATION: bool = True
    
    # Intelligence Router Thresholds
    # Subdomain count threshold for strategic planning
    QWEN_TRIGGER_SUBDOMAIN_COUNT: int = 100
    
    # Finding count threshold for AI prioritization
    QWEN_TRIGGER_FINDING_COUNT: int = 20
    
    # Enable response caching
    ENABLE_RESPONSE_CACHE: bool = True
    
    # Gemini API (Legacy/Fallback)
    GEMINI_API_TIMEOUT: int = 30  # seconds
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_RETRY_BASE_DELAY: float = 1.0
    GEMINI_RETRY_MAX_DELAY: float = 30.0
    
    # Gemini Models
    GEMINI_FLASH_MODEL: str = "gemini-2.5-flash"
    GEMINI_PRO_MODEL: str = "gemini-2.5-pro"
    
    # Gemini Pricing (USD per 1M tokens)
    GEMINI_FLASH_INPUT_PRICE: float = 0.075
    GEMINI_FLASH_OUTPUT_PRICE: float = 0.30
    GEMINI_PRO_INPUT_PRICE: float = 1.25
    GEMINI_PRO_OUTPUT_PRICE: float = 5.00
    
    # Agent Configuration
    MAX_AGENT_ITERATIONS: int = 10
    AGENT_ITERATION_TIMEOUT: int = 600  # 10 minutes per iteration

    # =========================================================================
    # Resilience Configuration
    # =========================================================================
    # Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD: int = 2
    CIRCUIT_BREAKER_TIMEOUT: int = 60  # seconds
    
    # Retry Configuration
    DEFAULT_MAX_RETRIES: int = 3
    DEFAULT_RETRY_BASE_DELAY: float = 1.0
    DEFAULT_RETRY_MAX_DELAY: float = 30.0
    
    # Timeouts
    DATABASE_QUERY_TIMEOUT: int = 5
    HTTP_REQUEST_TIMEOUT: int = 30
    SSE_POLLING_INTERVAL: float = 0.5  # seconds

    # =========================================================================
    # Security Configuration
    # =========================================================================
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Validation
    MAX_TARGET_LENGTH: int = 255
    MAX_USER_PROMPT_LENGTH: int = 5000
    
    # Blacklisted IPs/Networks
    BLACKLIST_INTERNAL_IPS: bool = True
    INTERNAL_IP_PATTERNS: List[str] = [
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "localhost"
    ]

    # =========================================================================
    # Monitoring Configuration
    # =========================================================================
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_ENABLED: bool = True
    HEALTH_CHECK_TIMEOUT: int = 5  # seconds for each check

    # =========================================================================
    # Performance Configuration
    # =========================================================================
    # Concurrency Limits
    MAX_CONCURRENT_SCANS: int = 5
    MAX_CONCURRENT_TOOL_EXECUTIONS: int = 3
    MAX_CONCURRENT_API_CALLS: int = 10
    
    # Caching (In-Memory)
    CACHE_ENABLED: bool = True  # Enable in-memory caching
    CACHE_TTL: int = 3600  # Default TTL: 1 hour
    CACHE_MAX_SIZE: int = 1000  # Max items in cache
    
    # Cache TTL for specific operations (seconds)
    CACHE_SCAN_RESULTS_TTL: int = 300  # 5 minutes
    CACHE_AI_ANALYSIS_TTL: int = 3600  # 1 hour
    CACHE_TOOL_OUTPUT_TTL: int = 600  # 10 minutes

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == "development"


settings = Settings()
