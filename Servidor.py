#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 12:19:50 2023

@author: alumno
"""
from multiprocessing.connection import Listener as Listen
from multiprocessing import Process, Manager 
from multiprocessing.connection import Client
import sys 
import traceback

def send_client_list(conn, clients):
    response = {
        "type": "client_list",
        "content": [{
            "address": v["address"],
            "authkey": v["authkey"],
            "port": v["port"]
            } for _,v in clients.items()]
    }
    conn.send(response)
                
def serve_client(conn, pid, clients):
    connected = True 
    print("Waiting for messages")
    while connected:
        try:
            m = conn.recv()
            print(f'received mesage: {m}: from {pid}')
            if  m["command"] == "quit":
                print("Adios al cliente😒 ")
                connected = False 
                conn.close()
            elif m["command"] == "list":
                send_client_list(conn, clients)
            else:
                print("Unknown command")
        except EOFError:
            print ('connection abruptly closed by client')
            connected = False
    del clients[pid]
    print (pid, 'connection closed')
    
def main(ip_adress):
    miListener = Listen(address=(ip_adress, 6000),
                  authkey=b'secret password server')
    with miListener as listener:
        print('listener starting')
        
        m= Manager()
        clients = m.dict()
        
        while True:
            print ('accepting conexions')
            try:
                conn = listener.accept()
                print ('connection accepted from', listener.last_accepted)
                client_info = conn.recv()
                pid = listener.last_accepted
                clients[pid]= client_info
                
                p= Process(target=serve_client, args=(conn, listener.last_accepted, clients))
                p.start()
            except Exception as e:
                traceback.print_exc()
                
        print('end server')
        
if __name__ == '__main__':
    ip_adress = '127.0.0.1'
    if len(sys.argv)>1:
            ip_address = sys.argv[1]
    main(ip_adress)