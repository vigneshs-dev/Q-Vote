from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Constants for quantum voting
NUM_CANDIDATES = 4  # Number of candidates in the election
NUM_QUBITS = 2      # Number of qubits needed (2 qubits can represent 4 states, 00, 01, 10, 11)

# Create a database connection
def get_db_connection():
    conn = sqlite3.connect('votes.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create tables if they don't exist
def create_tables():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate INTEGER NOT NULL)''')
    conn.commit()
    conn.close()

create_tables()

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already taken. Please try a different one."
    
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('vote'))
        else:
            return "Invalid credentials. Please try again."

    return render_template('login.html')

# Voting route where users can vote for a candidate
@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'username' not in session:
        return redirect(url_for('login'))

    current_vote_counts = []  # To store current vote counts

    if request.method == 'POST':
        candidate = request.form['candidate']  # Get the selected candidate from the form

        # Insert the vote into the database
        conn = get_db_connection()
        conn.execute('INSERT INTO votes (candidate) VALUES (?)', (candidate,))
        conn.commit()

        # Retrieve all votes from the database for debugging
        current_vote_counts = conn.execute('SELECT candidate, COUNT(*) as count FROM votes GROUP BY candidate').fetchall()
        conn.close()

        # Debug: Print out current vote counts from the database
        print("Current Vote Counts after Voting:")
        for row in current_vote_counts:
            print(f"Candidate {row['candidate']}: {row['count']} votes")

        # After vote submission, redirect to results page
        return redirect(url_for('results'))

    # If GET request, retrieve current vote counts to display on voting page
    conn = get_db_connection()
    current_vote_counts = conn.execute('SELECT candidate, COUNT(*) as count FROM votes GROUP BY candidate').fetchall()
    conn.close()

    return render_template('vote.html', current_vote_counts=current_vote_counts)

# Results page where the quantum voting simulation occurs
@app.route('/results')
def results():
    conn = get_db_connection()

    # Retrieve all votes from the database
    vote_counts_from_db = conn.execute('SELECT candidate, COUNT(*) as count FROM votes GROUP BY candidate').fetchall()
    conn.close()

    # Create a vote_distribution array based on user votes (initialize for 4 candidates)
    vote_distribution = [0] * NUM_CANDIDATES  # Ensuring the size matches NUM_CANDIDATES
    for row in vote_counts_from_db:
        candidate_index = int(row['candidate'])
        
        # Ensure the candidate index is valid
        if 0 <= candidate_index < NUM_CANDIDATES:
            vote_distribution[candidate_index] = row['count']
        else:
            print(f"Warning: Candidate index {candidate_index} is out of bounds.")

    # Simulate quantum voting with the retrieved vote distribution
    return_data = quantum_voting(vote_distribution)

    # Find the candidate(s) with the highest vote count
    winners = return_data['winner']
    if not isinstance(winners, list):
        winners = [winners]  # Ensure winners is a list, even if only one winner

    max_votes = return_data['votes']

    return render_template('results.html', vote_counts=vote_counts_from_db, winners=winners, max_votes=max_votes, image=return_data['image'])

# Quantum voting function to simulate voting
def quantum_voting(vote_distribution):
    """
    Simulates the quantum voting based on the provided vote distribution.
    
    Args:
        vote_distribution (list): A list containing the count of votes for each candidate.

    Returns:
        dict: A dictionary containing:
            - vote_counts: A dictionary with the counts of each vote outcome.
            - winner: The winner candidate based on the highest vote count.
            - votes: The total number of votes received by the winner.
            - image: Base64-encoded image of the vote distribution histogram.
    """
    vote_counts = {'00': 0, '01': 0, '10': 0, '11': 0}  # Store vote counts for each candidate (binary)

    for candidate_index in range(NUM_CANDIDATES):
        candidate_vote_count = vote_distribution[candidate_index]  # Get the vote count for this candidate

        for _ in range(candidate_vote_count):
            # Create a new quantum circuit for each voter's vote
            qc = QuantumCircuit(NUM_QUBITS, NUM_QUBITS)

            # Create a one-hot encoded vote vector (e.g., [0, 1, 0, 0] for vote 01)
            vote_vector = [0] * NUM_CANDIDATES
            vote_vector[candidate_index] = 1

            # Encode the vote in the quantum circuit using amplitude encoding
            amplitude_encoding(vote_vector, qc)

            # Apply Hadamard gate to create superposition and entangle qubits
            qc.h(0)  # Apply Hadamard gate on the first qubit
            qc.cx(0, 1)  # Entangle the first qubit with the second

            # Measure the qubits and store results in classical bits
            qc.measure([0, 1], [0, 1])

            # Use Aer's qasm_simulator to simulate the quantum circuit
            backend = Aer.get_backend('qasm_simulator')

            # Run the circuit and simulate with 1 shot (single measurement per voter)
            job = backend.run(qc, shots=1)
            result = job.result()
            counts = result.get_counts(qc)  # Get measurement results

            # Update vote counts based on measurement outcomes
            for outcome in counts:
                if outcome in vote_counts:
                    vote_counts[outcome] += counts[outcome]

    # Determine winner(s) by finding candidates with highest count
    max_vote_count = max(vote_counts.values())
    
    winners = [int(k, 2) for k, v in vote_counts.items() if v == max_vote_count]

    # Plot histogram of results and encode it as base64 image
    fig = plt.figure()
    plot_histogram(vote_counts)  
    buf = io.BytesIO()  
    plt.savefig(buf, format='png')  
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode()  

    return {
        'vote_counts': vote_counts,
        'winner': winners,
        'votes': max_vote_count,
        'image': img_base64
    }

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Function to encode votes using amplitude encoding into a quantum circuit
def amplitude_encoding(vote_vec, quantum_circuit):
    """
    Encodes a vote vector into a quantum circuit using amplitude encoding.
    
    Args:
        vote_vec (list): A list representing a vote vector (one-hot encoded).
        quantum_circuit (QuantumCircuit): A quantum circuit object to encode the vote.
    """
    norm = np.linalg.norm(vote_vec)  # Normalize the vote vector
    normalized_vector = vote_vec / norm
    quantum_circuit.initialize(normalized_vector, [0, 1])  # Initialize the circuit with the normalized vector

# Main function to start the Flask application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
