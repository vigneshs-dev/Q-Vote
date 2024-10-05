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

# Homepage route
@app.route('/')
def index():
    """
    Route for the homepage. Renders the index.html template.
    """
    return render_template('index.html')

# Voting route to trigger quantum voting simulation
@app.route('/vote', methods=['POST'])
def vote():
    """
    Route to simulate a quantum voting system based on user input votes for each candidate.
    
    Returns:
        JSON response containing:
            - vote_counts: A dictionary with the counts of each vote outcome.
            - winner: The winner candidate based on the highest vote count.
            - votes: The total number of votes received by the winner.
            - image: Base64-encoded image of the vote distribution histogram.
    """
    votes = request.json.get('votes', [0, 0, 0, 0])  # Get votes from the request
    NUM_CANDIDATES = 4  # Number of candidates

    # Use the user-provided votes to simulate the quantum voting system
    vote_counts = {'00': votes[0], '01': votes[1], '10': votes[2], '11': votes[3]}

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
