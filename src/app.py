from flask import Flask, render_template, request, jsonify
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
import io
import base64

# Flask app initialization
app = Flask(__name__)

@app.route('/')
def index():
    """Render the homepage."""
    return render_template('index.html')

@app.route('/vote', methods=['POST'])
def vote():
    """
    Simulate a quantum voting system based on user input votes for each candidate.
    
    Returns:
        JSON response containing:
            - vote_counts: A dictionary with the counts of each vote outcome.
            - winner: The winner candidate based on the highest vote count.
            - votes: The total number of votes received by the winner.
            - image: Base64-encoded image of the vote distribution histogram.
    """
    votes = request.json.get('votes', [0, 0, 0, 0])
    NUM_CANDIDATES = 4

    vote_counts = {f'{i:02b}': votes[i] for i in range(NUM_CANDIDATES)}

    winner = max(vote_counts, key=vote_counts.get)
    winner_candidate = int(winner, 2)

    fig, ax = plt.subplots()
    plot_histogram(vote_counts, ax=ax)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode()

    return jsonify({
        'vote_counts': vote_counts,
        'winner': winner_candidate,
        'votes': vote_counts[winner],
        'image': img_base64
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
