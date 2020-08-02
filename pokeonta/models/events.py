import pokeonta.models as models


class Event(models.Model):
    channel_id = models.CharField(max_length=32)
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=2000)
    link = models.CharField(max_length=256)
    starts = models.DateTimeField()
    ends = models.DateTimeField()
    cancelled = models.BooleanField()
