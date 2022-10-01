from microWebSrv import MicroWebSrv
import ujson
import sensorization

ws = []
s = sensorization # Es el objecto de sensorización

def sendData(height, accel):
  global ws
  obj = {
    "type": "data",
    "data": {
      "height": height,
      "accel": accel
    }
  }

  for i, s in enumerate(ws):
    if not s.IsClosed():
      s.SendText(ujson.dumps(obj))
    else:
      del ws[i]

def sendInitialData(ws):
  obj = {
    "type": "initial",
    "data": {
      "threshold_height": s.thresholds[s.alt_sensor],
      "threshold_accel": s.thresholds[s.acel_sensor],
      "hitted": s.hit,
      "historic": s.historial
    }
  }

  ws.SendText(ujson.dumps(obj))
  

def sendHit(date, accel):
  global ws

  obj = {
    "type": "hit",
    "data": {"date": date, "accel": accel }
  }
  for i, j in enumerate(ws):
    if not j.IsClosed():
      j.SendText(ujson.dumps(obj))
    else:
      del ws[i]

def _acceptWebSocketCallback(webSocket, httpClient) :
  print("WS ACCEPT")
  ws.append(webSocket)
  webSocket.RecvTextCallback   = _recvTextCallback
  webSocket.RecvBinaryCallback = _recvBinaryCallback
  webSocket.ClosedCallback     = _closedCallback

  sendInitialData(webSocket)

def _recvTextCallback(webSocket, msg) :
  print("WS RECV TEXT : %s" % msg)
  if msg == "resetHit":
    s.reset_hit_procedure()
  else:
    json = ujson.loads(msg)
    if json["type"] == "config":
      print(json["data"]["accel"], " ", json["data"]["height"])
      s.update_thresholds(json["data"]["height"], json["data"]["accel"])

def _recvBinaryCallback(webSocket, data) :
  print("WS RECV DATA : %s" % data)

def _closedCallback(webSocket) :
  print("WS CLOSED")
  for i, s in enumerate(ws):
    if not s.IsClosed():
      if s == webSocket:
        del ws[1]
        print("ws eliminado")
    else:
      del ws[i]
      print("encontrado ws muerto")

def server(sensorization_instance):
  global s
  s = sensorization_instance
  mws = MicroWebSrv()
  mws.MaxWebSocketRecvLen     = 256                      # Default is set to 1024
  mws.WebSocketThreaded       = True                    # WebSockets without new threads
  mws.AcceptWebSocketCallback = _acceptWebSocketCallback
  mws.Start(threaded=True)