import mysql.connector
import openai
import re
import pyttsx3  # For text-to-speech
from flask import Flask, request, jsonify, render_template
import threading

# Initialize OpenAI API key
openai.api_key = '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'
app = Flask(__name__)

# Initialize pyttsx3 engine for voice output
engine = pyttsx3.init()

# Create a lock to prevent concurrent access to the speech engine
speech_lock = threading.Lock()

# Function to convert text to speech (offload to a separate thread)
def speak(text):
    def speak_thread(text):
        with speech_lock:
            engine.say(text)
            engine.runAndWait()

    # Create a new thread for the speech function
    t = threading.Thread(target=speak_thread, args=(text,))
    t.start()

# Function to connect to MySQL database
def connect_db():
    conn = mysql.connector.connect(
        host="localhost",        # Replace with your MySQL host
        user="root",             # Replace with your MySQL username
        password="root@123",     # Replace with your MySQL password
        database="opencv"        # Replace with your MySQL database
    )
    return conn

# Function to safely execute SQL queries
def execute_query(conn, query):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        return f"Error: {err}"

# Query match functions for the chatbot
def match_count_query(user_input):
    match = re.search(r'how many .* in (\w+)', user_input.lower())
    return f"SELECT COUNT(*) FROM {match.group(1)}" if match else None

def match_show_query(user_input):
    match = re.search(r'show me .* in (\w+)', user_input.lower())
    return f"SELECT * FROM {match.group(1)}" if match else None

def parse_query(user_input):
    query_handlers = [match_count_query, match_show_query]
    for handler in query_handlers:
        query = handler(user_input)
        if query:
            return query
    return None

# Function to use OpenAI GPT if the query is not understood
def ask_openai_gpt(user_question):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=user_question,
        max_tokens=100
    )
    return response.choices[0].text.strip()

# Handle non-query questions
def handle_non_query(user_input):
    responses = {
        "hi": "Hello!",
        "hello": "Hi there! How can I assist you today?",
        "what is your name": "I am your AI chatbot. How can I help you?",
        "help": "You can ask me questions about the database or general information.",
        "exit": "Goodbye! Have a great day!",
        "database name": "The MySQL database is used for storing and managing data.",
        "project name": "The project name is 'dangal'."
    }
    default_response = "I'm not sure how to answer that. Can you ask something else?"
    return responses.get(user_input.lower(), default_response)

# Route for the chatbot front-end
@app.route('/')
def index():
    return render_template('chatbot.html')

# Route for handling chatbot queries via POST
@app.route('/ask', methods=['GET', 'POST'])
def ask():
    # Initialize response to prevent UnboundLocalError
    response = None

    if request.method == 'POST':
        user_input = request.form.get('messageText')

        # Ensure a database connection is established
        conn = connect_db()

        # Parse the query
        query = parse_query(user_input)
        if query:
            results = execute_query(conn, query)
            if isinstance(results, list) and results:
                if "count(*)" in results[0]:
                    response = f"There are {results[0]['count(*)']} items in the table."
                else:
                    response = "Here is the data: " + str(results)
            elif isinstance(results, str):
                response = results
            else:
                response = "No results found."
        else:
            # Handle non-query questions
            response = handle_non_query(user_input)
            if response == "I'm not sure how to answer that. Can you ask something else?":
                response = ask_openai_gpt(user_input)

        speak(response)  # Speak the response
    else:
        return "This endpoint only handles POST requests for chatbot queries."

    # Check if the response is set, if not, return an error message
    if response is None:
        response = "Sorry, I couldn't process your request."

    return jsonify({'answer': response})

if __name__ == '__main__':
    app.run(debug=True)
