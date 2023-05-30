import requests
import json
import time
from eth_utils import (
    keccak,
)
from eth_abi import abi
from web3.auto import w3
from pyuseragents import random as random_useragent


class Snapshot(object):



    def __init__(self,private_key, proxy = None):

        if proxy != None:

                self.proxy = {'https': f'http://{proxy}', 'http': f'http://{proxy}'}
        
        else:

            self.proxy = proxy

        self.web3 = w3
        self.private_key = private_key
        self.address = (self.web3.eth.account.from_key(private_key)).address
        self.useragent = random_useragent()





    def sign_vote(self,prop_d, n =10):

        try:

            deadline = int(time.time())

            prop = self.web3.to_bytes(hexstr=prop_d[1])



            message = {
                "primaryType": "Vote",
                "types": {
                    "Vote": [
                        {"name": "from", "type": "address"},
                        {"name": "space", "type": "string"},
                        {"name": "timestamp", "type": "uint64"},
                        {"name": "proposal", "type": "bytes32"},
                        {"name": "choice", "type": "uint32"},
                        {"name": "reason", "type": "string"},
                        {"name": "app", "type": "string"},
                        {"name": "metadata", "type": "string"}

                    ],
                    "EIP712Domain": [{"name": "name", "type": "string"},
                                     {"name": "version", "type": "string"}]
                    },

                "domain": {"name": "snapshot", "version": "0.1.4"},
                "message": {

                    "app": "snapshot", "choice": 1, "from": self.address, "metadata": "{}", "proposal": prop,
                    "reason": "",
                    "space": prop_d[0], "timestamp": deadline

                }

            }

            domain_type_hash = keccak(text='EIP712Domain(string name,string version)')
            name = message['domain']['name']
            version = message['domain']['version']

            domain_instance = abi.encode(
                ['bytes32', 'bytes32', 'bytes32'],
                [domain_type_hash, keccak(text=name), keccak(text=version)],
            )
            domain_hash = keccak(domain_instance)

            cool_struct_type_hash = keccak(
                text='Vote(address from,string space,uint64 timestamp,bytes32 proposal,uint32 choice,string reason,string app,string metadata)')
            From = message['message']['from']
            space = message['message']['space']
            timestamp = message['message']['timestamp']
            proposal = message['message']['proposal']
            choice = message['message']['choice']
            reason = message['message']['reason']
            app = message['message']['app']
            metadata = message['message']['metadata']

            cool_struct_instance = abi.encode(
                ['bytes32', 'address', 'bytes32', 'uint64', 'bytes32', 'uint32', 'bytes32', 'bytes32', 'bytes32'],
                [cool_struct_type_hash, From, keccak(text=space), timestamp, proposal, choice, keccak(text=reason),
                 keccak(text=app), keccak(text=metadata)]
            )
            cool_struct_hash = keccak(cool_struct_instance)

            preamble = b'\x19'
            version = b'\x01'

            message_hash = keccak(preamble + version + domain_hash + cool_struct_hash)

            signature = self.web3.eth.account.signHash(message_hash, private_key=self.private_key).signature.hex()
            message.pop("primaryType")
            message["types"].pop("EIP712Domain")
            message["message"]["proposal"] = prop_d[1]

        except requests.exceptions.ProxyError as e:

            if n <=0:
                return

            print(f"\033[31mPossibly a wrong proxy format was entered. Check: login,password@ip,port\nAccount {self.address} error SIGN vote {prop_d[0]} : {e}\nLets try {n} more time")

            time.sleep(5)
            n-=1
            return self.sign_vote(prop_d,n)

        except Exception as e:
            if n <=0:
                return
            print(f"\033[31mAccount {self.address} error SIGN vote {prop_d[0]} : {e}\nLets try {n} more time")

            time.sleep(5)
            n-=1
            return self.sign_vote(prop_d,n)

        else:

            return signature,message



    def check_vote(self,proposal,n=5):

        try:
            url = 'https://hub.snapshot.org/graphql'

            headers = {
                'accept': '*/*',
                'content-type': 'application/json',
                'user-agent': self.useragent
            }

            data = json.dumps({"operationName":"Votes","variables":{"voter":self.address,"proposals":proposal},"query":"query Votes($voter: String!, $proposals: [String]!) {\n  votes(where: {voter: $voter, proposal_in: $proposals}) {\n    proposal {\n      id\n    }\n }\n}"})

            r = requests.post(url, headers=headers, data=data,
                              proxies=self.proxy).json()

            vote = [i for i in [v['proposal']['id'] for v in r['data']['votes']]]

            return vote



        except Exception as e:

            if n <= 0:
                return proposal

            print(f'\033[31mAccount {self.address} error check_vote : {e}')

            time.sleep(5)

            n -= 1

            return self.check_vote(proposal,n)


    def send_vote(self,sign,message,n ={"error":5,"failed to check voting power":3}):

        try:

            url = 'https://seq.snapshot.org/'

            headers = {
                'accept': 'application / json',
                'content-type': 'application/json',
                'user-agent': self.useragent
            }

            data = json.dumps({"address":self.address,"sig":str(sign),"data": message})

            r = requests.post(url, headers=headers, data=data,
                                  proxies=self.proxy)
            if r.status_code ==200:
                time.sleep(5)
                return print(f'\033[32mAccount {self.address} vote {message["message"]["space"]} {message["message"]["proposal"]}')
            else:
                print(f'\033[31mAccount {self.address} error vote {message["message"]["space"]} {message["message"]["proposal"]}: {r.text}')
                time.sleep(5)

                if "error_description" in r.json() and r.json()["error_description"] =="failed to check voting power":

                    n["failed to check voting power"] -=1
                    if n["failed to check voting power"] <=0:
                        return
                    else:
                        return self.send_vote(sign, message, n)
                elif "error_description" in r.json() and r.json()["error_description"] =="no voting power":
                    return
                else:
                    n["error"] -=1
                    return self.send_vote(sign, message, n)



        except Exception as e:
            if n["error"] <=0:
                return
            print(f'\033[31mAccount {self.address} error for send vote {message["message"]["space"]} {message["message"]["proposal"]}: {e}')
            time.sleep(5)
            n["error"] -=1
            return self.send_vote(sign,message, n)







    def vote(self,proposal,prop_hex):




        vote = self.check_vote(prop_hex)


        for prop in proposal:

            if prop[1] in vote:
                print(f'\033[32mAccount {self.address} already vote {prop[0]} {prop[1]}')
                continue

            sign,message = self.sign_vote(prop)
            if message ==None:

                return

            self.send_vote(sign,message)

        return


