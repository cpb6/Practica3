#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 12:43:02 2023

@author: alumno
"""

from multiprocessing.connection import Client
from time import sleep

from multiprocessing.connection import Listener
from multiprocessing import Process, Manager
import sys, os


def is_myself(selected_client, my_info):
    return selected_client["address"] == my_info["address"] and selected_client["port"] == my_info["port"]


def print_help():
    print("""
          list - retrieve a list of all connected users
          quit - exit
          message # message_to_send - sends a message to an specific client.
              Ex: message 2 Hello my friend! - Sends the message 'Hello my friend!' to the user number 2
          upload # filename - sends a file to an user
              Ex: upload 3 book.pdf - send the file 'book.pdf' to the user number 3
          """)

def client_listener(info):
    print(f"Openning listener at {info}")
    cl = Listener(address=(info['address'], info['port']),
                  authkey=info['authkey'])
    print ('...............client Listener starting')
    print('................accepting conexions')
    while True:
        conn = cl.accept()
        print ('...........connection accept from', cl.last_accepted)
        m = conn.recv()
        from_ip = m["from"]["address"]
        from_port = m["from"]["port"]
        if m["command"] == "message":
            message = m["message"]
            print (f'..........message received from {from_ip} at port {from_port}: {message}')
        elif m["command"] == "upload":
            filename = m["filename"]
            content = m["content"]
            print (f'..........file received from {from_ip} at port {from_port}: {filename}')
            if not os.path.exists("files"):
                os.makedirs("files")
            file = open(f"files/{filename}", "wb")
            file.write(content)
            file.close()
        else:
            print (f'..........received an unknown command ({m["command"]}) from {from_ip} at port {from_port}')
        
def clearList(myList):
    while len(myList) > 0:
        myList.pop()
        
def send_direct_message(client_info, message, from_info):
    with Client(address=(client_info["address"], client_info["port"]), 
                authkey=client_info["authkey"]) as conn:
        frame = {
            "command": "message",
            "message": message,
            "from": from_info
            }
        conn.send(frame)
        conn.close()
def send_file(client_info, filename, from_info):
    if not os.path.isfile(filename):
        print("File does not exists")
        return
    file = open(filename, "rb")
    content = file.read()
    file.close()
    with Client(address=(client_info["address"], client_info["port"]), 
                authkey=client_info["authkey"]) as conn:
        frame = {
            "command": "upload",
            "content": content,
            "filename": filename,
            "from": from_info
            }
        conn.send(frame)
        conn.close()
        
def server_responses(conn, client_list):
    connected = True
    while connected:
        try:
            print("Receiving directly from server")
            server_response = conn.recv()
            if server_response["type"]=="client_list":
                clearList(client_list)
                server_list= server_response["content"]
                print()
                for i in range(len(server_list)):
                    client= server_list[i]
                    client_list.append(client)
                    print(f"{i} - address {client['address']} port {client['port']}")
            else:
                print(server_response)
        except:
            print("Cerrando conexion con el servidor")
            connected = False

def main(server_address, info):
    print('trying to connect')
    manager = Manager()
    client_list = manager.list()
    with Client(address=(server_address, 6000), 
                authkey=b'secret password server') as conn:
        cl = Process(target=client_listener, args=(info,))
        cl.start()
        c2 = Process(target=server_responses, args=(conn,client_list))
        c2.start()
        conn.send(info)
        connected = True 
        while connected:
            value = input("send command ('help' to list all commands)")
            if value == "list":
                frame = {
                    "command":"list"
                    }
            elif value == "quit":
                frame = {
                    "command":"quit"
                    }
                connected = False
            elif value == "cache":
                print(client_list)
                continue
            elif value == "help":
                print_help()
                continue
            # message 3 Hola que tal?
            elif value == "message" or value.startswith("message "):
                try:
                    _ , client_choice , message= value.split(" ", 2)
                    client_number = int(client_choice)
                    client = client_list[client_number]
                    if is_myself(client, info):
                        print("Cannot send messae to yourself")
                        continue
                    message_process= Process(target=send_direct_message, args= (client, message, info))
                    message_process.start()
                except:
                    print("Message error. Is the format correct?")
                continue
            elif value == "upload" or value.startswith("upload "):
                try:
                    _, client_choice ,filename = value.split(" ", 2)
                    client_number = int(client_choice)
                    client = client_list[client_number]
                    if is_myself(client, info):
                        print("Cannot send messae to yourself")
                        continue
                    file_process= Process(target=send_file, args= (client, filename, info))
                    file_process.start()
                except:
                    print("Upload error. Is the format correct?")
                continue
            else:
                print("Command not found")
                continue
            conn.send(frame)
            print("Message sent")
        sleep(1)
        c2.terminate()
        cl.terminate()
        
    print("end client")

if __name__== '__main__':
    server_address = '127.0.0.1'
    client_address ='127.0.0.1'
    client_port = 6001
    
    if len(sys.argv) >1:
        client_port = int(sys.argv[1])
    if len(sys.argv) >2:
        client_address = sys.argv[2]
    if len(sys.argv) > 3:
        server_address = sys.argv[3]
    info = {
        'address' : client_address,
        'port' : client_port,
        'authkey' : b'secret client server'
    }
    main(server_address, info)
            