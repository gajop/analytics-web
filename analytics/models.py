from django.db import models

# Create your models here.

class Game(models.Model):
    game_name = models.CharField(max_length=200)
    game_short_name = models.CharField(max_length=20, null=True, blank=True)
    game_version = models.CharField(max_length=200, null=True, blank=True)
    class Meta:
        unique_together = ("game_name", "game_version")

class Engine(models.Model):
    engine_version = models.CharField(max_length=200)

class Map(models.Model):
    map_name = models.CharField(max_length=200, unique=True)

class GameInstance(models.Model):
    # game static
    game = models.ForeignKey('Game')
    engine = models.ForeignKey('Engine', null=True, blank=True)
    map = models.ForeignKey('Map', null=True, blank=True)
    engine_instance_id = models.CharField(max_length=200, null=True, blank=True)
    # TODO: consider separating users from game instance to allow multiple recordings of the same instance
    user_name = models.CharField(max_length=200, null=True, blank=True)
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    # engine build flags are actually unsynced (player specific)
    engine_build_flags = models.CharField(max_length=200, null=True, blank=True)
    started_date = models.DateTimeField(auto_now_add=True, blank=True)
    stopped_date = models.DateTimeField(blank=True, null=True)

class Event(models.Model):
    game_instance = models.ForeignKey("GameInstance")
    upload_date = models.DateTimeField(auto_now_add=True, blank=True)

    # custom fields
    name = models.CharField(max_length=200)
    value_str   = models.CharField(max_length=500, null=True, blank=True)
    value_float = models.FloatField(null=True, blank=True)
    # TODO: use something like attribute/value store instead
