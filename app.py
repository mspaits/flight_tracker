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

# Function to get airline name for iataCode
def get_airline_name(xx):
    """Function to look up airline name from 2-letter code"""
    try:
        airline_response = amadeus.reference_data.airlines.get(airlineCodes=xx)
        airline_name = airline_response.data[0]['commonName']
        return airline_name

    except ResponseError as error:
        print(f"An error occurred: {error}")
        return None


try:
    response = amadeus.shopping.flight_offers_search.get(
        originLocationCode='RDU',
        destinationLocationCode='MIA',
        departureDate='2026-01-19',
        adults=1,
        includedAirlineCodes='F9',
        currencyCode='USD',
        max=3
    )

except ResponseError as error:
    print(f"An error occurred: {error}")


# Print stuff to terminal
for flight in response.data:
    legs = len(flight['itineraries'][0]['segments'])
    itinerary = flight['itineraries'][0] # Contains duration and segments
    segments = itinerary['segments'] # Contains each flight leg details

    print("")
    print("Search no:", flight['id'])
    print("Stops:", legs - 1)
    print("Departure Airport:", segments[0]['departure']['iataCode'])
    print("Departure Time:", segments[0]['departure']['at'])
    print("Arrival Airport:", segments[-1]['arrival']['iataCode'])
    print("Arrival Time:", segments[-1]['arrival']['at'])
    print("Duration:", flight['itineraries'][0]['duration'])
    print("Carrier Code:", get_airline_name(flight['validatingAirlineCodes']))
    print("Price:", flight['price']['grandTotal'])
    print("Bookable seats:", flight['numberOfBookableSeats'])

    for i in range(legs):
    # Need to print each leg details
        print("  Leg:", i + 1)
        print("Departure Airport:", segments[i]['departure']['iataCode'])
        print("Departure Time:", segments[i]['departure']['at'])
        print("Arrival Airport:", segments[i]['arrival']['iataCode'])
        print("Arrival Time:", segments[i]['arrival']['at'])
        print("Duration:", segments[i]['duration'])
        print("Carrier Code:", get_airline_name(segments[i]['carrierCode']))
        print("Flight Number:", segments[i]['number'])


# Save response to a JSON file
with open("flight_offers.json", "w", encoding="utf-8") as file:
    json.dump(response.data, file, indent=2)
print("\nFlight offers saved to flight_offers.json")

# Create a dict to hold flight data for rendering in Flask
flight_data = {
    "flights": response.data
}

# Flask route to render a simple homepage
@app.route('/')
def index():
    return render_template('index.html')

