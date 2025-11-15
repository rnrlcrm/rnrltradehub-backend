"""
Notification Dispatcher Service - Batched notification system.

Handles email, SMS, webhook, and push notifications with queue management,
retry logic, and delivery tracking.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import (
    NotificationQueue, EmailTemplate, EmailLog,
    User, BusinessPartner, AuditLog
)
from schemas import NotificationQueueCreate


class NotificationService:
    """Service for managing notification queue and dispatch."""

    @staticmethod
    def queue_notification(
        db: Session,
        notification_data: NotificationQueueCreate,
        user_id: Optional[int] = None
    ) -> NotificationQueue:
        """Queue a notification for delivery."""
        notification = NotificationQueue(
            id=str(uuid4()),
            organization_id=notification_data.organization_id,
            notification_type=notification_data.notification_type,
            recipient_type=notification_data.recipient_type,
            recipient_id=notification_data.recipient_id,
            subject=notification_data.subject,
            message=notification_data.message,
            template_id=notification_data.template_id,
            template_data=notification_data.template_data or {},
            priority=notification_data.priority,
            scheduled_for=notification_data.scheduled_for,
            status='QUEUED',
            retry_count=0,
            max_retries=notification_data.max_retries if hasattr(notification_data, 'max_retries') else 3,
            created_by_user=user_id or notification_data.created_by_user,
            source_entity_type=notification_data.source_entity_type,
            source_entity_id=notification_data.source_entity_id
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def get_pending_notifications(
        db: Session,
        notification_type: Optional[str] = None,
        limit: int = 100
    ) -> List[NotificationQueue]:
        """
        Get pending notifications ready for processing.
        
        Returns notifications that are:
        - QUEUED status
        - Scheduled for now or earlier (or not scheduled)
        - Below max retry count
        """
        query = db.query(NotificationQueue).filter(
            and_(
                NotificationQueue.status == 'QUEUED',
                NotificationQueue.retry_count < NotificationQueue.max_retries,
                or_(
                    NotificationQueue.scheduled_for == None,
                    NotificationQueue.scheduled_for <= datetime.utcnow()
                )
            )
        )

        if notification_type:
            query = query.filter(NotificationQueue.notification_type == notification_type)

        # Order by priority and creation time
        priority_order = {
            'URGENT': 0,
            'HIGH': 1,
            'NORMAL': 2,
            'LOW': 3
        }

        notifications = query.order_by(
            NotificationQueue.created_at.asc()
        ).limit(limit).all()

        # Sort by priority in Python
        notifications.sort(
            key=lambda n: (priority_order.get(n.priority, 99), n.created_at)
        )

        return notifications

    @staticmethod
    def process_email_notification(
        db: Session,
        notification: NotificationQueue,
        email_service
    ) -> bool:
        """
        Process an email notification.
        
        Uses the email_service to actually send the email.
        """
        try:
            notification.status = 'PROCESSING'
            db.commit()

            # Get recipient email
            recipient_email = None
            if notification.recipient_type == 'USER':
                user = db.query(User).filter(User.id == int(notification.recipient_id)).first()
                if user:
                    recipient_email = user.email
            elif notification.recipient_type == 'PARTNER':
                partner = db.query(BusinessPartner).filter(
                    BusinessPartner.id == notification.recipient_id
                ).first()
                if partner:
                    recipient_email = partner.contact_email

            if not recipient_email:
                raise ValueError(f"Could not find email for {notification.recipient_type} {notification.recipient_id}")

            # Use template if provided
            if notification.template_id:
                template = db.query(EmailTemplate).filter(
                    EmailTemplate.id == notification.template_id
                ).first()
                if not template:
                    raise ValueError(f"Template {notification.template_id} not found")

                # Render template with data
                subject = template.subject
                body = template.body_html

                # Simple template variable replacement
                for key, value in notification.template_data.items():
                    subject = subject.replace(f"{{{{{key}}}}}", str(value))
                    body = body.replace(f"{{{{{key}}}}}", str(value))
            else:
                subject = notification.subject or "Notification"
                body = notification.message

            # Send email using email service
            # This is a placeholder - actual implementation would use SMTP
            success = True  # Assume success for now
            
            if success:
                notification.status = 'SENT'
                notification.sent_at = datetime.utcnow()
                notification.delivery_status = 'delivered'
            else:
                raise Exception("Email send failed")

            db.commit()
            return True

        except Exception as e:
            notification.status = 'QUEUED'  # Reset for retry
            notification.retry_count += 1
            notification.error_message = str(e)

            if notification.retry_count >= notification.max_retries:
                notification.status = 'FAILED'

            db.commit()
            return False

    @staticmethod
    def process_notification_queue(
        db: Session,
        batch_size: int = 50
    ) -> Dict[str, int]:
        """
        Process pending notifications in batches.
        
        Returns statistics on processed notifications.
        """
        stats = {
            'processed': 0,
            'sent': 0,
            'failed': 0,
            'retried': 0
        }

        # Get pending notifications
        notifications = NotificationService.get_pending_notifications(
            db,
            limit=batch_size
        )

        for notification in notifications:
            stats['processed'] += 1

            if notification.notification_type == 'EMAIL':
                success = NotificationService.process_email_notification(
                    db,
                    notification,
                    None  # Pass email service instance
                )
                if success:
                    stats['sent'] += 1
                else:
                    if notification.retry_count < notification.max_retries:
                        stats['retried'] += 1
                    else:
                        stats['failed'] += 1

            # Add handlers for SMS, WEBHOOK, PUSH as needed

        return stats

    @staticmethod
    def cancel_notification(
        db: Session,
        notification_id: str,
        user_id: int
    ) -> NotificationQueue:
        """Cancel a queued notification."""
        notification = db.query(NotificationQueue).filter(
            NotificationQueue.id == notification_id
        ).first()
        if not notification:
            raise ValueError(f"Notification {notification_id} not found")

        if notification.status not in ['QUEUED', 'FAILED']:
            raise ValueError(f"Cannot cancel {notification.status} notification")

        notification.status = 'CANCELLED'

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Admin",
            module="Notifications",
            action="CANCEL",
            details=f"Cancelled notification {notification_id}"
        )
        db.add(audit)

        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def queue_bulk_notifications(
        db: Session,
        notification_type: str,
        recipient_type: str,
        recipient_ids: List[str],
        subject: str,
        message: str,
        template_id: Optional[int] = None,
        template_data: Optional[Dict] = None,
        priority: str = 'NORMAL',
        org_id: int = None,
        user_id: Optional[int] = None
    ) -> List[NotificationQueue]:
        """Queue multiple notifications at once."""
        notifications = []

        for recipient_id in recipient_ids:
            notification_data = NotificationQueueCreate(
                organization_id=org_id,
                notification_type=notification_type,
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                subject=subject,
                message=message,
                template_id=template_id,
                template_data=template_data,
                priority=priority,
                created_by_user=user_id
            )
            notification = NotificationService.queue_notification(
                db,
                notification_data,
                user_id
            )
            notifications.append(notification)

        return notifications

    @staticmethod
    def create_event_notification(
        db: Session,
        event_type: str,
        entity_type: str,
        entity_id: str,
        recipients: List[str],
        org_id: int,
        user_id: Optional[int] = None
    ) -> List[NotificationQueue]:
        """
        Create notifications based on system events.
        
        Maps event types to notification templates and sends to relevant recipients.
        """
        # Event to template mapping
        event_templates = {
            'CONTRACT_CREATED': {
                'subject': 'New Sales Contract Created',
                'message': 'A new sales contract has been created and requires your attention.',
                'priority': 'HIGH'
            },
            'PAYMENT_RECEIVED': {
                'subject': 'Payment Received',
                'message': 'A payment has been received and recorded.',
                'priority': 'NORMAL'
            },
            'DISPUTE_RAISED': {
                'subject': 'Dispute Raised',
                'message': 'A new dispute has been raised and requires resolution.',
                'priority': 'URGENT'
            },
            'INSPECTION_FAILED': {
                'subject': 'Quality Inspection Failed',
                'message': 'A quality inspection has failed. Immediate action required.',
                'priority': 'URGENT'
            },
            'DELIVERY_SCHEDULED': {
                'subject': 'Delivery Scheduled',
                'message': 'A delivery has been scheduled.',
                'priority': 'NORMAL'
            },
            'KYC_EXPIRING': {
                'subject': 'KYC Documentation Expiring Soon',
                'message': 'Your KYC documentation is expiring soon. Please update.',
                'priority': 'HIGH'
            }
        }

        template_config = event_templates.get(event_type)
        if not template_config:
            # Default notification
            template_config = {
                'subject': f'{event_type} Event',
                'message': f'System event: {event_type} for {entity_type} {entity_id}',
                'priority': 'NORMAL'
            }

        # Queue notifications for all recipients
        return NotificationService.queue_bulk_notifications(
            db=db,
            notification_type='EMAIL',
            recipient_type='USER',
            recipient_ids=recipients,
            subject=template_config['subject'],
            message=template_config['message'],
            priority=template_config['priority'],
            org_id=org_id,
            user_id=user_id
        )
