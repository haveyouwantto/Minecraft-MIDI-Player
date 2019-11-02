import asyncio
import glob
import json
import os
import sys
import threading
import time

import mido
import websockets


sub = json.dumps({
    "body": {
        "eventName": "PlayerMessage"
    },
    "header": {
        "requestId": "0ffae098-00ff-ffff-abbb-bbbbbbdf3344",
        "messagePurpose": "subscribe",
        "version": 1,
        "messageType": "commandRequest"
    }
})


def cmd(line):
    return json.dumps({
        "body": {
            "origin": {
                "type": "player"
            },
            "commandLine": line,
            "version": 1
        },
        "header": {
            "requestId": "ffff0000-0000-0000-0000-000000000000",
            "messagePurpose": "commandRequest",
            "version": 1,
            "messageType": "commandRequest"
        }
    })


def getChat(msg):
    return msg["body"]["properties"]["Message"]


def runmain(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as e:
        return e.value


def info(msg):
    return cmd("say \u00a7d" + str(msg))


def drawKeyboard(e,s=0):
    out=""
    i=s
    while i < e:
        if (i % 12 == 1 or i % 12 == 3 or i % 12 == 6 or i % 12 == 8 or i % 12 == 10):
            out += "\u00a70\u258F"
        else:
            out += "\u00a7f\u258F"
        i+=1
    return out

def midiDisplay(midimsg):
    out = '/titleraw @s actionbar {"rawtext":[{"text":"\u00a70'
    i = 0
    out += drawKeyboard(midimsg.note)
    out += "\u00a7c\u258F"
    out += drawKeyboard(128,midimsg.note+1)
    i+=1
    
    return cmd(out+'"}]}')


def play_note(midimsg):
    origin = midimsg.note - 66
    pitch = 2 ** (origin / 12)
    volume = midimsg.velocity / 128
    return cmd("execute @a ~ ~ ~ playsound note.harp @s ^0 ^ ^ " + str(volume) + " " + str(pitch))


class midiplayer(threading.Thread):
    def __init__(self, ws, mid):
        threading.Thread.__init__(self)
        self.ws = ws
        self.play = True
        self.mid = mido.MidiFile(mid)

    def run(self):
        for msg in self.mid.play():
            if msg.type == "note_on":
                print(msg)
                runmain(self.ws.send(play_note(msg)))
                runmain(self.ws.send(midiDisplay(msg)))
            if not self.play:
                break

    def stop(self):
        self.play = False


async def hello(ws, path):
    await ws.send(sub)

    sender = "外部"

    while True:
        data = await ws.recv()
        msg = json.loads(data)
        print(data)
        midiplayers = []
        if msg["header"]["messagePurpose"] == "event":

            if msg["body"]["eventName"] == "PlayerMessage" and msg["body"]["properties"]["Sender"] != sender:

                raw = getChat(msg)

                args = raw.split(" ")
                if raw.startswith(".midi"):
                    try:
                        midils = glob.glob("midis/*.mid")
                        if args[1] == "-ls":
                            for i in range(len(midils)):
                                await ws.send(info('[§c{0}§d] - {1}'.format(i, midils[i])))
                        elif args[1] == "-stop":
                            for i in midiplayers:
                                i.stop()
                        else:
                            arg1 = int(args[1])
                            if arg1 < len(midils):
                                await ws.send(info("正在加载 " + midils[arg1]))
                                player = midiplayer(ws, midils[arg1])
                                midiplayers.append(player)
                                player.start()
                            else:
                                await ws.send(info("文件不存在"))

                    except Exception as e:
                        await ws.send(info(str(e)))

        elif msg["header"]["messagePurpose"] == "commandResponse":
            pass


start_server = websockets.serve(hello, "localhost", 19111)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
