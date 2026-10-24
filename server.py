import os
import asyncio, json, math, random, time
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from websockets.asyncio.server import serve
from websockets.http11 import Response
from websockets.datastructures import Headers

ROOT=Path(__file__).resolve().parent
players=[None,None]
units=[]
towers=[{'team':team,'x':x,'y':y,'hp':100} for team,y in [(0,555),(1,85)] for x in [100,320]]
elixir=[5.,5.]
remaining=120
message='Waiting for two players'
costs={'Knight':3,'Archer':3,'Giant':5,'Runner':2}
health={'Knight':28,'Archer':17,'Giant':75,'Runner':12}
speed={'Knight':42,'Archer':31,'Giant':20,'Runner':70}
damage={'Knight':8,'Archer':5,'Giant':12,'Runner':5}
started=False

def snapshot():
 return {'units':units,'towers':towers,'elixir':elixir,'time':max(0,math.ceil(remaining)),'message':message}
async def broadcast():
 msg=json.dumps({'type':'state','state':snapshot()})
 for p in players:
  if p:
   try: await p.send(msg)
   except: pass
async def handler(ws):
    global started, message
    try:
        slot = players.index(None)
    except ValueError:
  await ws.send(json.dumps({'type':'error','message':'Room full. Two players maximum.'}));await ws.close();return
 players[slot]=ws
 await ws.send(json.dumps({'type':'hello','player':slot}))
 if all(players): started=True;message='Battle started!'
 await broadcast()
 try:
  async for raw in ws:
   try: m=json.loads(raw)
   except: continue
   if m.get('type')!='deploy' or not started or remaining<=0:continue
   typ=m.get('unit');x=m.get('x');y=m.get('y')
   if typ not in costs or not isinstance(x,(int,float)) or not isinstance(y,(int,float)):continue
   if not (20<x<400 and ((340<y<615) if slot==0 else (25<y<300))):continue
   if elixir[slot]<costs[typ]:continue
   elixir[slot]-=costs[typ]
   units.append({'team':slot,'type':typ,'x':float(x),'y':float(y),'hp':health[typ],'cooldown':0})
 finally:
  players[slot]=None;started=False;message='Player disconnected. Waiting for two players';await broadcast()
async def loop():
 global remaining,message,started
 dt=.1
 while True:
  await asyncio.sleep(dt)
  if started and remaining>0:
   remaining=max(0,remaining-dt)
   for i in range(2):elixir[i]=min(10,elixir[i]+dt*.7)
   for u in units[:]:
    enemies=[e for e in units if e['team']!=u['team']]
    targets=enemies+[t for t in towers if t['team']!=u['team'] and t['hp']>0]
    if not targets:continue
    target=min(targets,key=lambda t:(u['x']-t['x'])**2+(u['y']-t['y'])**2)
    dist=math.hypot(u['x']-target['x'],u['y']-target['y']) or 1
    reach=105 if u['type']=='Archer' else 23
    u['cooldown']-=dt
    if dist>reach:
     u['x']+=(target['x']-u['x'])/dist*speed[u['type']]*dt
     u['y']+=(target['y']-u['y'])/dist*speed[u['type']]*dt
    elif u['cooldown']<=0:
     target['hp']-=damage[u['type']];u['cooldown']=1.0
   units[:]=[u for u in units if u['hp']>0]
   for t in towers:
    if t['hp']<=0:continue
    nearby=[u for u in units if u['team']!=t['team'] and math.hypot(u['x']-t['x'],u['y']-t['y'])<125]
    if nearby: min(nearby,key=lambda u:math.hypot(u['x']-t['x'],u['y']-t['y']))['hp']-=dt*5
   if not any(t['hp']>0 for t in towers if t['team']==0):message='Red wins!';remaining=0
   elif not any(t['hp']>0 for t in towers if t['team']==1):message='Blue wins!';remaining=0
   elif remaining<=0:
    a=[sum(max(0,t['hp']) for t in towers if t['team']==i) for i in range(2)]
    message='Blue wins!' if a[0]>a[1] else 'Red wins!' if a[1]>a[0] else 'Draw!'
  await broadcast()
async def main():
 async def process_request(conn,req):
  if req.path not in ('/','/index.html'):return Response(404,'Not Found',Headers(),b'Not found')
  return Response(200,'OK',Headers([('Content-Type','text/html; charset=utf-8'),('Cache-Control','no-store')]),(ROOT/'index.html').read_bytes())
 async with serve(handler,'0.0.0.0',int(os.environ.get('PORT',8765)),process_request=process_request,max_size=4096):
  print('Crown Clash server running');await loop()
if __name__=='__main__':asyncio.run(main())
