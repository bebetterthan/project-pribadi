from app.db.base import Base
from app.models.user import User
from app.models.team import Team, TeamMember
from app.models.asset import Asset, TargetType, AssetCriticality
from app.models.scan import Scan, ScanStatus
from app.models.result import ScanResult
from app.models.analysis import AIAnalysis
from app.models.chat_message import ChatMessage
from app.models.vulnerability import Vulnerability, VulnerabilitySeverity, VulnerabilityStatus
from app.models.scan_comparison import ScanComparison
from app.models.scan_context import ScanContext, FindingType  # NEW: For tool chaining
from app.models.api_key import APIKey
from app.models.notification import Notification, NotificationType, NotificationChannel
from app.models.webhook import Webhook, WebhookDelivery
from app.models.comment import VulnerabilityComment

__all__ = [
    "Base",
    "User",
    "Team",
    "TeamMember",
    "Asset",
    "TargetType",
    "AssetCriticality",
    "Scan",
    "ScanStatus",
    "ScanResult",
    "AIAnalysis",
    "ChatMessage",
    "Vulnerability",
    "VulnerabilitySeverity",
    "VulnerabilityStatus",
    "ScanComparison",
    "APIKey",
    "Notification",
    "NotificationType",
    "NotificationChannel",
    "Webhook",
    "WebhookDelivery",
    "VulnerabilityComment",
    "ScanContext",  # NEW: For tool chaining
    "FindingType",  # NEW: For tool chaining
]
