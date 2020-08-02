import pokeonta.models as models


class AirSupportGroup(models.Model):
    host_id = models.BigIntegerField()
    raid_type = models.CharField(max_length=64)
    location = models.CharField(max_length=64)
    time = models.DateTimeField()
    message_id = models.BigIntegerField()
