"""Flight Tracker Application using Amadeus API"""

from io import StringIO
import os
import json
import base64
import google.auth
import sqlite3
from pprint import pprint
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from amadeus import Client, ResponseError
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, g


load_dotenv()

app = Flask(__name__)


# Database connection preventing multiple thread usage issues.  Per copilot suggestion.
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('tracked.db')
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


amadeus = Client(
    client_id=os.getenv("AMADEUS_API_KEY"),
    client_secret=os.getenv("AMADEUS_API_SECRET")
)


def get_airline_name(xx):
    """Function to look up airline name from 2-letter code"""
    try:
        airline_response = amadeus.reference_data.airlines.get(airlineCodes=xx)
        airline_name = airline_response.data[0]['commonName']
        return airline_name

    except ResponseError as error:
        print(f"An error occurred: {error}")
        return None


def get_flight_offers(origin, destination, departure_date, adults, airline_code, max_results):
    """Function to get flight offers from Amadeus API"""
    try:
        params = dict(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=adults,
            currencyCode='USD'
        )
        if airline_code:
            params['includedAirlineCodes'] = airline_code
        if max_results:
            params['max'] = int(max_results)

        response = amadeus.shopping.flight_offers_search.get(**params)

        return response

    except ResponseError as error:
        print(f"An error occurred: {error}")
        return None


def process_flight_data(response):
    """Function to process flight data from Amadeus response"""

    # Create an empty list to hold flight data for rendering in Flask
    flight_data = []

    for flight in response.data:
        legs = len(flight['itineraries'][0]['segments'])
        # Contains duration and segments
        itinerary = flight['itineraries'][0]
        # Contains each flight leg details
        segments = itinerary['segments']

        flight_info = {
            "search_no": flight['id'],
            "stops": (legs - 1),
            "departure_airport": segments[0]['departure']['iataCode'],
            "departure_time": segments[0]['departure']['at'],
            "arrival_airport": segments[-1]['arrival']['iataCode'],
            "arrival_time": segments[-1]['arrival']['at'],
            "duration": flight['itineraries'][0]['duration'],
            "carrier_code": flight['validatingAirlineCodes'][0],
            "price": flight['price']['grandTotal'],
            "bookable_seats": flight['numberOfBookableSeats']
        }
        flight_data.append(flight_info)

        for i in range(legs):
            # Need to print each leg details
            flight_info_leg = {
                "stops": f"Leg: {i + 1}",  # Actually indicates leg number
                "departure_airport": segments[i]['departure']['iataCode'],
                "departure_time": segments[i]['departure']['at'],
                "arrival_airport": segments[i]['arrival']['iataCode'],
                "arrival_time": segments[i]['arrival']['at'],
                "duration": segments[i]['duration'],
                "carrier_code": segments[i]['operating'].get('carrierCode') or
                segments[i]['operating'].get('carrierName'),
                "flight_number": segments[i]['number']
            }
            flight_data.append(flight_info_leg)

    return flight_data


# Straight up copied this from Codex.  Decided to do it the right way with OAuth2 and got in way deep.
def get_gmail_creds():

    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


# Create function to email out results.  From Google Gmail API quickstart.
def gmail_send_message(flight_data):
    """Email flight offers using Gmail API"""

    creds = get_gmail_creds()

    # Codex recommendation
    buffer = StringIO()
    pprint(flight_data, stream=buffer, sort_dicts=False)
    ppflight_data = buffer.getvalue()

    try:
        service = build("gmail", "v1", credentials=creds)
        message = EmailMessage()

        message['To'] = "mspaitsdev@gmail.com"
        message['From'] = "mspaitsdev@gmail.com"
        message['Subject'] = "Flight Offers Test"

        message.set_content(f"Flight offers are so great!\n {ppflight_data}")

        # Encode the message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {'raw': encoded_message}
        # pyling: disable=E1101
        send_message = (service.users().messages().send(
            userId="me", body=create_message).execute())
        print(F'Message Id: {send_message["id"]}')

    except HttpError as error:
        print(f'An error occurred: {error}')
        send_message = None
    return send_message


# Flask route to render a simple homepage
@app.route('/', methods=['GET', 'POST'])
def index():
    """Route for homepage and flight search"""

    print("Index route hit")

    if request.method == 'POST':
        # Get data from HTML form
        origin = request.form.get('origin').upper()
        destination = request.form.get('destination').upper()
        departure_date = request.form.get('departure_date')
        adults = int(request.form.get('adults', 1))
        airline_code = request.form.get('airline_code')
        max_results = request.form.get('max_results')

        # Call function to get flight offers
        response = get_flight_offers(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            adults=adults,
            airline_code=airline_code,
            max_results=max_results
        )

        if response is None:
            return "Error retrieving flight offers."

        # Save response to a JSON file
        with open("flight_offers.json", "w", encoding="utf-8") as file:
            json.dump(response.data, file, indent=2)
        print("\nFlight offers saved to flight_offers.json")

        flight_data = process_flight_data(response)

        return render_template('index.html', flights=flight_data)

    else:
        return render_template('index.html')


@app.route('/autotrack', methods=['GET', 'POST'])
def autotrack():
    """Route for auto-tracking flights.  Adds searches to the db and displays tracked searches."""

    if request.method == 'POST':
        # Get data from HTML form
        origin = request.form.get('origin').upper()
        destination = request.form.get('destination').upper()
        departure_date = request.form.get('departure_date')
        adults = int(request.form.get('adults', 1))
        airline_code = request.form.get('airline_code')
        max_results = request.form.get('max_results')

        # Apparently this is what you need to do to access Sqlite3 outside of CS50 IDE.
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO searches (origin, destination, date, adults, results, airline) VALUES (?, ?, ?, ?, ?, ?)",
                    (origin, destination, departure_date, adults, max_results, airline_code))
        db.commit()

        return redirect('/autotrack')

    else:

        # Retrieve tracked searches from the database to render on webpage
        db = get_db()
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        cur.execute("SELECT * FROM searches")
        tracked_table = cur.fetchall()  # Fetches all rows

        return render_template('autotrack.html', tracked_table=tracked_table)


# I got this method of passing in the search_id from a copilot suggestion
@app.route('/delete/<int:search_id>', methods=['POST'])
def delete_search(search_id):
    """Route to delete a tracked search"""

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM searches WHERE id = ?", (search_id,))
    db.commit()

    return redirect('/autotrack')


@app.route('/check/<int:search_id>', methods=['POST'])
def check_search(search_id):
    """Route to check a tracked search immediately"""

    db = get_db()
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    cur.execute("SELECT * FROM searches WHERE id = ?", (search_id,))
    search = cur.fetchone()  # Fetches one row

    print([dict(search)])

    if search is None:
        return "Search not found.", 404

    response = get_flight_offers(
        origin=search['origin'],
        destination=search['destination'],
        departure_date=search['date'],
        adults=search['adults'],
        airline_code=search['airline'],
        max_results=search['results']
    )

    if response is None:
        return "Error retrieving flight offers."

    # Save response to a JSON file
    with open("flight_offers.json", "w", encoding="utf-8") as file:
        json.dump(response.data, file, indent=2)
    print("\nFlight offers saved to flight_offers.json")

    flight_data = process_flight_data(response)

    # Save to txt file
    with open("flight_offers.txt", "w", encoding="utf-8") as file:
        pprint(flight_data, stream=file, sort_dicts=False)
    print("\nFlight offers saved to flight_offers.txt")

    gmail_send_message(flight_data)

    return render_template('index.html', flights=flight_data)
