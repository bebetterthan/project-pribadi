"""
CVE Enrichment Service
Fase 3.5: Auto-enrich CVEs with real-world threat intelligence
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from app.utils.logger import logger

class CVEEnricher:
    """
    Enrich CVE identifiers with real-world threat intelligence
    
    Data Sources:
    - NVD (National Vulnerability Database) - Free, rate-limited
    - CVE Circl.lu - Free, no rate limit
    """
    
    NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    CIRCL_API_URL = "https://cve.circl.lu/api/cve"
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def enrich_cve(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Enrich single CVE with threat intelligence
        
        Args:
            cve_id: CVE identifier (e.g., 'CVE-2023-12345')
            
        Returns:
            Enrichment data or None if unavailable
        """
        # Check cache first
        if cve_id in self.cache:
            logger.debug(f"CVE {cve_id} found in cache")
            return self.cache[cve_id]
        
        # Try Circl.lu first (no rate limit)
        enrichment = await self._fetch_from_circl(cve_id)
        
        # Fallback to NVD if Circl fails
        if not enrichment or not enrichment.get('cvss_score'):
            logger.debug(f"Circl failed for {cve_id}, trying NVD")
            enrichment = await self._fetch_from_nvd(cve_id)
        
        # Cache result
        if enrichment:
            self.cache[cve_id] = enrichment
            
        return enrichment
    
    async def _fetch_from_circl(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch CVE data from CVE Circl.lu
        
        Args:
            cve_id: CVE identifier
            
        Returns:
            Parsed CVE data
        """
        try:
            url = f"{self.CIRCL_API_URL}/{cve_id}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Circl returned {response.status} for {cve_id}")
                    return None
                
                data = await response.json()
                
                # Parse Circl format
                return self._parse_circl_response(data)
                
        except Exception as e:
            logger.error(f"Failed to fetch from Circl for {cve_id}: {e}")
            return None
    
    async def _fetch_from_nvd(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch CVE data from NVD
        
        Args:
            cve_id: CVE identifier
            
        Returns:
            Parsed CVE data
        """
        try:
            url = f"{self.NVD_API_URL}?cveId={cve_id}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"NVD returned {response.status} for {cve_id}")
                    return None
                
                data = await response.json()
                
                # Parse NVD format
                return self._parse_nvd_response(data)
                
        except Exception as e:
            logger.error(f"Failed to fetch from NVD for {cve_id}: {e}")
            return None
    
    def _parse_circl_response(self, data: Dict) -> Dict[str, Any]:
        """Parse Circl.lu API response"""
        try:
            # Extract key fields
            cvss_score = None
            cvss_vector = None
            
            # Circl provides cvss, cvss-time, cvss-vector
            if 'cvss' in data:
                cvss_score = float(data['cvss'])
            if 'cvss-vector' in data:
                cvss_vector = data['cvss-vector']
            
            description = data.get('summary', 'No description available')
            published = data.get('Published', '')
            
            return {
                'cvss_score': cvss_score,
                'cvss_vector': cvss_vector,
                'severity': self._cvss_to_severity(cvss_score) if cvss_score else 'unknown',
                'description': description,
                'published_date': published,
                'source': 'circl.lu',
                'exploit_available': False,  # Circl doesn't provide this
                'patch_available': None,  # Not provided
                'references': data.get('references', []),
            }
        except Exception as e:
            logger.error(f"Failed to parse Circl response: {e}")
            return {}
    
    def _parse_nvd_response(self, data: Dict) -> Dict[str, Any]:
        """Parse NVD API response"""
        try:
            vulnerabilities = data.get('vulnerabilities', [])
            if not vulnerabilities:
                return {}
            
            cve = vulnerabilities[0]['cve']
            
            # Extract CVSS metrics
            cvss_score = None
            cvss_vector = None
            severity = 'unknown'
            
            metrics = cve.get('metrics', {})
            if 'cvssMetricV31' in metrics and metrics['cvssMetricV31']:
                cvss_data = metrics['cvssMetricV31'][0]['cvssData']
                cvss_score = cvss_data.get('baseScore')
                cvss_vector = cvss_data.get('vectorString')
                severity = cvss_data.get('baseSeverity', '').lower()
            elif 'cvssMetricV2' in metrics and metrics['cvssMetricV2']:
                cvss_data = metrics['cvssMetricV2'][0]['cvssData']
                cvss_score = cvss_data.get('baseScore')
                cvss_vector = cvss_data.get('vectorString')
                severity = cvss_data.get('baseSeverity', '').lower()
            
            # Extract description
            descriptions = cve.get('descriptions', [])
            description = descriptions[0]['value'] if descriptions else 'No description available'
            
            # Extract dates
            published = cve.get('published', '')
            last_modified = cve.get('lastModified', '')
            
            # Extract references
            references = cve.get('references', [])
            ref_urls = [ref['url'] for ref in references]
            
            return {
                'cvss_score': cvss_score,
                'cvss_vector': cvss_vector,
                'severity': severity,
                'description': description,
                'published_date': published,
                'last_modified_date': last_modified,
                'source': 'nvd.nist.gov',
                'exploit_available': self._check_exploit_in_references(ref_urls),
                'patch_available': self._check_patch_in_references(ref_urls),
                'references': ref_urls,
            }
        except Exception as e:
            logger.error(f"Failed to parse NVD response: {e}")
            return {}
    
    def _cvss_to_severity(self, score: float) -> str:
        """Convert CVSS score to severity label"""
        if score >= 9.0:
            return 'critical'
        elif score >= 7.0:
            return 'high'
        elif score >= 4.0:
            return 'medium'
        elif score > 0:
            return 'low'
        else:
            return 'unknown'
    
    def _check_exploit_in_references(self, urls: list) -> bool:
        """Check if any reference URL indicates exploit availability"""
        exploit_indicators = [
            'exploit-db.com',
            'packetstormsecurity.com',
            'metasploit',
            'exploit',
        ]
        return any(indicator in url.lower() for url in urls for indicator in exploit_indicators)
    
    def _check_patch_in_references(self, urls: list) -> bool:
        """Check if any reference URL indicates patch availability"""
        patch_indicators = [
            'security.gentoo.org',
            'security-tracker.debian.org',
            'access.redhat.com',
            'ubuntu.com/security',
            '/patch',
            '/security',
            '/advisory',
        ]
        return any(indicator in url.lower() for url in urls for indicator in patch_indicators)
    
    def calculate_priority_score(self, enrichment: Dict[str, Any]) -> int:
        """
        Calculate priority score (0-100) based on enrichment data
        
        Factors:
        - CVSS score (40% weight)
        - Exploit availability (+30 points)
        - Public exploit (+20 points if exploit mature)
        - No patch available (+10 points)
        
        Returns:
            Priority score (0-100)
        """
        score = 0.0
        
        # CVSS score contribution (40% of total)
        cvss = enrichment.get('cvss_score', 0)
        if cvss:
            score += (cvss / 10.0) * 40
        
        # Exploit availability
        if enrichment.get('exploit_available'):
            score += 30
            
        # Patch availability (no patch = higher priority)
        if not enrichment.get('patch_available'):
            score += 10
        
        # Cap at 100
        return min(int(score), 100)
    
    def generate_recommendation(self, cve_id: str, enrichment: Dict[str, Any]) -> str:
        """
        Generate actionable recommendation based on enrichment
        
        Args:
            cve_id: CVE identifier
            enrichment: Enrichment data
            
        Returns:
            Actionable recommendation text
        """
        priority = self.calculate_priority_score(enrichment)
        cvss = enrichment.get('cvss_score', 0)
        exploit = enrichment.get('exploit_available', False)
        patch = enrichment.get('patch_available', False)
        
        # Build recommendation
        if priority >= 80:
            urgency = "URGENT"
        elif priority >= 60:
            urgency = "HIGH PRIORITY"
        elif priority >= 40:
            urgency = "MEDIUM PRIORITY"
        else:
            urgency = "LOW PRIORITY"
        
        recommendation = f"{urgency}: {cve_id} detected. "
        
        if cvss:
            recommendation += f"CVSS {cvss} ({enrichment.get('severity', 'unknown').upper()}). "
        
        if exploit:
            recommendation += "Public exploit available - high risk of exploitation. "
        
        if patch:
            recommendation += "Patch available - apply immediately. "
        else:
            recommendation += "No patch available - implement compensating controls. "
        
        # Add specific actions
        if priority >= 80:
            recommendation += "Recommended: Immediate patching or service isolation."
        elif priority >= 60:
            recommendation += "Recommended: Schedule patching within 24-48 hours."
        elif priority >= 40:
            recommendation += "Recommended: Include in next maintenance window."
        else:
            recommendation += "Recommended: Monitor for updates."
        
        return recommendation


# Convenience function for single CVE enrichment
async def enrich_cve_async(cve_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to enrich single CVE
    
    Args:
        cve_id: CVE identifier
        
    Returns:
        Enrichment data
    """
    async with CVEEnricher() as enricher:
        return await enricher.enrich_cve(cve_id)


# Convenience function for batch CVE enrichment
async def enrich_cves_batch(cve_ids: list) -> Dict[str, Dict[str, Any]]:
    """
    Enrich multiple CVEs concurrently
    
    Args:
        cve_ids: List of CVE identifiers
        
    Returns:
        Dict mapping CVE IDs to enrichment data
    """
    async with CVEEnricher() as enricher:
        tasks = [enricher.enrich_cve(cve_id) for cve_id in cve_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            cve_id: result if not isinstance(result, Exception) else None
            for cve_id, result in zip(cve_ids, results)
        }

