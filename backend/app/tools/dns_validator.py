"""
DNS Validation for discovered subdomains
Filters out invalid/non-existent domains
"""
import asyncio
import socket
from typing import List, Dict, Any, Tuple
from app.utils.logger import logger


class DNSValidator:
    """Validate DNS resolution for subdomains"""
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
    
    async def validate_bulk(self, subdomains: List[str]) -> Dict[str, Any]:
        """
        Validate multiple subdomains in parallel
        
        Returns:
            Dict with valid and invalid subdomain lists
        """
        logger.info(f"🔍 DNS Validation: Testing {len(subdomains)} subdomains...")
        
        # Validate all subdomains in parallel
        tasks = [self._validate_single(subdomain) for subdomain in subdomains]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid = []
        invalid = []
        
        for subdomain, result in zip(subdomains, results):
            if isinstance(result, Exception):
                logger.warning(f"❌ {subdomain}: Validation error - {result}")
                invalid.append({"subdomain": subdomain, "reason": "validation_error"})
            elif result:
                ip_address, status = result
                if status == "valid":
                    valid.append({"subdomain": subdomain, "ip": ip_address})
                    logger.debug(f"✅ {subdomain} → {ip_address}")
                else:
                    invalid.append({"subdomain": subdomain, "reason": status})
                    logger.debug(f"❌ {subdomain}: {status}")
            else:
                invalid.append({"subdomain": subdomain, "reason": "unknown"})
        
        logger.info(f"✅ DNS Validation Complete: {len(valid)} valid, {len(invalid)} invalid")
        
        return {
            "total_tested": len(subdomains),
            "valid_count": len(valid),
            "invalid_count": len(invalid),
            "valid_subdomains": valid,
            "invalid_subdomains": invalid,
            "validation_rate": f"{(len(valid)/len(subdomains)*100):.1f}%" if subdomains else "0%"
        }
    
    async def _validate_single(self, subdomain: str) -> Tuple[str, str]:
        """
        Validate a single subdomain
        
        Returns:
            Tuple of (ip_address, status)
            status: "valid", "nxdomain", "timeout", "error"
        """
        try:
            # Use asyncio to run DNS lookup with timeout
            loop = asyncio.get_event_loop()
            ip_address = await asyncio.wait_for(
                loop.run_in_executor(None, socket.gethostbyname, subdomain),
                timeout=self.timeout
            )
            return (ip_address, "valid")
        
        except socket.gaierror as e:
            # DNS resolution failed - domain doesn't exist
            if e.errno == -2 or e.errno == -5:  # NXDOMAIN
                return ("", "nxdomain")
            else:
                return ("", f"dns_error_{e.errno}")
        
        except asyncio.TimeoutError:
            return ("", "timeout")
        
        except Exception as e:
            logger.warning(f"Unexpected error validating {subdomain}: {e}")
            return ("", "error")
    
    def format_validation_report(self, results: Dict[str, Any]) -> str:
        """Format validation results for display"""
        report = []
        report.append("=" * 60)
        report.append("🔍 DNS VALIDATION RESULTS")
        report.append("=" * 60)
        report.append(f"Total Tested: {results['total_tested']}")
        report.append(f"Valid: {results['valid_count']} ({results['validation_rate']})")
        report.append(f"Invalid: {results['invalid_count']}")
        report.append("")
        
        if results['valid_subdomains']:
            report.append("✅ VALID SUBDOMAINS:")
            for item in results['valid_subdomains'][:10]:  # Show first 10
                report.append(f"   • {item['subdomain']} → {item['ip']}")
            if len(results['valid_subdomains']) > 10:
                report.append(f"   ... and {len(results['valid_subdomains'])-10} more")
        
        report.append("")
        
        if results['invalid_subdomains']:
            report.append("❌ INVALID SUBDOMAINS:")
            reason_counts = {}
            for item in results['invalid_subdomains']:
                reason = item['reason']
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
            
            for reason, count in reason_counts.items():
                report.append(f"   • {reason}: {count} subdomains")
        
        report.append("=" * 60)
        return "\n".join(report)

