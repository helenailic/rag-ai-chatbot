# How to Run the Assistant

1. **Navigate to the Data Folder**  
   Open your terminal and navigate to the `chatbot` folder:  
   `cd path to chatbot folder`

2. **Set Up a Virtual Environment**  
   Create and activate a virtual environment:  
   - **Windows**:  
     `python -m venv venv`  
     `venv\Scripts\activate`  
   - **Mac/Linux**:  
     `python -m venv venv`  
     `source venv/bin/activate`

3. **Install Required Libraries**  
   Copy these into terminal:  
   `pip install requests`
   `pip install numpy`
   `pip install scikit-learn`
   `pip install pandas`
   `pip install openai`
   `pip install flask`
   `pip install flask-cors`
   `pip install python-dotenv`
   `pip install spotipy`

5. `python sales_database_init.py`


6. **Run the Flask Application**  
   Start the chatbot backend:  
   `python app.py`

7. **Access the User Interface**  
   Open the `index.html` file in your browser from your file explorer.

8. **Interact with the Chatbot**  
   Use the chatbot directly from the opened UI.


