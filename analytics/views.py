from django.utils import timezone

from django.shortcuts import render

from jsonrpc import jsonrpc_method
#from ipware.ip import get_real_ip
from ipware.ip import get_ip

from analytics.models import Game, Engine, Map, GameInstance, Event

def checkNull(d, attr):
    if d.get(attr) is None:
        raise "Missing required parameter: " + attr

@jsonrpc_method('openSession(gameInstance=dict) -> int', validate=True)
def openSession(request, gameInstance):
    try:
        game_name = gameInstance["game_name"]
        game_short_name = gameInstance.get("game_short_name")
        game_version = gameInstance.get("game_version")
        engine_version = gameInstance.get("engine_version")
        engine_build_flags = gameInstance.get("engine_build_flags")
        map_name = gameInstance.get("map_name")
        engine_instance_id = gameInstance.get("engine_instance_id")
        user_name = gameInstance.get("user_name")
    except KeyError as k:
        raise Exception("Missing required parameter: " + k.message)

    game = Game.objects.get_or_create(game_name=game_name, 
                              game_version=game_version, 
                              game_short_name=game_short_name)[0]
    engine = None
    if engine_version is not None:
        engine = Engine.objects.get_or_create(engine_version=engine_version)[0]
    map = None
    if map_name is not None:
        map = Map.objects.get_or_create(map_name=map_name)[0]

    user_ip = get_ip(request)
    game_instance = GameInstance(game=game, engine=engine, map=map, engine_instance_id=engine_instance_id, user_name=user_name, user_ip=user_ip, engine_build_flags=engine_build_flags)
    game_instance.save()
    return game_instance.pk

@jsonrpc_method('closeSession(sessionID=int)', validate=True)
def closeSession(request, sessionID):
    game_instance = GameInstance.objects.filter(pk=sessionID).first()
    if game_instance is None:
        raise Exception("No session with id = " + str(sessionID) + ". Did you forget to call openSession(...)?")
    game_instance.stopped_date = timezone.now()
    game_instance.save()

@jsonrpc_method('registerEvent(event=dict) -> Boolean', validate=True)
def registerEvent(request, event):
    try:
        name = event["name"]
        value = event.get("value")
        game_instance_id = event["session_id"]
    except KeyError as k:
        raise Exception("Missing required parameter: " + k.message)
    game_instance = GameInstance.objects.filter(pk=game_instance_id).first()
    if game_instance is None:
        raise Exception("No session with id = " + str(game_instance_id) + ". Did you forget to call openSession(...)?")
    event = Event(name=name, value=value, game_instance=game_instance)
    event.save()
    return True

def index(request):
    gameInstances = GameInstance.objects.all()
    playLengths = []
    for gameInstance in gameInstances:
        startTime, endTime = gameInstance.started_date, gameInstance.stopped_date
        # uncomment if we want to obtain start and end time from game_start, game_end events
        # startTime, endTime = None, None
        #events = gameInstance.event_set.all()
        #for event in events:
        #if event.name == "game_start":
            #startTime = event.upload_date
        #elif event.name == "game_end":
            #endTime = event.upload_date
        if startTime and endTime:
            playLength = endTime - startTime
            playLengths.append(playLength.total_seconds())
    print(len(gameInstances), len(playLengths))
  
    playLengthBuckets = []
    if len(playLengths) > 0:
        playLengths = sorted(playLengths)
        print(playLengths)
        buckets = [("<10s", 10), ("10s-20s", 20), ("20s-1min", 60), ("1min-2min", 120), ("2min-5min", 300), ("5min-10min", 600), ("10min+", float("inf"))]
        bucketNums = [0] * len(buckets)
        for playLength in playLengths:
            for i, bucket in enumerate(buckets):
                if playLength < bucket[1]:
                    bucketNums[i] = bucketNums[i] + 1
                    break
        for i, bucket in enumerate(buckets):
            playLengthBuckets.append((bucket[0], bucketNums[i]))
        # AUTO sorting, might use later on..
        #bucketNum = min(3, len(playLengths))
        #bucketSize = len(playLengths) * 1.0 / bucketNum
        #for i in range(bucketNum):
            #bucketLengths = playLengths[int(i * bucketSize) : int((i + 1) * bucketSize)]
            #rangeStr = str(bucketLengths[0]) + "s - " + str(bucketLengths[-1]) + "s"
            #playLengthBuckets.append((rangeStr, len(bucketLengths)))
    print(playLengthBuckets)
    
    dateBuckets = []
    dates = GameInstance.objects.values_list("started_date", flat=True)
    print(dates)
    dates = sorted(dates)
    days = {}
    for dt in dates:
        days.setdefault(dt.toordinal(), []).append(dt)
    dates = []
    for day in range(min(days), max(days)+1):
        date = dt.fromordinal(day)
        numPlayers = len(days.get(day, []))
        dates.append((date.strftime("%d/%m/%y"), numPlayers))
    print(dates)
    context = {"playLengthBuckets":playLengthBuckets, "dayActivities":dates}
    return render(request, 'index.html', context)