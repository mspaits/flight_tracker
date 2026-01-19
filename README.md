# Project: Flight-Tracker
### Video Demo:

### Description:
The Flight-Tracker web app was created primarily to alert the user when airline flights become available for a selected route and date.  The app utilizes several features to help search and track flight routes.  Please note: this app is being hosted locally and is not currently available for public use.

#### Key features include:
- Home page allowing the user to search a one way route.
- Secondary page allowing the user to save a route for one click searching in the future
- Option for user to add their email to the tracker which will activate a daily search of that route and send them the results in a formatted email.
  - This part is particularly useful when you want to know as soon as flights become available since there are usually a limited number of seats available via saver fares using points.

### Directions for use and implementation details:
- On the Flight Tracker page (home page, index.html): Search a one way flight route by entering the details of the desired route and hit the "Search Flights" button.  The "From", "To", "Departure Date", and "Number of Adult" fields are mandatory.  Optionally you can add the airline code of a specific airline and the max number of route results you would like returned.  Note: the "Airline Code" field must contain only the two digit code for the selected airline.  Only one airline may be searched at a time.  Incorrect entries will simply reload the search page.
  - The search querries the Global Distribution System (GDS) provider Amadeus via an API call and returns available flights listed in order of price.  Each listing will first display a search number and the main itinerary.  Below it, each leg of the itinerary will be listed as "Leg: 1", "Leg: 2", etc.  (please note: the app is using the test environment version of the API as the "move to production workflow" to get a production API key is currently down.  I will move to the production as soon as it becomes available).  Note to self: don't commit your API keys!!!  It's not easy to erease things off of Github.
  - To set up a route for tracking hit the "To Auto Track Page" button.

- On the Auto Tracker page (autotrack.html):  You are able to store criteria for a future search by entering the desired route details and hitting the "Track Route" button.  Entries are displayed on the below table.  To run a search on any route just hit the "Search Now" button and results will be returned on the home page.  Additionally, you have the option to enter your email address which will appear in the below table.  The app is set up to send a daily email with fresh flight search results for each row that contains an email.  An email can be added or removed from an existing tracked route with the corresponding buttons.  Also, a route can be deleted with the "Delete Route" button.
  - The auto email was set up using a Google Cloud gmail API.  I decided to go the proper route which entailed full OAuth authentication.  This took me a bit deeper than I was expecting and I leaned on AI heavily to write the token requesting and handling function.  Although, the Google documentation was pretty good and I did learn a lot.

### Files:
- app.py - The main file, as you might immagine.  
