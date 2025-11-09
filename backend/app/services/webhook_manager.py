"""
Webhook Manager - Event-driven integration system
FASE 5: Webhook system with delivery and retry logic
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import Webhook, WebhookDelivery
from app.utils.logger import logger
from datetime import datetime
import uuid
import httpx
import hmac
import hashlib
import json
import asyncio


class WebhookManager:
    """Manage webhooks and event delivery"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_webhook(
        self,
        user_id: str,
        name: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Webhook:
        """Create new webhook"""
        webhook = Webhook(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            url=url,
            secret=secret,
            events=events,
            filters=filters,
            is_active=True
        )
        
        self.db.add(webhook)
        self.db.commit()
        self.db.refresh(webhook)
        
        logger.info(f"[Webhook] Created: {name} for user {user_id}")
        return webhook
    
    async def trigger_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        user_id: Optional[str] = None
    ):
        """
        Trigger webhooks for an event
        
        Args:
            event_type: Type of event (scan.completed, vulnerability.found, etc.)
            payload: Event data
            user_id: Optional user ID to filter webhooks
        """
        # Find active webhooks for this event
        query = self.db.query(Webhook).filter(
            Webhook.is_active == True,
            Webhook.events.contains([event_type])
        )
        
        if user_id:
            query = query.filter(Webhook.user_id == user_id)
        
        webhooks = query.all()
        
        if not webhooks:
            logger.debug(f"[Webhook] No webhooks for event: {event_type}")
            return
        
        logger.info(f"[Webhook] Triggering {len(webhooks)} webhooks for event: {event_type}")
        
        # Trigger each webhook asynchronously
        tasks = [self._deliver_webhook(webhook, event_type, payload) for webhook in webhooks]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _deliver_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        payload: Dict[str, Any]
    ):
        """Deliver webhook with retry logic"""
        # Apply filters if configured
        if webhook.filters and not self._apply_filters(payload, webhook.filters):
            logger.debug(f"[Webhook] Filtered out: {webhook.name}")
            return
        
        # Prepare payload
        full_payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload
        }
        
        # Create delivery record
        delivery = WebhookDelivery(
            id=str(uuid.uuid4()),
            webhook_id=webhook.id,
            event_type=event_type,
            payload=full_payload,
            attempt_number=1
        )
        self.db.add(delivery)
        self.db.commit()
        self.db.refresh(delivery)
        
        # Attempt delivery with retries
        max_attempts = webhook.retry_count
        for attempt in range(1, max_attempts + 1):
            try:
                success = await self._send_webhook_request(webhook, full_payload)
                
                if success:
                    # Success!
                    delivery.success = True
                    delivery.delivered_at = datetime.utcnow()
                    webhook.last_success_at = datetime.utcnow()
                    webhook.success_count += 1
                    self.db.commit()
                    
                    logger.info(f"[Webhook] Delivered: {webhook.name} (attempt {attempt})")
                    return
                
            except Exception as e:
                logger.error(f"[Webhook] Delivery failed: {webhook.name} (attempt {attempt}): {e}")
                delivery.error_message = str(e)
            
            # Update attempt number
            delivery.attempt_number = attempt
            self.db.commit()
            
            # Wait before retry (exponential backoff)
            if attempt < max_attempts:
                await asyncio.sleep(2 ** attempt)  # 2s, 4s, 8s...
        
        # All attempts failed
        delivery.success = False
        webhook.last_failure_at = datetime.utcnow()
        webhook.last_error = delivery.error_message
        webhook.failure_count += 1
        self.db.commit()
        
        logger.error(f"[Webhook] All attempts failed: {webhook.name}")
    
    async def _send_webhook_request(
        self,
        webhook: Webhook,
        payload: Dict[str, Any]
    ) -> bool:
        """Send actual HTTP request to webhook URL"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Agent-P-Webhook/1.0"
        }
        
        # Add HMAC signature if secret configured
        if webhook.secret:
            payload_bytes = json.dumps(payload).encode()
            signature = hmac.new(
                webhook.secret.encode(),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"
        
        async with httpx.AsyncClient(timeout=webhook.timeout_seconds) as client:
            response = await client.post(
                webhook.url,
                json=payload,
                headers=headers
            )
            
            # Consider 2xx as success
            return 200 <= response.status_code < 300
    
    def _apply_filters(self, payload: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if payload matches filters"""
        # Simple filter implementation
        # Example: {"severity": "critical"} only triggers for critical vulnerabilities
        for key, value in filters.items():
            if payload.get(key) != value:
                return False
        return True
    
    def get_user_webhooks(self, user_id: str) -> List[Webhook]:
        """Get all webhooks for user"""
        return self.db.query(Webhook).filter(Webhook.user_id == user_id).all()
    
    def get_webhook_deliveries(
        self,
        webhook_id: str,
        limit: int = 50
    ) -> List[WebhookDelivery]:
        """Get recent deliveries for webhook"""
        return (
            self.db.query(WebhookDelivery)
            .filter(WebhookDelivery.webhook_id == webhook_id)
            .order_by(WebhookDelivery.created_at.desc())
            .limit(limit)
            .all()
        )
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete webhook"""
        webhook = self.db.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return False
        
        self.db.delete(webhook)
        self.db.commit()
        
        logger.info(f"[Webhook] Deleted: {webhook.name}")
        return True

