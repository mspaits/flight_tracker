"""Flight Tracker Application using Amadeus API"""

import os
import json
import sqlite3
from amadeus import Client, ResponseError
from dotenv import load_dotenv
from flask import Flask, render_template, request, g

load_dotenv()

app = Flask(__name__)

# Database connection preventing multiple thread usage issues


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
            max=max_results,
            currencyCode='USD'
        )
        if airline_code:
            params['includedAirlineCodes'] = airline_code

        print(params)

        response = amadeus.shopping.flight_offers_search.get(**params)

        return response

    except ResponseError as error:
        print(f"An error occurred: {error}")
        return None


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
        max_results = int(request.form.get('max_results', 5))

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
                    "carrier_code": segments[i]['carrierCode'],
                    "flight_number": segments[i]['number']
                }
                flight_data.append(flight_info_leg)

        return render_template('index.html', flights=flight_data)

    else:
        return render_template('index.html')


@app.route('/autotrack', methods=['GET', 'POST'])
def autotrack():
    """Route for auto-tracking flights"""

    if request.method == 'POST':
        # Get data from HTML form
        origin = request.form.get('origin').upper()
        destination = request.form.get('destination').upper()
        departure_date = request.form.get('departure_date')
        adults = int(request.form.get('adults', 1))
        airline_code = request.form.get('airline_code')
        max_results = int(request.form.get('max_results', 5))

        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO searches (origin, destination, date, adults, results, airline) VALUES (?, ?, ?, ?, ?, ?)",
                    (origin, destination, departure_date, adults, max_results, airline_code))
        db.commit()

    return render_template('autotrack.html')
