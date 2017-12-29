import hashlib
import json
from time import time

class BlockChain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    # Creates a new block and adds it to the chain
    def new_block(self, proof, previous_hash=None):
        block = {
            'index':            len(self.chain) + 1,
            'timestamp':        time(),
            'transactions':     self.current_transactions,
            'proof':            proof,
            'previous_hash':    previous_hash or self.hash(self.chain[-1]),
        }

        self.current_transactions = []

        self.chain.append(block)
        return block

    # Adds a new transactions to the list of transactions
    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'sender':       sender,
            'recipient':    recipient,
            'amount':       amount,
        })

        return self.last_block['index'] + 1

    @staticmethod
    # Hashes a block
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    # Returns the last block in the chain
    def last_block(self):
        return self.chain[-1]
        pass