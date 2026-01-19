# Project: Flight-Tracker
### Video Demo:

### Description:
The Flight-Tracker web app was created primarily to alert the user when airline flights become available for a selected route and date.  The app utilizes several features to help search and track flight routes.  Please note: this app is being hosted locally and is not currently available for public use.

#### Key features include:
- Home page allowing the user to search a one way route.
- Secondary page allowing the user to save a route for one click searching in the future
- Option for user to add their email to the tracker which will activate a daily search of that route and send them the results in a formatted email.
  - This part is particularly useful when you want to know as soon as flights become available since there are usually a limited number of seats available via saver fares using points.

### Directions for use:
- On the Flight Tracker page (home page, index.html): Search a one way flight route by entering the details of the desired route and hit the "Search Flights" button.  The "From", "To", "Departure Date", and "Number of Adult" fields are mandatory.  Optionally you can add the airline code of a specific airline and the max number of route results you would like returned.  Note: the "Airline Code" field must contain only the two digit code for the selected airline.  Only one airline may be searched at a time.  Incorrect entries will simply reload the search page.
  - The search querries the Global Distribution System (GDS) provider Amadeus via an API call and returns available flights listed in order of price.  Each listing will first display a search number and the main itinerary.  Below it, each leg of the itinerary will be listed as "Leg: 1", "Leg: 2", etc.  (please note: the app is using the test environment version of the API as the "move to production workflow" to get a production API key is currently down.  I will move to the production as soon as it becomes available).  Note to self: don't commit your API keys!!!  It's not easy to erease things off of Github.
  - To set up a route for tracking hit the "To Auto Track Page" button.

- On the Auto Tracker page (autotrack.html):  You are able to store criteria for a future search by entering the desired route details and hitting the "Track Route" button.  Entries are displayed on the below table.  To run a search on any route just hit the "Search Now" button and results will be returned on the home page.  Additionally, you have the option to enter your email address which will appear in the below table.  The app is set up to send a daily email with fresh flight search results for each row that contains an email.  An email can be added or removed from an existing tracked route with the corresponding buttons.  Also, a route can be deleted with the "Delete Route" button.
  - The auto email was set up using a Google Cloud gmail API.  I decided to go the proper route which entailed full OAuth authentication.  This took me a bit deeper than I was expecting and I leaned on AI heavily to write the token requesting and handling function.  Although, the Google documentation was pretty good and I did learn a lot.

### Files:
- app.py - The main file, as you might immagine.  The main workflows include routes to display the homepage with flight search and the auto tracker page.  I guess I'll just go down the list and explain what I learned.
  - Working with APIs.  They were actually more involved than I was expecting.  No one is going to give you any information without an API key code.  At first I was unclear on the difference between making a traditional API call by passing info into HTTP request and other ways such as using a provided software developer kit (SDK).  Like with many things I eventually learned, there are multiple ways to do things and sometimes there is not one clear right way.  Luckily the Amadeus developer site provided a SDK which handled all the OAuth token stuff for me.  Each API system is a little bit different and it took some time to learn the Amadeus one (
  - Storing your API keys and secrets as envirionmental variabled in a .env folder (that you don't commit to Github!).  Only reference them via that file in your code.
  - Working with an Sqlite3 database is a bit more tedious when not working in the CS50 codespace.  There is a cursor involved and I had some help from AI in writing the funcion that finds and accesses the database.  Also, there were considerations to prevent multiple threads from using the database at the same time, maybe similar to race conditions.  More on this later but I set up my own home server for this site on a Raspberry Pi.  You can't track your database because if you git pull your repository onto your server, the commited database will come with it and overwrite your server data.  Allowing the code to find the path to and access different databases on different systems was tricky.
  - 
