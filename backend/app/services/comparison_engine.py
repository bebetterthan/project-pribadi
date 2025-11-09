"""
Comparison Engine - Detect changes between scan runs
FASE 4: Track vulnerability lifecycle and security posture trends
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import Scan, ScanComparison, Vulnerability
from app.repositories.scan_repository import ScanRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.utils.logger import logger
from datetime import datetime
import uuid


class ComparisonEngine:
    """
    Compares two scan runs and generates a detailed change report
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.scan_repo = ScanRepository(db)
        self.vuln_repo = VulnerabilityRepository(db)
    
    async def compare_scans(
        self,
        current_scan_id: str,
        baseline_scan_id: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> ScanComparison:
        """
        Compare two scans and generate a detailed report
        
        If baseline_scan_id not provided, will automatically find the most recent
        completed scan for the same asset before the current scan.
        
        Returns ScanComparison object with detailed changes
        """
        current_scan = self.scan_repo.get(current_scan_id)
        if not current_scan:
            raise ValueError(f"Current scan {current_scan_id} not found")
        
        # Auto-detect baseline if not provided
        if not baseline_scan_id and current_scan.asset_id:
            baseline_scan = self.scan_repo.get_latest_completed_scan(
                asset_id=current_scan.asset_id,
                before_scan_id=current_scan_id
            )
            if baseline_scan:
                baseline_scan_id = baseline_scan.id
        
        if not baseline_scan_id:
            logger.info(f"No baseline scan found for {current_scan_id}, cannot compare")
            return None
        
        baseline_scan = self.scan_repo.get(baseline_scan_id)
        if not baseline_scan:
            raise ValueError(f"Baseline scan {baseline_scan_id} not found")
        
        logger.info(f"Comparing scans: {baseline_scan_id} (baseline) vs {current_scan_id} (current)")
        
        # Generate comparison summary
        summary = await self._generate_comparison_summary(baseline_scan, current_scan)
        
        # Check if comparison already exists
        existing = (
            self.db.query(ScanComparison)
            .filter(
                ScanComparison.baseline_scan_id == baseline_scan_id,
                ScanComparison.current_scan_id == current_scan_id
            )
            .first()
        )
        
        if existing:
            # Update existing comparison
            existing.summary = summary
            existing.changes_detected = summary.get("has_changes", False)
            self.db.commit()
            self.db.refresh(existing)
            logger.info(f"Updated existing comparison: {existing.id}")
            return existing
        
        # Create new comparison
        comparison = ScanComparison(
            id=str(uuid.uuid4()),
            asset_id=current_scan.asset_id,
            baseline_scan_id=baseline_scan_id,
            current_scan_id=current_scan_id,
            comparison_type="auto",
            changes_detected=summary.get("has_changes", False),
            summary=summary,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        
        self.db.add(comparison)
        self.db.commit()
        self.db.refresh(comparison)
        
        logger.info(f"Created new comparison: {comparison.id}")
        return comparison
    
    async def _generate_comparison_summary(
        self,
        baseline_scan: Scan,
        current_scan: Scan
    ) -> Dict[str, Any]:
        """Generate detailed comparison summary"""
        
        # 1. Compare vulnerabilities
        baseline_vulns = self.vuln_repo.get_scan_vulnerabilities(baseline_scan.id, limit=1000)
        current_vulns = self.vuln_repo.get_scan_vulnerabilities(current_scan.id, limit=1000)
        
        vuln_comparison = self._compare_vulnerabilities(baseline_vulns, current_vulns)
        
        # 2. Compare tools executed
        baseline_tools = set(baseline_scan.tools or [])
        current_tools = set(current_scan.tools or [])
        
        tools_added = list(current_tools - baseline_tools)
        tools_removed = list(baseline_tools - current_tools)
        
        # 3. Calculate risk score change
        baseline_risk = self._calculate_risk_score(baseline_vulns)
        current_risk = self._calculate_risk_score(current_vulns)
        risk_delta = current_risk - baseline_risk
        
        # Determine trend
        if risk_delta < -10:
            trend = "improved"
            trend_emoji = "✅"
        elif risk_delta > 10:
            trend = "degraded"
            trend_emoji = "⚠️"
        else:
            trend = "stable"
            trend_emoji = "➖"
        
        # 4. Generate human-readable summary
        summary_text = self._generate_summary_text(
            vuln_comparison,
            risk_delta,
            trend
        )
        
        # 5. Compile complete summary
        summary = {
            "has_changes": (
                len(vuln_comparison["new"]) > 0 or
                len(vuln_comparison["fixed"]) > 0 or
                len(tools_added) > 0 or
                len(tools_removed) > 0
            ),
            "baseline_scan": {
                "id": baseline_scan.id,
                "target": baseline_scan.target,
                "completed_at": baseline_scan.completed_at.isoformat() if baseline_scan.completed_at else None,
                "total_vulns": len(baseline_vulns),
                "risk_score": baseline_risk
            },
            "current_scan": {
                "id": current_scan.id,
                "target": current_scan.target,
                "completed_at": current_scan.completed_at.isoformat() if current_scan.completed_at else None,
                "total_vulns": len(current_vulns),
                "risk_score": current_risk
            },
            "vulnerabilities": vuln_comparison,
            "tools": {
                "added": tools_added,
                "removed": tools_removed
            },
            "risk_analysis": {
                "baseline_score": baseline_risk,
                "current_score": current_risk,
                "delta": risk_delta,
                "trend": trend,
                "trend_emoji": trend_emoji
            },
            "summary_text": summary_text,
            "compared_at": datetime.utcnow().isoformat()
        }
        
        return summary
    
    def _compare_vulnerabilities(
        self,
        baseline_vulns: List[Vulnerability],
        current_vulns: List[Vulnerability]
    ) -> Dict[str, Any]:
        """
        Compare vulnerability lists and identify new, fixed, and unchanged
        
        Matching logic: Same CVE or same title+host
        """
        # Create lookup sets for matching
        baseline_set = {}
        for v in baseline_vulns:
            key = self._vuln_key(v)
            baseline_set[key] = v
        
        current_set = {}
        for v in current_vulns:
            key = self._vuln_key(v)
            current_set[key] = v
        
        # Identify changes
        baseline_keys = set(baseline_set.keys())
        current_keys = set(current_set.keys())
        
        new_keys = current_keys - baseline_keys
        fixed_keys = baseline_keys - current_keys
        unchanged_keys = baseline_keys & current_keys
        
        # Build comparison result
        new_vulns = [self._vuln_summary(current_set[k]) for k in new_keys]
        fixed_vulns = [self._vuln_summary(baseline_set[k]) for k in fixed_keys]
        unchanged_vulns = [self._vuln_summary(current_set[k]) for k in unchanged_keys]
        
        # Count by severity
        new_by_severity = self._count_by_severity([current_set[k] for k in new_keys])
        fixed_by_severity = self._count_by_severity([baseline_set[k] for k in fixed_keys])
        
        return {
            "new": new_vulns,
            "fixed": fixed_vulns,
            "unchanged": len(unchanged_vulns),
            "new_count": len(new_vulns),
            "fixed_count": len(fixed_vulns),
            "new_by_severity": new_by_severity,
            "fixed_by_severity": fixed_by_severity
        }
    
    def _vuln_key(self, vuln: Vulnerability) -> str:
        """Generate unique key for vulnerability matching"""
        if vuln.cve_id:
            return f"cve:{vuln.cve_id}:{vuln.affected_host}"
        else:
            # Fallback to title + host for non-CVE findings
            return f"title:{vuln.title}:{vuln.affected_host}"
    
    def _vuln_summary(self, vuln: Vulnerability) -> Dict[str, Any]:
        """Convert vulnerability to summary dict"""
        return {
            "id": vuln.id,
            "cve_id": vuln.cve_id,
            "title": vuln.title,
            "severity": vuln.severity.value,
            "cvss_score": vuln.cvss_score,
            "affected_host": vuln.affected_host,
            "affected_url": vuln.affected_url
        }
    
    def _count_by_severity(self, vulns: List[Vulnerability]) -> Dict[str, int]:
        """Count vulnerabilities by severity"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for vuln in vulns:
            counts[vuln.severity.value] += 1
        return counts
    
    def _calculate_risk_score(self, vulns: List[Vulnerability]) -> int:
        """
        Calculate overall risk score (0-100) based on vulnerabilities
        
        Formula: Weighted sum of vulnerabilities by severity
        """
        severity_weights = {
            "critical": 40,
            "high": 20,
            "medium": 10,
            "low": 5,
            "info": 1
        }
        
        score = 0
        for vuln in vulns:
            weight = severity_weights.get(vuln.severity.value, 0)
            score += weight
        
        # Cap at 100
        return min(score, 100)
    
    def _generate_summary_text(
        self,
        vuln_comparison: Dict[str, Any],
        risk_delta: int,
        trend: str
    ) -> str:
        """Generate human-readable summary text"""
        lines = []
        
        # Headline
        if trend == "improved":
            lines.append("✅ **Security Posture IMPROVED**")
        elif trend == "degraded":
            lines.append("⚠️ **Security Posture DEGRADED**")
        else:
            lines.append("➖ **Security Posture STABLE**")
        
        lines.append("")
        
        # Risk score change
        if risk_delta > 0:
            lines.append(f"⬆️ Risk score increased by {risk_delta} points")
        elif risk_delta < 0:
            lines.append(f"⬇️ Risk score decreased by {abs(risk_delta)} points")
        else:
            lines.append("➖ Risk score unchanged")
        
        lines.append("")
        
        # New vulnerabilities
        if vuln_comparison["new_count"] > 0:
            lines.append(f"🆕 **New Vulnerabilities:** {vuln_comparison['new_count']}")
            new_by_sev = vuln_comparison["new_by_severity"]
            if new_by_sev["critical"] > 0:
                lines.append(f"  - 🔴 Critical: {new_by_sev['critical']}")
            if new_by_sev["high"] > 0:
                lines.append(f"  - 🟠 High: {new_by_sev['high']}")
            if new_by_sev["medium"] > 0:
                lines.append(f"  - 🟡 Medium: {new_by_sev['medium']}")
        else:
            lines.append("🆕 **New Vulnerabilities:** None")
        
        lines.append("")
        
        # Fixed vulnerabilities
        if vuln_comparison["fixed_count"] > 0:
            lines.append(f"✅ **Fixed Vulnerabilities:** {vuln_comparison['fixed_count']}")
            fixed_by_sev = vuln_comparison["fixed_by_severity"]
            if fixed_by_sev["critical"] > 0:
                lines.append(f"  - 🔴 Critical: {fixed_by_sev['critical']}")
            if fixed_by_sev["high"] > 0:
                lines.append(f"  - 🟠 High: {fixed_by_sev['high']}")
            if fixed_by_sev["medium"] > 0:
                lines.append(f"  - 🟡 Medium: {fixed_by_sev['medium']}")
        else:
            lines.append("✅ **Fixed Vulnerabilities:** None")
        
        # Recommendation
        lines.append("")
        if trend == "degraded":
            lines.append("**Recommendation:** Immediate review required. New vulnerabilities detected.")
        elif trend == "improved":
            lines.append("**Recommendation:** Continue monitoring. Good security hygiene observed.")
        else:
            lines.append("**Recommendation:** Maintain current security practices.")
        
        return "\n".join(lines)

