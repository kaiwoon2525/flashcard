import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user
import pymysql
import secrets
import requests
import plotly.graph_objs as go
from collections import Counter
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import random
from bs4 import BeautifulSoup

app = Flask(__name__)
secret_key = secrets.token_hex(16)
app.secret_key = secret_key

login_manager = LoginManager(app)
login_manager.login_view = 'login'

db_settings = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "usbw",
    "db": "flashword",
    "charset": "utf8"
}

# Define a User class if you haven't already
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# User loader function to retrieve a user by their ID
@login_manager.user_loader
def load_user(user_id):
    # This function should return a user object or None if the user is not found.
    # You should customize it based on your user model.
    return User(user_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/go_login')
def go_login():
    return render_template('login.html')

@app.route('/go_createuser')
def go_createuser():
    return render_template('createuser.html')

# @app.route('/go_webscraping', methods=['GET', 'POST'])
# def go_webscraping():
#     card_keyword = request.args.get('card_keyword', default=None, type=str)

#     # Check if card_keyword is None
#     if card_keyword is None:
#         flash("Please provide a keyword for web scraping.", 'error')
#         return redirect(url_for('index'))  # Redirect to the index page or any appropriate route
    
#     return render_template('web_scraping.html', card_keyword=card_keyword)


@app.route('/createdeckpage', methods=['GET'])
def createdeckpage():
    user_id = request.args.get('user_id', default=None, type=int)
    return render_template('createdeck.html', user_id=user_id)


@app.route('/deckdetails', methods=['GET', 'POST'])
def deckdetails():
    user_id = request.args.get('user_id', default=None, type=int)
    
    # Fetch user decks from the database
    user_decks = []

    if user_id:
        try:
            conn = pymysql.connect(**db_settings)
            cursor = conn.cursor()

            # Fetch decks for the user from the database including Deck ID and Create by User ID
            cursor.execute("SELECT deck_id, deck_name, created_by_user_id FROM deck WHERE created_by_user_id = %s", (user_id,))
            user_decks = cursor.fetchall()

            cursor.close()
            conn.close()
        except Exception as ex:
            flash(f"An error occurred: {ex}", 'error')
    
    return render_template('deck_details.html', user_id=user_id, user_decks=user_decks)




@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    try:
        conn = pymysql.connect(**db_settings)
        cursor = conn.cursor()

        # Insert a new user into the database
        cursor.execute("INSERT INTO users (name, password) VALUES (%s, %s)", (username, password))
        conn.commit()

        cursor.close()
        conn.close()
    except Exception as ex:
        print(f"An error occurred: {ex}")

    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    user_id = None  # Initialize the user_id to None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = pymysql.connect(**db_settings)
            cursor = conn.cursor()

            # Check if the username and password are in the database
            cursor.execute("SELECT id FROM users WHERE name=%s AND password=%s", (username, password))
            user = cursor.fetchone()

            if user:
                user_id = user[0]  # Store the user's ID
                flash('Login successful.', 'success')
                return redirect(url_for('deckdetails', user_id=user_id))
                #return redirect(url_for('createdeckpage', user_id=user_id))
            else:
                flash('Invalid username or password.', 'error')

            cursor.close()
            conn.close()
        except Exception as ex:
            flash(f"An error occurred: {ex}", 'error')

    return render_template('login.html')
    

@app.route('/create_flashcard', methods=['GET', 'POST'])
def create_flashcard():
    if request.method == 'POST':
        user_id = request.form['user_id']
        deck_id = request.form['deck_id']
        question = request.form['question']
        answer = request.form['answer']
        

        try:
            conn = pymysql.connect(**db_settings)
            cursor = conn.cursor()

            # Insert the flashcard into the database
            cursor.execute("INSERT INTO flashcards (question, answer, deck_id) VALUES (%s, %s, %s)", (question, answer, deck_id))
            conn.commit()

            cursor.close()
            conn.close()

            flash('Flashcard created successfully.', 'success')
            return redirect(url_for('deckdetails', user_id=user_id))
        except Exception as ex:
            flash(f"An error occurred: {ex}", 'error')

    # deck_id = request.args.get('deck_id', default=None, type=int)
    user_id = request.args.get('user_id', default=None, type=int)
    deck_id = request.args.get('deck_id')
    # user_id = request.args.get('user_id')
    return render_template('createflashcard.html', deck_id=deck_id, user_id=user_id)



@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    card_keyword = request.args.get('card_keyword', default=None, type=str)
    user_id = request.args.get('user_id', default=None, type=int)
    
    if card_keyword is None:
        return "Please provide a keyword for web scraping."

    url = 'https://birtenshaw.org.uk/birtenshaw-school-merseyside/'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')

        keyword = card_keyword
        unique_paragraphs = set()  # Use a set to store unique paragraphs
        for paragraph in paragraphs:
            if keyword in paragraph.text:
                unique_paragraphs.add(paragraph.text.strip())  # Add the stripped paragraph text to the set
        
        return render_template('results.html', paragraphs=unique_paragraphs, user_id=user_id)
    else:
        return "Failed to retrieve the web page."



@app.route('/createdeck', methods=['POST'])
def createdeck():
    if request.method == 'POST':
        user_id = request.form['user_id']
        deck_name = request.form['deck_name']

        try:
            conn = pymysql.connect(**db_settings)
            cursor = conn.cursor()

            # Insert the deck information into the database
            cursor.execute("INSERT INTO deck (deck_name, created_by_user_id) VALUES (%s, %s)", (deck_name, user_id))
            conn.commit()

            cursor.close()
            conn.close()

            flash('Deck created successfully.', 'success')
        except Exception as ex:
            flash(f"An error occurred: {ex}", 'error')

    return redirect(url_for('deckdetailspage', user_id=user_id))




@app.route('/test', methods=['GET', 'POST'])
def test():        
    deck_id = request.args.get('deck_id', default=None, type=int)
    user_id = request.args.get('user_id', default=None, type=int)
    
    # Fetch flashcards for the selected deck from the database
    flashcards = []

    try:
        conn = pymysql.connect(**db_settings)
        cursor = conn.cursor()

        # Fetch flashcards for the deck from the database
        cursor.execute("""
            SELECT question, answer, flashcards_id, difficulty 
            FROM flashcards 
            WHERE deck_id = %s 
            ORDER BY 
                CASE 
                    WHEN difficulty = 3 THEN 1 
                    WHEN difficulty = 2 THEN 2 
                    ELSE 3 
                END ASC
        """, (deck_id,))
        flashcards = cursor.fetchall()
        
        if flashcards:
            # Selecting the first flashcard from the sorted list
            random_num = flashcards[0]
            
            # printing random number
            flash("Flashcard ID : " + str(random_num[2]))
            flash("Question : " + str(random_num[0]))
            flash("Answer : " + str(random_num[1]))
            flash("Difficulty : " + str(random_num[1]))
            
            
            question = random_num[0]
            answer = random_num[1]
            flashcards_id = random_num[2]
            difficulty= random_num[3]
        else:
            flash("No flashcards found for this deck", 'error')
            return redirect(url_for('some_redirect_route'))  # Redirect to an appropriate route
        
    except Exception as ex:
        flash(f"An error occurred: {ex}", 'error')
    finally:
        cursor.close()
        conn.close()

    return render_template('test_flashcard.html', question=question, answer=answer, 
                            user_id=user_id, flashcards_id=flashcards_id, deck_id=deck_id, difficulty=difficulty)

@app.route('/test2', methods=['GET', 'POST'])
def test2():
    user_id = request.args.get('user_id', default=None, type=int)
    deck_id = request.args.get('deck_id', default=None, type=int)
    flashcards_id = request.args.get('flashcards_id', default=None, type=int)
    answer = request.args.get('answer', default=None, type=str)
    return render_template('test_flashcard2.html', user_id=user_id, deck_id=deck_id, flashcards_id=flashcards_id, answer=answer)





@app.route('/update_difficulty', methods=['POST'])
def update_difficulty():
    user_id = request.form.get('user_id', type=int)
    flashcards_id = request.form.get('flashcards_id', type=int)
    deck_id = request.form.get('deck_id', type=int)
    difficulty_str = request.form.get('difficulty')

    # Mapping the difficulty string to its corresponding integer value
    difficulty_map = {'Easy': 1, 'Good': 2, 'Hard': 3}
    difficulty = difficulty_map.get(difficulty_str)

    if difficulty is None:
        flash("Invalid difficulty level", 'error')
        return redirect(url_for('test', user_id=user_id, deck_id=deck_id))

    try:
        conn = pymysql.connect(**db_settings)
        cursor = conn.cursor()

        # Update the difficulty level and frequency in the database
        cursor.execute("UPDATE flashcards SET difficulty = %s, frequency = frequency + 1 WHERE flashcards_id = %s", (difficulty, flashcards_id))
        conn.commit()
        flash("Difficulty level updated successfully")
    except Exception as ex:
        conn.rollback()
        flash(f"An error occurred: {ex}", 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('test', user_id=user_id, deck_id=deck_id))



@app.route('/learning_performance', methods=['GET', 'POST'])
def learning_performance():
    user_id = request.args.get('user_id', default=None, type=int)
    deck_id = request.args.get('deck_id', default=None, type=int)
    
    try:
        conn = pymysql.connect(**db_settings)
        cursor = conn.cursor()

        # Fetch flashcards for the deck from the database
        cursor.execute("SELECT question, frequency FROM flashcards WHERE deck_id = %s", (deck_id,))
        flashcards = cursor.fetchall()
        
        # Convert flashcards to a DataFrame
        df = pd.DataFrame(flashcards, columns=['question', 'frequency'])

        plt.figure(figsize=(10, 6))
        sns.countplot(x='question', data=df, palette='viridis', hue='question', legend=False)
        plt.title('Learning performance')
        plt.xlabel('Question')
        plt.ylabel('Frequency')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('static/learning_performance.png')  # Save the graph as an image
        plt.close()

        cursor.close()
        conn.close()

        return render_template('learning_performance.html', user_id=user_id, deck_id=deck_id)
    except Exception as ex:
        flash(f"An error occurred: {ex}", 'error')
        return redirect(url_for('deckdetails', user_id=user_id))
    



@app.route('/card_details', methods=['GET', 'POST'])
def card_details():
    deck_id = request.args.get('deck_id', default=None, type=int)
    user_id = request.args.get('user_id', default=None, type=int)
    card_details = []

    try:
        conn = pymysql.connect(**db_settings)
        cursor = conn.cursor()

        cursor.execute("SELECT question, answer, difficulty, frequency FROM flashcards WHERE deck_id = %s", (deck_id,))
        card_details = cursor.fetchall()

        cursor.close()
        conn.close()
        return render_template('card_details.html', card_details=card_details, user_id=user_id)
                
    except Exception as ex:
        flash(f"An error occurred: {ex}", 'error')
    
    return render_template('card_details.html', user_id=user_id)






if __name__ == '__main__':
    app.run(debug=True)

