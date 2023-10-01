import random
import time
from vote import Snapshot
import re


if __name__ == "__main__":

    with open('data/wallet.txt', 'r') as f:
        private_keys = [i for i in [w.strip() for w in f] if i != '']
    with open('data/proxy.txt', 'r') as f:
        proxy = [i for i in [p.strip() for p in f] if i != '']
    with open('data/proposal.txt', 'r') as f:
        proposal = [i for i in [re.findall(r'\w+[^@]+', p.strip()) for p in f] if i != []]
        prop_adrs = [i for i in [p[1] for p in proposal] if i != '']



    if len(proxy)==0:
        input('You have not provided any proxies.\nPress ENTER to continue, in which case YOUR proxy IP will be used '
              'for all accounts')
        choice = 1
        proxy = None

    elif len(proxy) !=len(private_keys):
        input('The number of proxies does not match the number of keys.\nTo continue press ENTER, in this case 1 '
              'proxy will be used for all accounts')
        choice = 2
        proxy = proxy[0]

    else:
        choice = 3

    sleep_start = 3
    sleep_end = 10
    
    for i in range(0,len(private_keys)):
        if choice ==1:
            Snapshot(private_keys[i]).vote(proposal,prop_adrs)
            time.sleep(random.randrange(sleep_start,sleep_end))
        elif choice ==2:
            Snapshot(private_keys[i], proxy).vote(proposal,prop_adrs)
            time.sleep(random.randrange(sleep_start,sleep_end))

        else:
            Snapshot(private_keys[i],proxy[i]).vote(proposal,prop_adrs)
            time.sleep(random.randrange(sleep_start,sleep_end))


    exit()







