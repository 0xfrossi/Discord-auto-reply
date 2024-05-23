import websocket
import json
import threading
import time
from http.client import HTTPSConnection
from collections import deque 
import re
import requests
import openai
import random


def send_js_req(ws, req):
    ws.send(json.dumps(req))

def recive_js_resp(ws):
    resp= ws.recv()
    if resp:
        return json.loads(resp)
    
def heartbeat(interval, ws):
    print("heartbeat begin")
    while True:
        time.sleep(interval)
        hb_js={
           "op":1,
            "d": "null"
        }
        send_js_req(ws,hb_js )
        print("Heartbeat sent!")

def get_connection():
    return HTTPSConnection("discord.com", 443)

def send_message(conn, channel_id, message_data):
    try:
        conn.request("POST", f"/api/v10/channels/{channel_id}/messages", message_data, header_data)
        resp = conn.getresponse()
        print("status: "+ str(resp.status))

        if 199 < resp.status < 300:
            print("Message sent!")
        else:
            print("Message not sent. Response:")
            print("Response Status: " + str(resp.status))
            print("Response Reason: " + resp.reason)
            response_data = resp.read().decode('utf-8')
            print("Response Body:")
            print(response_data)
    except Exception as e:
        print(f"Error sending message: {e}")


def valid_content(input_string):
    regex = r'^(?!^ *$)(?!^~$)(?!^\d+$)[\d\s\w.,!?;:\'"()-]+$'
    if re.match(regex, input_string):
        return True
    else:
        return False

#Never tested
def create_gpt_reply(context, buffer):
    openai.api_key=""
    url = ""
    headers = {
        "Authorization": "",
        "Content-Type": "application/json",
    }
    prompt="Act like a xxxxxxxxxxxx\n"
    
    input_tokens=""
    if type(context)==deque:
        while not len(buffer)==0:
            content= buffer.pop()
            input_tokens += content.get("content") + "\n"
    else:
        input_tokens=context

    data = {
        "prompt": prompt + input_tokens,
        "max_tokens": 20 
    }
    try:
        #response = requests.post(url, headers=headers, json=data)
        #result  = response.json()
        # = result["choices"][0]["text"]
        risposta = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=[{"role":"user", "content": prompt + input_tokens}],
        #max_tokens=20  
        )
        risposta_text = risposta.choices[0].message.content   
        print("Reply created form gpt")
    except  Exception as error:
        print(error)
    return risposta_text


def print_random_mess(buff):
    while True:
        if  buff.maxlen==len(buff) :
                reply= create_gpt_reply(buff)
                        
                message_data = json.dumps({"content": reply})
                conn = get_connection()
                send_message(conn, text[3], message_data)
                conn.close()
                print("Random Message Sent from 'print_random_mess': "+ reply)  
        time.sleep(60)     


#buffer= deque(maxlen=15)

###############################
#   END FUNCTIONS DEFINITION   #
###############################

# Load the parameters
with open("info.txt", "r") as file:
    text = file.read().splitlines()

ws= websocket.WebSocket()
ws.connect("wss://gateway.discord.gg/?v=10&encoding=json")
event= recive_js_resp(ws)
heartbeat_interval= event['d']['heartbeat_interval'] / 1000

threading._start_new_thread(heartbeat, (heartbeat_interval, ws))

token=text[1]
group_id=text[2]
channel_id=text[3]
my_user=text[0]
payload ={
    'op': 2,
    'd': {
        "token":token,
        'properties': {   #modify these with your setting
            '$op': 'windows',
            '$browser': 'firefox',
            "$device": 'pc',
        },      
    },
}

send_js_req(ws, payload)

header_data = {
    "content-type": "application/json",
    "user-id": my_user,
    "authorization": token,
    "host": "discord.com",
    "referrer": group_id
}

print("Messages will be sent to " + header_data["referrer"] + ".")

#raw sniff of all messages sent in the channel and filters only the interested for an automatic reply 
# this code intercepts only some messages 
while True:
    event= recive_js_resp(ws)
    if event is not None and event['d'] is not None:
        try:
                #with open("jsDumps.txt", 'a') as file:
            if 'd' in event and 'channel_id' in event['d'] and event['d']['channel_id'] == channel_id and 'content' in event['d']:

                content=event['d']['content']
                check=valid_content(content)

                if not event['d']['referenced_message'] and check:
                    print(f"{event['d']['author']['username']}: {event['d']['content']}")
                    
                    #file.write(f"{event['d']['author']['username']}: {event['d']['content']} => \n")
                                        
                    #buffer.append({"author": event['d']['author']['username'], "content": content, "reply_id_mes": None })
                    #print(buffer)
                    reply=None
                    second=["","ser","mate","bro", "fam", "man"]
                    i=random.randint(0,5)
                    salut=["hey","yoo","hello","hi", "yo", "yoo", "yoyo"]
                    #blacklist= event['d']['author']['username']=="xxx" or event['d']['author']['username']=="xxx"
                    blacklist=[] # I used it to blacklist some messages sent by specific users that I didnt want generate a reply

                    if  "sup"  in content.lower().split() and not blacklist:
                        reply="Sup "+ second[i]
                    
                    if ("i'm back" in content.lower() or "im back" in content.lower() ) and not blacklist:
                        reply="Welcome back "+ second[i]

                    if ( "gm"  in content.lower().split() or "gmgm"  in content.lower()) and not blacklist  :
                        reply="GM "+ second[i]

                    elif  ("gn" in content.lower().split() or "gngn" in content.lower()) and not blacklist:
                        reply="GN "+ second[i]

                    elif any(keyword in content.lower().split() for keyword in salut) and not blacklist:
                        
                        j=random.randint(0,3)
                        reply=salut[j] + " "+ second[i]
                        print(reply)

                    if not reply==None:
                        message_data = json.dumps({"content": reply,                        
                                        "message_reference": {
                                                "message_id": event['d']['id'],                                 
                                            },
                                    })
                        time.sleep(14)
                        conn = get_connection()
                        send_message(conn, channel_id, message_data)
                        conn.close()
                        print("Message Sent!")        
                elif event['d']['referenced_message'] and check:
                    print(f"{event['d']['author']['username']}: {event['d']['content']} || reply at: {event['d']['referenced_message']['author']['username']}")
 
 #debugging and testing stuff
                    
                    #buffer.append({"author": event['d']['author']['username'], "content": content, "reply_id_mes":  event['d']['message_reference']['message_id'] })
                    #print(buffer)

                    #file.write(f"{event['d']['author']['username']}: {event['d']['content']} || reply at: {event['d']['referenced_message']['author']['username']} => \n")

                #file.write(json.dumps(event['d'], indent=2)+"\n")
                #file.write("---- END MESSAGE ----\n")

                #if event['d']['referenced_message']['author']['username']== my_user:
                    #reply=create_gpt_reply(content)
                    # message_data = json.dumps({"content": reply,                        
                    #                 "message_reference": {
                    #                         "message_id": event['d']['message_reference']['message_id'],   }, })
                    # conn = get_connection()
                    # send_message(conn, text[3], message_data)
                    #  conn.close()
                    #  print("Message in reply sent: "+reply)
                         
            else: pass
               
            #op_code=event('op')
            #if op_code==11:
                #print("Heartbeat received")
        except  Exception as error:
           #print(error)
           pass
    #threading._start_new_thread(print_random_mess,(buffer,))     

# [mentions]["username"]  when you want to retrieve the user mentioned with @username ("referenced_message":"None")
# ['referenced_message'] full

    