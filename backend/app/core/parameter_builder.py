"""
Intelligent Parameter Builder - Phase 1, Day 3
Dynamically constructs tool commands based on available scan context data
"""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import os
import tempfile
from pathlib import Path
from app.core.scan_context_manager import ScanContextManager
from app.models.scan_context import FindingType
from app.utils.logger import logger


class ToolParameterBuilder(ABC):
    """
    Base class for tool parameter builders.
    Each tool has its own builder that knows how to construct optimal parameters.
    """
    
    def __init__(self, scan_context_manager: ScanContextManager, scan_id: str, target: str):
        """
        Initialize parameter builder.
        
        Args:
            scan_context_manager: ScanContextManager instance
            scan_id: Scan identifier
            target: Original target (domain/IP)
        """
        self.context = scan_context_manager
        self.scan_id = scan_id
        self.target = target
        self.temp_dir = Path(tempfile.gettempdir()) / f"scan_{scan_id}"
        self.temp_dir.mkdir(exist_ok=True)
    
    @abstractmethod
    def build_parameters(self) -> Dict[str, Any]:
        """
        Build parameters for tool execution.
        
        Returns:
            Dictionary with:
            - 'target_hosts': List of hosts/URLs to scan
            - 'command_args': Additional command arguments
            - 'reasoning': Why these parameters were chosen
            - 'priority': Priority level (1-5)
        """
        pass
    
    def _write_targets_to_file(self, targets: List[str], filename: str) -> str:
        """
        Write target list to a file.
        
        Args:
            targets: List of targets
            filename: Filename for the target list
            
        Returns:
            Absolute path to created file
        """
        file_path = self.temp_dir / filename
        with open(file_path, 'w') as f:
            for target in targets:
                f.write(f"{target}\n")
        logger.debug(f"Wrote {len(targets)} targets to {file_path}")
        return str(file_path)
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {e}")


class SubfinderParameterBuilder(ToolParameterBuilder):
    """Parameter builder for Subfinder"""
    
    def build_parameters(self) -> Dict[str, Any]:
        """Build Subfinder parameters"""
        # Subfinder always runs on main domain
        return {
            'target_hosts': [self.target],
            'command_args': {
                'silent': True,
                'all': True  # Use all sources
            },
            'reasoning': f"Discovering subdomains for {self.target} using all passive sources",
            'priority': 1  # High priority - foundation tool
        }


class HttpxParameterBuilder(ToolParameterBuilder):
    """Parameter builder for HTTPX"""
    
    def build_parameters(self) -> Dict[str, Any]:
        """Build HTTPX parameters based on available subdomains"""
        # Check if subdomains exist
        subdomains = self.context.get_subdomains(self.scan_id)
        
        if subdomains and len(subdomains) > 0:
            # Prioritize interesting targets
            interesting = self.context.get_interesting_targets(self.scan_id, limit=100)
            
            if interesting and len(interesting) > 10:
                # Scan interesting first, then rest
                target_file = self._write_targets_to_file(interesting, 'httpx_priority_targets.txt')
                reasoning = f"Probing {len(interesting)} high-priority subdomains (admin, api, dev, etc.) from {len(subdomains)} total"
                priority = 2
            else:
                # Scan all subdomains
                target_file = self._write_targets_to_file(subdomains, 'httpx_all_targets.txt')
                reasoning = f"Probing all {len(subdomains)} discovered subdomains for HTTP services"
                priority = 2
            
            return {
                'target_file': target_file,
                'target_hosts': interesting if interesting else subdomains[:50],  # For placeholder substitution
                'command_args': {
                    'silent': True,
                    'status_code': True,
                    'title': True,
                    'tech_detect': True,
                    'follow_redirects': True,
                    'threads': 50
                },
                'reasoning': reasoning,
                'priority': priority
            }
        else:
            # No subdomains - fall back to main domain
            return {
                'target_hosts': [self.target],
                'command_args': {
                    'silent': True,
                    'status_code': True,
                    'title': True,
                    'tech_detect': True
                },
                'reasoning': f"No subdomains discovered, probing main domain {self.target}",
                'priority': 3  # Lower priority without subdomain data
            }


class NmapParameterBuilder(ToolParameterBuilder):
    """Parameter builder for Nmap"""
    
    def build_parameters(self) -> Dict[str, Any]:
        """Build Nmap parameters"""
        # Nmap can use subdomains if available
        subdomains = self.context.get_subdomains(self.scan_id)
        
        if subdomains and len(subdomains) > 0:
            # Select high-priority targets for port scanning
            interesting = self.context.get_interesting_targets(self.scan_id, limit=10)
            
            if interesting:
                targets = interesting[:5]  # Limit to 5 to avoid long scans
                reasoning = f"Port scanning {len(targets)} high-priority targets"
                priority = 2
            else:
                targets = [self.target]  # Just main domain
                reasoning = f"Port scanning main domain {self.target}"
                priority = 2
        else:
            targets = [self.target]
            reasoning = f"Port scanning main domain {self.target}"
            priority = 1
        
        return {
            'target_hosts': targets,
            'command_args': {
                'scan_profile': 'quick',  # Use quick profile
                'service_version': True,
                'os_detection': False,  # Skip OS detection for speed
                'timing': 4  # Aggressive timing
            },
            'reasoning': reasoning,
            'priority': priority
        }


class NucleiParameterBuilder(ToolParameterBuilder):
    """Parameter builder for Nuclei"""
    
    def build_parameters(self) -> Dict[str, Any]:
        """Build Nuclei parameters based on available HTTP services"""
        # Get active URLs from scan context
        urls = self.context.get_active_urls(self.scan_id)
        
        if not urls:
            logger.warning("Nuclei: No active URLs found in scan context")
            return {
                'target_hosts': [],
                'command_args': {},
                'reasoning': "No active URLs to scan - skipping",
                'priority': 0,
                'skip': True
            }
        
        # Check if we have technology information
        has_tech_info = self.context.has_findings(self.scan_id, FindingType.TECHNOLOGY)
        
        if has_tech_info:
            # Can optimize template selection based on detected technologies
            # TODO: Implement tech-based template selection
            template_categories = ['cves', 'vulnerabilities', 'exposures']
            reasoning = f"Scanning {len(urls)} active URLs with vulnerability templates"
        else:
            template_categories = ['cves', 'vulnerabilities']
            reasoning = f"Scanning {len(urls)} active URLs for known CVEs and common vulnerabilities"
        
        # Write URL list to file
        target_file = self._write_targets_to_file(urls, 'nuclei_targets.txt')
        
        return {
            'target_file': target_file,
            'target_hosts': urls[:50],  # For placeholder substitution
            'command_args': {
                'templates': template_categories,
                'severity': ['critical', 'high', 'medium'],
                'rate_limit': 150,
                'bulk_size': 25,
                'concurrency': 25
            },
            'reasoning': reasoning,
            'priority': 3
        }


class WhatwebParameterBuilder(ToolParameterBuilder):
    """Parameter builder for Whatweb"""
    
    def build_parameters(self) -> Dict[str, Any]:
        """Build Whatweb parameters"""
        # Get active URLs
        urls = self.context.get_active_urls(self.scan_id)
        
        if not urls:
            return {
                'target_hosts': [],
                'command_args': {},
                'reasoning': "No active URLs to fingerprint - skipping",
                'priority': 0,
                'skip': True
            }
        
        # Prioritize interesting URLs
        interesting = self.context.get_interesting_targets(self.scan_id, limit=50)
        active_interesting = [url for url in urls if any(target in url for target in interesting)] if interesting else urls
        
        targets = active_interesting[:30] if active_interesting else urls[:30]
        
        return {
            'target_hosts': targets,
            'command_args': {
                'aggression': 3,
                'verbose': True
            },
            'reasoning': f"Fingerprinting technologies on {len(targets)} active URLs",
            'priority': 3
        }


class FfufParameterBuilder(ToolParameterBuilder):
    """Parameter builder for Ffuf"""
    
    def build_parameters(self) -> Dict[str, Any]:
        """Build Ffuf parameters"""
        # Get active URLs
        urls = self.context.get_active_urls(self.scan_id)
        
        if not urls:
            return {
                'target_hosts': [],
                'command_args': {},
                'reasoning': "No active URLs for directory fuzzing - skipping",
                'priority': 0,
                'skip': True
            }
        
        # Prioritize interesting URLs (admin, api, etc.)
        interesting = self.context.get_interesting_targets(self.scan_id, limit=20)
        active_interesting = [url for url in urls if any(target in url for target in interesting)] if interesting else []
        
        if active_interesting:
            targets = active_interesting[:5]  # Limit to 5 targets
            reasoning = f"Fuzzing directories on {len(targets)} high-priority targets (admin, api, etc.)"
            priority = 4
        else:
            targets = urls[:3]  # Just 3 targets
            reasoning = f"Fuzzing directories on {len(targets)} active URLs"
            priority = 4
        
        return {
            'target_hosts': targets,
            'command_args': {
                'wordlist': 'common.txt',  # Use common wordlist
                'threads': 40,
                'match_status_codes': '200,204,301,302,307,401,403',
                'recursion': False  # No recursion for speed
            },
            'reasoning': reasoning,
            'priority': priority
        }


class Wafw00fParameterBuilder(ToolParameterBuilder):
    """Parameter builder for Wafw00f"""
    
    def build_parameters(self) -> Dict[str, Any]:
        """Build Wafw00f parameters"""
        # Get active URLs
        urls = self.context.get_active_urls(self.scan_id)
        
        if not urls:
            return {
                'target_hosts': [],
                'command_args': {},
                'reasoning': "No active URLs for WAF detection - skipping",
                'priority': 0,
                'skip': True
            }
        
        # WAF detection only needs main domain or a few URLs
        targets = urls[:5] if len(urls) > 5 else urls
        
        return {
            'target_hosts': targets,
            'command_args': {
                'find_all': True
            },
            'reasoning': f"Detecting WAF on {len(targets)} URLs",
            'priority': 3
        }


class ParameterBuilderFactory:
    """
    Factory to create appropriate parameter builder for each tool
    """
    
    _builders = {
        'subfinder': SubfinderParameterBuilder,
        'httpx': HttpxParameterBuilder,
        'nmap': NmapParameterBuilder,
        'nuclei': NucleiParameterBuilder,
        'whatweb': WhatwebParameterBuilder,
        'ffuf': FfufParameterBuilder,
        'wafw00f': Wafw00fParameterBuilder,
    }
    
    @classmethod
    def create_builder(
        cls,
        tool_name: str,
        scan_context_manager: ScanContextManager,
        scan_id: str,
        target: str
    ) -> ToolParameterBuilder:
        """
        Create parameter builder for a tool.
        
        Args:
            tool_name: Tool name (e.g., 'httpx')
            scan_context_manager: ScanContextManager instance
            scan_id: Scan identifier
            target: Original target
            
        Returns:
            ToolParameterBuilder instance
            
        Raises:
            ValueError: If tool not supported
        """
        tool_lower = tool_name.lower()
        
        if tool_lower not in cls._builders:
            logger.warning(f"No parameter builder for '{tool_name}', using base builder")
            # Return a generic builder
            return ToolParameterBuilder(scan_context_manager, scan_id, target)
        
        builder_class = cls._builders[tool_lower]
        builder = builder_class(scan_context_manager, scan_id, target)
        
        logger.debug(f"Created {builder_class.__name__} for {tool_name}")
        return builder
    
    @classmethod
    def get_supported_tools(cls) -> List[str]:
        """Get list of supported tools"""
        return list(cls._builders.keys())


def build_tool_parameters(
    tool_name: str,
    scan_context_manager: ScanContextManager,
    scan_id: str,
    target: str
) -> Dict[str, Any]:
    """
    Convenience function to build parameters for a tool.
    
    Args:
        tool_name: Tool name
        scan_context_manager: ScanContextManager instance
        scan_id: Scan identifier
        target: Original target
        
    Returns:
        Parameter dictionary
    """
    try:
        builder = ParameterBuilderFactory.create_builder(
            tool_name, scan_context_manager, scan_id, target
        )
        params = builder.build_parameters()
        
        logger.info(f"Built parameters for {tool_name}: {params.get('reasoning', 'N/A')}")
        return params
        
    except Exception as e:
        logger.error(f"Failed to build parameters for {tool_name}: {e}", exc_info=True)
        return {
            'target_hosts': [target],
            'command_args': {},
            'reasoning': f"Error building parameters: {str(e)}",
            'priority': 5,
            'error': True
        }

