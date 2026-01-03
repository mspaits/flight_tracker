"""Flight Tracker Application using Amadeus API"""

import os
import json
from amadeus import Client, ResponseError
from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()

app = Flask(__name__)

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

    print("Index route hit")

    # Get flight offers
    response = get_flight_offers(
        origin="RDU",
        destination="MIA",
        departure_date="2026-01-19",
        adults=1,
        airline_code="UA",
        max_results=5
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
        itinerary = flight['itineraries'][0]  # Contains duration and segments
        segments = itinerary['segments']  # Contains each flight leg details

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

    print(flight_data)

    return render_template('index.html', flights=flight_data)
