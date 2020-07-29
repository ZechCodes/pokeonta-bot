import pokeonta.models as models


class TrainerCards(models.Model):
    user_id = models.CharField(max_length=32)
    trainer_name = models.CharField(max_length=64)
    friend_code = models.CharField(max_length=12)
