import hashlib
import json

from textwrap import detent
from time import time
from uuid import uuid4

from flask import Flask, jsonify, request

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

    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    # Hashes a block
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:4] == "0000"

    @property
    # Returns the last block in the chain
    def last_block(self):
        return self.chain[-1]

# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = BlockChain()


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined new coin.
    blockchain.new_transaction(
        sender      = "0",
        recipient   = node_identifier,
        amount      = 1
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    respose = {
        'message':          "New Block Forged",
        'index':            block['index'],
        'transactions':     block['transactions'],
        'proof':            block['proof'],
        'previous_hash':    block['previous_hash'],
    }

    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'receipent', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['receipent'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain':    blockchain.chain,
        'length':   len(blockchain.chain),
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)