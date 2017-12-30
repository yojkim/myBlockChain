import hashlib
import json
import requests

from time import time
from uuid import uuid4
from urllib.parse import urlparse

from flask import Flask, jsonify, request

class BlockChain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

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

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n------------\n")

            if block['previous_hash'] != self.hash(last_block):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        neighbors = self.nodes
        new_chain = None
        
        max_length = len(self.chain)

        for node in neighbors:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

            if length > max_length and self.valid_chain(chain):
                max_length = length
                new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False

    @staticmethod
    # Hashes a block
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
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

    response = {
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

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a vaild list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message':      "New nodes have been added",
        'total_nodes':  list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message':      "Our chain was replaced",
            'new_chain':    blockchain.chain,
        }
    else:
        response = {
            'message':      "Our chain is authoritative",
            'chain':        blockchain.chain,
        }

    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)