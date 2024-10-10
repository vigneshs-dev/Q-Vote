# Import necessary libraries
import os
import math
import hashlib
import random
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.compiler import transpile

# Assuming the app.py is inside the 'src' directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current file (src folder)
DATABASE_PATH = os.path.join(BASE_DIR, 'db', 'votes.db')  # Set the database path inside the src folder

# Initialize Flask App
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Update the get_db_connection function
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)  # Connect using the absolute path
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    has_voted BOOLEAN NOT NULL DEFAULT 0)''')

    conn.execute('''CREATE TABLE IF NOT EXISTS votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    candidate INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id))''')
    conn.commit()
    conn.close()

# Voter Class
class Voter:
    def __init__(self, voter_id, secret_key_AB, secret_key_AC):
        self.voter_id = voter_id  # Voter ID assigned by Tallyman
        self.secret_key_AB = secret_key_AB  # Secret key shared with Tallyman
        self.secret_key_AC = secret_key_AC  # Secret key shared with Scrutineer
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

# Tallyman Class
class Tallyman:
    def __init__(self):
        self.voter_database = {}  # Store hash IDs and votes

    def issue_voter_id(self, voter_name):
        """Issue a unique voter ID and generate secret keys."""
        voter_id = f"{voter_name}_{random.randint(1000,9999)}"
        secret_key_AB = bin(random.getrandbits(4))[2:].zfill(4)
        secret_key_AC = bin(random.getrandbits(4))[2:].zfill(4)
        return voter_id, secret_key_AB, secret_key_AC

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

# Scrutineer Class
class Scrutineer:
    def __init__(self, secret_key_AC):
        self.secret_key_AC = secret_key_AC  # Secret key shared with Voter

    def verify_vote(self, hash_id, voting_db):
        """Verify if a vote exists in the database using hash ID."""
        return hash_id in voting_db

@app.route('/')
def index():
    # If the user is logged in
    if 'user_id' in session:
        return redirect(url_for('results'))
    else:
        # If not logged in, redirect to registration
        return redirect(url_for('register'))


# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, has_voted) VALUES (?, ?, ?)',
                         (username, hashed_password, False))
            conn.commit()
            conn.close()
            flash("Registration successful. Please log in.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash("Username already taken. Please try a different one.")
            return redirect(url_for('register'))

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

        if user is None:
            flash("User not found. Please register first.", 'error')
            return redirect(url_for('login'))

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = username
            flash("Login successful.")
            return redirect(url_for('vote'))
        else:
            flash("Invalid credentials. Please try again.")
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'user_id' not in session:
        flash("Please log in to vote.", category='warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    # Check if user has already voted
    if user['has_voted']:
        conn.close()
        flash("You have already voted. You cannot vote again.", category='error')
        return redirect(url_for('results'))

    if request.method == 'POST':
        candidate = int(request.form['candidate'])
        adjusted_candidate = candidate - 1

        # Insert the vote
        conn.execute('INSERT INTO votes (user_id, candidate) VALUES (?, ?)', (session['user_id'], adjusted_candidate))
        conn.execute('UPDATE users SET has_voted = ? WHERE id = ?', (True, session['user_id']))
        conn.commit()
        conn.close()
        flash("Your vote has been recorded successfully!", category='success')
        return redirect(url_for('results'))

    # Fetch current vote counts for display
    current_vote_counts = conn.execute('SELECT candidate, COUNT(*) as count FROM votes GROUP BY candidate').fetchall()
    conn.close()

    # Prepare vote counts for rendering
    adjusted_counts = [(row['candidate'] + 1, row['count']) for row in current_vote_counts]
    all_candidates = {1: 0, 2: 0, 3: 0, 4: 0}
    for candidate, count in adjusted_counts:
        all_candidates[candidate] = count

    vote_counts = [(candidate, count) for candidate, count in all_candidates.items()]
    return render_template('vote.html', current_vote_counts=vote_counts)

@app.route('/results')
def results():
    if 'user_id' not in session:
        flash("Please log in to view results.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    votes_from_db = conn.execute('SELECT candidate FROM votes').fetchall()
    users_from_db = conn.execute('SELECT username FROM users').fetchall()
    conn.close()

    user_votes_db = [row['candidate'] for row in votes_from_db]
    usernames_db = [row['username'] for row in users_from_db]

    tallyman = Tallyman()
    secret_key_AC = bin(random.getrandbits(4))[2:].zfill(4)
    scrutineer = Scrutineer(secret_key_AC)

    for user, user_vote in zip(usernames_db, user_votes_db):
        voter_id, secret_key_AB, secret_key_AC = tallyman.issue_voter_id(user)
        voter = Voter(voter_id, secret_key_AB, secret_key_AC)

        vote_circuit = voter.encode_vote([1 if i == user_vote else 0 for i in range(4)])
        signed_vote = voter.sign_vote(vote_circuit)
        tallyman.store_vote(voter.hash_id, signed_vote)

        if scrutineer.verify_vote(voter.hash_id, tallyman.voter_database):
            print(f"Vote verified by Scrutineer for voter hash ID: {voter.hash_id}")
        else:
            print(f"Vote could not be verified by Scrutineer.")

    results = tallyman.tally_votes()
    print("Quantum Vote Counts:", results)

    # Adjust the results to be 1-based
    adjusted_results = {k+1: v for k, v in results.items()}

    max_votes = max(adjusted_results.values())
    winners = [candidate for candidate, count in adjusted_results.items() if count == max_votes]

    return render_template('results.html', vote_counts=adjusted_results, winners=winners, max_votes=max_votes)

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))

# Function to determine the winner
def determine_winner(vote_counts):
    """Determine the winner based on vote counts."""
    winner = max(vote_counts, key=vote_counts.get)
    return winner, vote_counts[winner]

# Main Voting Program (Quantum Voting + Tally + Scrutineer Verification)
def main():
    # Initialize Tallyman and Scrutineer
    tallyman = Tallyman()

    # Assuming Scrutineer has AC to verify
    secret_key_AC = bin(random.getrandbits(4))[2:].zfill(4)
    scrutineer = Scrutineer(secret_key_AC)

    # Retrieve votes from the database (simulate database query)
    conn = get_db_connection()
    votes_from_db = conn.execute('SELECT candidate FROM votes').fetchall()
    conn.close()

    # Convert database votes to list of approvals (1 for approval, 0 for disapproval)
    user_votes_db = [row['candidate'] for row in votes_from_db]

    # List of users to simulate voting (for this example)
    users = ["user1", "user2", "user3", "user4", "user5"]

    for user, user_vote in zip(users, user_votes_db):
        # Simulate each user as a voter
        voter_id, secret_key_AB, secret_key_AC = tallyman.issue_voter_id(user)
        voter = Voter(voter_id, secret_key_AB, secret_key_AC)

        # Voter encodes their vote into quantum circuit
        vote_circuit = voter.encode_vote([1 if i == user_vote else 0 for i in range(4)])  # 4 candidates

        # Voter signs their vote
        signed_vote = voter.sign_vote(vote_circuit)

        # Store the vote in Tallyman's database before verification
        tallyman.store_vote(voter.hash_id, signed_vote)

        # Verify if the vote exists in the database
        if scrutineer.verify_vote(voter.hash_id, tallyman.voter_database):
            print(f"Vote verified by Scrutineer for voter hash ID: {voter.hash_id}")
        else:
            print(f"Vote could not be verified by Scrutineer.")

    # Tally the votes
    results = tallyman.tally_votes()
    print("Vote Counts:", results)

    # Determine the maximum votes and find winners
    max_votes = max(results.values())
    winners = [candidate for candidate, count in results.items() if count == max_votes]

    # Announce winners
    if len(winners) == 1:
        print(f"The winner is Candidate {winners[0]} with {max_votes} votes.")
    else:
        print(f"It's a tie! Candidates {', '.join(map(str, winners))} have the highest votes with {max_votes} votes.")


# Run the Flask app
if __name__ == "__main__":
    create_tables()  # Ensure tables are created before running the app
    app.run(debug=True, host='0.0.0.0', port=5000)
