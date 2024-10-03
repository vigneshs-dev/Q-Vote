"""
This module implements a quantum voting system using Qiskit, simulating 10 voters and tallying votes.
"""

import random  # Standard library import

# Third-party library imports
import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram

# Constants
NUM_CANDIDATES = 4  # Representing 4 candidates (00, 01, 10, 11)
NUM_QUBITS = 2  # 2 qubits are enough to represent 4 candidates (2^2 = 4)
NUM_VOTERS = 10  # We simulate voting from 10 members

# Function to encode votes using amplitude encoding
def amplitude_encoding(vote_vec, quantum_circuit):
    """
    This function encodes the given vote vector using amplitude encoding.

    Args:
    vote_vec (list): The vote vector for the candidate.
    quantum_circuit (QuantumCircuit): The quantum circuit in which the vote will be encoded.
    """
    norm = np.linalg.norm(vote_vec)
    normalized_vector = vote_vec / norm
    quantum_circuit.initialize(normalized_vector, [0, 1])

# Simulate votes from 10 voters
vote_counts = {'00': 0, '01': 0, '10': 0, '11': 0}

for _ in range(NUM_VOTERS):
    # Create a new quantum circuit for each voter
    qc = QuantumCircuit(NUM_QUBITS, NUM_QUBITS)  # 2 qubits and 2 classical bits

    # Generate a random vote for one of the 4 candidates (candidate 0, 1, 2, or 3)
    vote_choice = random.randint(0, NUM_CANDIDATES - 1)

    # Create a vote vector for the selected candidate
    vote_vector = [0] * NUM_CANDIDATES  # Initialize all to 0
    vote_vector[vote_choice] = 1  # Set the chosen candidate's index to 1

    # Encode the vote in the quantum circuit
    amplitude_encoding(vote_vector, qc)

    # Entangle qubits using Hadamard and CNOT gates
    qc.h(0)  # Apply Hadamard gate to the first qubit
    qc.cx(0, 1)  # Apply CNOT gate to entangle the qubits

    # Measure the qubits to retrieve results after sending them to Charlie
    qc.measure([0, 1], [0, 1])

    # Use Aer's qasm_simulator
    backend = Aer.get_backend('qasm_simulator')

    # Transpile and run the circuit on the qasm simulator
    job = backend.run(qc, shots=1)  # Only 1 shot per voter (since each voter votes once)
    result = job.result()

    # Get counts for each outcome (binary representation of the candidate choices)
    counts = result.get_counts(qc)

    # Update the vote counts
    for outcome in counts:
        vote_counts[outcome] += 1

# Output the final vote counts
print("Final Vote Counts:", vote_counts)

# Determine the winner by selecting the candidate with the highest votes
winner = max(vote_counts, key=vote_counts.get)
print(f"The winner is candidate {int(winner, 2)} with {vote_counts[winner]} votes.")

# Visualize the results using a histogram
plot_histogram(vote_counts)
plt.show()
