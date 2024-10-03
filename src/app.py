from flask import Flask, render_template, jsonify
import random
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
import io
import base64

# Constants for quantum voting
NUM_CANDIDATES = 4
NUM_QUBITS = 2
NUM_VOTERS = 10

# Function to encode votes using amplitude encoding
def amplitude_encoding(vote_vec, quantum_circuit):
    norm = np.linalg.norm(vote_vec)
    normalized_vector = vote_vec / norm
    quantum_circuit.initialize(normalized_vector, [0, 1])

# Flask app initialization
app = Flask(__name__)

# Homepage route
@app.route('/')
def index():
    return render_template('index.html')

# Voting route to trigger quantum voting simulation
@app.route('/vote')
def vote():
    vote_counts = {'00': 0, '01': 0, '10': 0, '11': 0}

    for _ in range(NUM_VOTERS):
        # Create a new quantum circuit for each voter
        qc = QuantumCircuit(NUM_QUBITS, NUM_QUBITS)

        # Generate a random vote for one of the 4 candidates
        vote_choice = random.randint(0, NUM_CANDIDATES - 1)

        # Create a vote vector
        vote_vector = [0] * NUM_CANDIDATES
        vote_vector[vote_choice] = 1

        # Encode the vote in the quantum circuit
        amplitude_encoding(vote_vector, qc)

        # Entangle qubits
        qc.h(0)
        qc.cx(0, 1)

        # Measure the qubits
        qc.measure([0, 1], [0, 1])

        # Use Aer's qasm_simulator
        backend = Aer.get_backend('qasm_simulator')

        # Run the circuit
        job = backend.run(qc, shots=1)
        result = job.result()
        counts = result.get_counts(qc)

        # Update vote counts
        for outcome in counts:
            vote_counts[outcome] += 1

    # Determine the winner
    winner = max(vote_counts, key=vote_counts.get)
    winner_candidate = int(winner, 2)

    # Plot the histogram and encode it as a base64 image
    fig = plt.figure()
    plot_histogram(vote_counts)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode()

    # Return the result as JSON
    return jsonify({
        'vote_counts': vote_counts,
        'winner': winner_candidate,
        'votes': vote_counts[winner],
        'image': img_base64
    })

if __name__ == '__main__':
    app.run(debug=True)
