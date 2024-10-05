from flask import Flask, render_template, request, jsonify
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
import io
import base64

# Constants for quantum voting
NUM_CANDIDATES = 4  # Number of candidates in the election
NUM_QUBITS = 2      # Number of qubits needed (2 qubits can represent 4 states, 00, 01, 10, 11)

# Function to encode votes using amplitude encoding into a quantum circuit
def amplitude_encoding(vote_vec, quantum_circuit):
    norm = np.linalg.norm(vote_vec)  # Normalize the vote vector
    normalized_vector = vote_vec / norm
    quantum_circuit.initialize(normalized_vector, [0, 1])  # Initialize the circuit with the normalized vector

# Flask app initialization
app = Flask(__name__)

# Homepage route
@app.route('/')
def index():
    return render_template('index.html')

# Voting route to trigger quantum voting simulation
@app.route('/vote', methods=['POST'])
def vote():
    # Get the votes from the form
    user_votes = request.json['votes']

    vote_counts = {'00': 0, '01': 0, '10': 0, '11': 0}  # Dictionary to store vote counts for each candidate (binary)

    for vote_choice in user_votes:
        # Create a new quantum circuit for each voter with 2 qubits and 2 classical bits
        qc = QuantumCircuit(NUM_QUBITS, NUM_QUBITS)

        # Create a one-hot encoded vote vector (e.g., [0, 1, 0, 0] for vote 01)
        vote_vector = [0] * NUM_CANDIDATES
        vote_vector[vote_choice] = 1

        # Encode the vote in the quantum circuit using amplitude encoding
        amplitude_encoding(vote_vector, qc)

        # Apply Hadamard gate to create superposition and entangle qubits
        qc.h(0)  # Apply Hadamard gate on the first qubit
        qc.cx(0, 1)  # Entangle the first qubit with the second

        # Measure the qubits and store the results in classical bits
        qc.measure([0, 1], [0, 1])

        # Use Aer's qasm_simulator to simulate the quantum circuit
        backend = Aer.get_backend('qasm_simulator')

        # Run the circuit and simulate with 1 shot (single vote measurement per voter)
        job = backend.run(qc, shots=1)
        result = job.result()
        counts = result.get_counts(qc)  # Get the result of the quantum measurement

        # Update vote counts based on the measurement outcomes
        for outcome in counts:
            vote_counts[outcome] += 1

    # Determine the winner by finding the candidate with the highest vote count
    winner = max(vote_counts, key=vote_counts.get)
    winner_candidate = int(winner, 2)  # Convert binary string to integer (candidate number)

    # Plot the histogram of the vote counts and encode it as a base64 image
    fig = plt.figure()
    plot_histogram(vote_counts)  # Plot the voting results as a histogram
    buf = io.BytesIO()  # Create an in-memory byte stream for the image
    plt.savefig(buf, format='png')  # Save the plot as a PNG image to the byte stream
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode()  # Convert the image to base64 format

    # Return the vote counts, winner information, and histogram image as a JSON response
    return jsonify({
        'vote_counts': vote_counts,
        'winner': winner_candidate,
        'votes': vote_counts[winner],
        'image': img_base64
    })

# Main function to start the Flask application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
