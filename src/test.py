# Import necessary libraries
import math
import hashlib
import random
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.compiler import transpile

# Voter Class (Alice)
class Voter:
    def __init__(self, voter_id, secret_key_KAB, secret_key_KAC):
        self.voter_id = voter_id  # Voter ID assigned by Bob
        self.secret_key_KAB = secret_key_KAB  # Secret key shared with Bob
        self.secret_key_KAC = secret_key_KAC  # Secret key shared with Charlie
        self.hash_id = self.create_hash_id()  # Hash of voter ID for anonymity
    
    def create_hash_id(self):
        """Creates a hash ID for voter using their voter ID."""
        return hashlib.sha256(self.voter_id.encode()).hexdigest()
    
    def encode_vote(self, vote):
        """Encode the vote using quantum mechanics, superposition, and entanglement."""
        total_approvals = sum(vote)  # Count total approvals
        if total_approvals == 0:
            print(f"{self.voter_id} has not approved any candidates, assigning default vote.")
            # Assign a default vote (e.g., approve the first candidate)
            vote[0] = 1
            total_approvals = 1  # Update total approvals to prevent division by zero
        
        # Normalize the vote array
        n = 1 / math.sqrt(total_approvals)  # Normalization factor
        normalized_vote = [i * n for i in vote]
        
        # Initialize a 2-qubit quantum circuit (since there are 4 candidates)
        qc = QuantumCircuit(2, 2, name='Vote')  # 2 classical bits for measurement
        qc.initialize(normalized_vote, [0, 1])
        
        # Measure the qubits and store the result in classical bits
        qc.measure([0, 1], [0, 1])  # Measure qubits and store in classical bits 0 and 1
        
        return qc
    
    def sign_vote(self, vote_circuit):
        """Signs the vote using a signature method."""
        sign_circuit = QuantumCircuit(2, name='Signature')
        sign_circuit.z(0)
        sign_circuit.x(1)
        
        # Use compose method to combine circuits
        signed_vote = vote_circuit.compose(sign_circuit)
        return signed_vote

# Tallyman Class (Bob)
class Tallyman:
    def __init__(self):
        self.voter_database = {}  # Store hash IDs and votes

    def issue_voter_id(self, voter_name):
        """Issue a unique voter ID and generate secret keys."""
        voter_id = f"{voter_name}_{random.randint(1000,9999)}"
        secret_key_KAB = bin(random.getrandbits(4))[2:].zfill(4)
        secret_key_KAC = bin(random.getrandbits(4))[2:].zfill(4)
        return voter_id, secret_key_KAB, secret_key_KAC

    def store_vote(self, hash_id, vote_circuit):
        """Store the vote in the database."""
        self.voter_database[hash_id] = vote_circuit

    def tally_votes(self):
        """Tally votes and return the results."""
        results = {0: 0, 1: 0, 2: 0, 3: 0}  # Initialize counts for candidates 1 to 4

        # Initialize the Aer simulator
        simulator = AerSimulator()

        # Count the votes based on the stored circuits
        for hash_id, vote_circuit in self.voter_database.items():
            # Transpile the circuit for the simulator
            compiled_circuit = transpile(vote_circuit, simulator)

            # Run the circuit once to get measurement results
            sim_result = simulator.run(compiled_circuit, shots=1).result()  # Run with 1 shot for a single outcome
            counts = sim_result.get_counts()

            # Count approvals based on the measured results
            for outcome, count in counts.items():
                candidate_index = int(outcome, 2)  # Convert binary string to integer index
                if candidate_index < 4:  # Ensure we only consider the first 4 candidates
                    results[candidate_index] += 1  # Increment the vote for the candidate

        return results

# Scrutineer Class (Charlie)
class Scrutineer:
    def __init__(self, secret_key_KAC):
        self.secret_key_KAC = secret_key_KAC  # Secret key shared with Voter (Alice)
    
    def verify_vote(self, hash_id, voting_db):
        """Verify if a vote exists in the database using hash ID."""
        return hash_id in voting_db

# Function to determine the winner
def determine_winner(vote_counts):
    """Determine the winner based on vote counts."""
    winner = max(vote_counts, key=vote_counts.get)
    return winner, vote_counts[winner]

# Main Voting Program
def main():
    # Initialize Bob (Tallyman) and Charlie (Scrutineer)
    bob = Tallyman()
    
    # Assuming Charlie has KAC to verify
    secret_key_KAC = bin(random.getrandbits(4))[2:].zfill(4)
    charlie = Scrutineer(secret_key_KAC)
    
    # List to hold voters' names
    voters = ["Alice", "Bob", "Charlie", "David", "Eve"]
    
    for voter_name in voters:
        # Simulate each voter casting their vote
        voter_id, secret_key_KAB, secret_key_KAC = bob.issue_voter_id(voter_name)
        alice = Voter(voter_id, secret_key_KAB, secret_key_KAC)
        
        # Randomly generate a vote: 1 means approval, 0 means disapproval
        # For simplicity, we randomly generate votes for 4 candidates (1s and 0s)
        alice_vote = [random.randint(0, 1) for _ in range(4)]
        
        # Alice encodes her vote into quantum circuit
        vote_circuit = alice.encode_vote(alice_vote)
        
        # Alice signs her vote
        signed_vote = alice.sign_vote(vote_circuit)
        
        # Store the vote in Bob's (Tallyman) database before verification
        bob.store_vote(alice.hash_id, signed_vote)
        
        # Verify if the vote exists in the database
        if charlie.verify_vote(alice.hash_id, bob.voter_database):
            print(f"Vote verified by Charlie for voter hash ID: {alice.hash_id}")
        else:
            print(f"Vote could not be verified by Charlie.")
    
    # In your main function, after tallying votes:
    results = bob.tally_votes()
    print("Vote Counts:", results)

    # Determine the maximum votes and find winners
    max_votes = max(results.values())
    winners = [candidate for candidate, count in results.items() if count == max_votes]

    # Announce winners
    if len(winners) == 1:
        print(f"The winner is Candidate {winners[0]} with {max_votes} votes.")
    else:
        print(f"It's a tie! Candidates {', '.join(map(str, winners))} have the highest votes with {max_votes} votes.")


# Run the program
if __name__ == "__main__":
    main()
