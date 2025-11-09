"""
Scan Profile Models
Fase 3.5: Professional scan configuration presets
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum

class ProfileType(str, Enum):
    """Scan profile types"""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    CUSTOM = "custom"

@dataclass
class ToolConfig:
    """Configuration for a single tool"""
    flags: List[str]
    timeout: int  # seconds
    enabled: bool = True
    
@dataclass
class ScanProfile:
    """
    Complete scan profile configuration
    """
    name: str
    type: ProfileType
    description: str
    estimated_duration: int  # seconds
    tools: Dict[str, ToolConfig]
    
    # Metadata
    use_case: str
    target_audience: str
    
    def get_tool_config(self, tool_name: str) -> Optional[ToolConfig]:
        """Get configuration for specific tool"""
        return self.tools.get(tool_name)
    
    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if tool is enabled in this profile"""
        config = self.get_tool_config(tool_name)
        return config.enabled if config else False


# ============================================================================
# PREDEFINED PROFILES
# ============================================================================

QUICK_PROFILE = ScanProfile(
    name="Quick Scan",
    type=ProfileType.QUICK,
    description="Fast reconnaissance for initial assessment",
    estimated_duration=600,  # 10 minutes
    use_case="Quick check, demos, time-constrained scenarios",
    target_audience="All users",
    tools={
        "subfinder": ToolConfig(
            flags=["-timeout", "60"],
            timeout=60,
            enabled=True
        ),
        "httpx": ToolConfig(
            flags=["-timeout", "3"],
            timeout=30,
            enabled=True
        ),
        "nmap": ToolConfig(
            flags=["-T4", "-F", "--top-ports", "100"],
            timeout=180,
            enabled=True
        ),
        "whatweb": ToolConfig(
            flags=["-a", "1"],  # Stealthy
            timeout=30,
            enabled=False  # Skip for quick
        ),
        "ffuf": ToolConfig(
            flags=[],  # Use quick wordlist
            timeout=120,
            enabled=False  # Skip for quick
        ),
        "nuclei": ToolConfig(
            flags=["-s", "critical", "-tags", "cve,exposure", "-c", "50"],
            timeout=240,
            enabled=True
        ),
    }
)

STANDARD_PROFILE = ScanProfile(
    name="Standard Scan",
    type=ProfileType.STANDARD,
    description="Balanced scan for most use cases",
    estimated_duration=1800,  # 30 minutes
    use_case="Regular pentesting, balanced approach",
    target_audience="Security professionals, developers",
    tools={
        "subfinder": ToolConfig(
            flags=["-timeout", "180"],
            timeout=180,
            enabled=True
        ),
        "httpx": ToolConfig(
            flags=["-timeout", "5"],
            timeout=60,
            enabled=True
        ),
        "nmap": ToolConfig(
            flags=["-sV", "-T4", "-F"],
            timeout=600,
            enabled=True
        ),
        "whatweb": ToolConfig(
            flags=["-a", "3"],  # Aggressive
            timeout=60,
            enabled=True
        ),
        "ffuf": ToolConfig(
            flags=[],  # Use standard wordlist
            timeout=300,
            enabled=True
        ),
        "nuclei": ToolConfig(
            flags=["-s", "critical,high", "-c", "50"],
            timeout=600,
            enabled=True
        ),
    }
)

DEEP_PROFILE = ScanProfile(
    name="Deep Scan",
    type=ProfileType.DEEP,
    description="Comprehensive analysis, nothing missed",
    estimated_duration=7200,  # 2 hours
    use_case="Pre-production deployment, compliance audits",
    target_audience="Advanced security professionals",
    tools={
        "subfinder": ToolConfig(
            flags=["-timeout", "300", "-all"],
            timeout=300,
            enabled=True
        ),
        "httpx": ToolConfig(
            flags=["-timeout", "10"],
            timeout=120,
            enabled=True
        ),
        "nmap": ToolConfig(
            flags=["-sV", "--version-intensity", "9", "-O", "-sC", "-p-", "-T4"],
            timeout=3600,
            enabled=True
        ),
        "whatweb": ToolConfig(
            flags=["-a", "4"],  # Heavy
            timeout=120,
            enabled=True
        ),
        "ffuf": ToolConfig(
            flags=[],  # Use deep wordlist
            timeout=1800,
            enabled=True
        ),
        "nuclei": ToolConfig(
            flags=["-s", "critical,high,medium,low", "-c", "30"],
            timeout=1800,
            enabled=True
        ),
    }
)

# Profile registry
PROFILES: Dict[str, ScanProfile] = {
    ProfileType.QUICK: QUICK_PROFILE,
    ProfileType.STANDARD: STANDARD_PROFILE,
    ProfileType.DEEP: DEEP_PROFILE,
}


class ScanProfileManager:
    """Manager for scan profiles"""
    
    @staticmethod
    def get_profile(profile_type: str) -> ScanProfile:
        """
        Get scan profile by type
        
        Args:
            profile_type: Profile type (quick/standard/deep)
            
        Returns:
            ScanProfile instance
            
        Raises:
            ValueError: If profile not found
        """
        profile = PROFILES.get(profile_type)
        if not profile:
            raise ValueError(f"Unknown profile type: {profile_type}. Available: {list(PROFILES.keys())}")
        return profile
    
    @staticmethod
    def list_profiles() -> List[Dict[str, Any]]:
        """
        List all available profiles with metadata
        
        Returns:
            List of profile summaries
        """
        return [
            {
                "type": profile.type,
                "name": profile.name,
                "description": profile.description,
                "estimated_duration": profile.estimated_duration,
                "use_case": profile.use_case,
            }
            for profile in PROFILES.values()
        ]
    
    @staticmethod
    def get_tool_command_args(profile: ScanProfile, tool_name: str) -> List[str]:
        """
        Get command-line arguments for tool based on profile
        
        Args:
            profile: Scan profile
            tool_name: Tool name (e.g., 'nmap')
            
        Returns:
            List of command-line flags
        """
        config = profile.get_tool_config(tool_name)
        if not config:
            return []
        return config.flags
    
    @staticmethod
    def apply_profile_to_scan(profile: ScanProfile, scan_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply profile settings to scan configuration
        
        Args:
            profile: Scan profile to apply
            scan_config: Base scan configuration
            
        Returns:
            Updated scan configuration
        """
        scan_config["profile"] = profile.type
        scan_config["estimated_duration"] = profile.estimated_duration
        scan_config["tools_config"] = {
            tool_name: {
                "flags": config.flags,
                "timeout": config.timeout,
                "enabled": config.enabled
            }
            for tool_name, config in profile.tools.items()
        }
        return scan_config

