from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from contracts.models import ContractType, Party, Contract, ContractParty, ContractMilestone

@receiver(post_save, sender=Contract)
def contract_saved(sender, instance, created, **kwargs):
    # TODO: Add audit logging or notifications for contract create/update
    pass

@receiver(post_delete, sender=Contract)
def contract_deleted(sender, instance, **kwargs):
    # TODO: Add audit logging or notifications for contract delete
    pass

@receiver(post_save, sender=ContractType)
def contracttype_saved(sender, instance, created, **kwargs):
    # TODO: Add audit logging or notifications for contract type create/update
    pass

@receiver(post_delete, sender=ContractType)
def contracttype_deleted(sender, instance, **kwargs):
    # TODO: Add audit logging or notifications for contract type delete
    pass

@receiver(post_save, sender=Party)
def party_saved(sender, instance, created, **kwargs):
    # TODO: Add audit logging or notifications for party create/update
    pass

@receiver(post_delete, sender=Party)
def party_deleted(sender, instance, **kwargs):
    # TODO: Add audit logging or notifications for party delete
    pass

@receiver(post_save, sender=ContractParty)
def contractparty_saved(sender, instance, created, **kwargs):
    # TODO: Add audit logging or notifications for contract party create/update
    pass

@receiver(post_delete, sender=ContractParty)
def contractparty_deleted(sender, instance, **kwargs):
    # TODO: Add audit logging or notifications for contract party delete
    pass

@receiver(post_save, sender=ContractMilestone)
def contractmilestone_saved(sender, instance, created, **kwargs):
    # TODO: Add audit logging or notifications for contract milestone create/update
    pass

@receiver(post_delete, sender=ContractMilestone)
def contractmilestone_deleted(sender, instance, **kwargs):
    # TODO: Add audit logging or notifications for contract milestone delete
    pass 