import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, OrderStatusHistory

logger = logging.getLogger(__name__)

@receiver(post_save, sender=OrderStatusHistory)
def order_status_event_handler(sender, instance, created, **kwargs):
    """
    Simula o consumo de um Evento de Domínio.
    Sempre que um histórico é criado, um evento é "publicado".
    """
    if created:
        event_payload = {
            "event": "order.status_changed",
            "order_id": instance.order.id,
            "old_status": instance.old_status,
            "new_status": instance.new_status,
            "timestamp": instance.changed_at.isoformat()
        }
        
        # Log estruturado 
        logger.info(f"DOMAIN EVENT PUBLISHED: {event_payload}")