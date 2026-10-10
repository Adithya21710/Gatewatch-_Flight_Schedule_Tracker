# Gatewatch — Flight Route Intelligence

**Gatewatch is a serverless flight-monitoring platform that watches routes over time, tracks flight frequency and prices, detects changes, and alerts users through email.**

The project is built on Azure and uses SerpAPI's Google Flights data as its live flight-data source. Instead of acting as a one-time flight search page, Gatewatch stores route information and compares what changes over time.

## Why Gatewatch

Most flight search tools answer a question at one point in time:

> What flights are available right now?

Gatewatch focuses on the question that comes after that:

> What changed since I started watching this route?

For a tracked route, Gatewatch can surface:

- Flight frequency
- Individual flight options
- Airline and flight number
- Aircraft information
- Departure and arrival times
- Price for each flight
- Lowest available route price
- Historical price data
- Frequency changes
- Added or removed flights
- Route expiry and automatic cleanup
- Email notifications for important changes

This turns a flight search into a lightweight route-monitoring system.

## Architecture

```text
                         ┌──────────────────────┐
                         │      SerpAPI         │
                         │    Google Flights    │
                         └──────────┬───────────┘
                                    │
                                    ▼
┌─────────────────┐       ┌──────────────────────┐
│ Static Frontend │ ────▶ │ HTTP Function App   │
│ HTML/CSS/JS     │       │ Route / Flight APIs  │
└─────────────────┘       └──────────┬───────────┘
                                     │
                                     ▼
                              ┌───────────────┐
                              │ Azure Table   │
                              │ Storage       │
                              └───────┬───────┘
                                      ▲
                                      │
                              ┌───────┴────────┐
                              │ Timer Function │
                              │ Daily Monitor  │
                              └───────┬────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │ Azure Communication    │
                         │ Services Email         │
                         └────────────────────────┘
```

### HTTP Function App

The HTTP Function App powers the interactive website.

It is responsible for:

- Fetching tracked routes
- Adding routes
- Fetching individual flight details
- Returning stored price data
- Returning stored flight data
- Adding email subscribers
- Deleting tracked routes

When a route is added, the backend queries SerpAPI, processes the returned flight options, and stores the route and individual flight information in Azure Table Storage.

### Timer Function App

The Timer Function App runs automatically and checks tracked routes periodically.

It is responsible for:

- Re-checking live flight frequency
- Detecting frequency increases or decreases
- Detecting flights that are no longer present
- Detecting newly available flights
- Updating stored route information
- Sending change notifications
- Removing expired routes
- Avoiding unnecessary API calls for expired routes

The HTTP and Timer workloads are kept separate so that interactive requests do not interfere with the background monitoring process.

### Azure Table Storage

Azure Table Storage is used as the application's persistent data layer.

The project uses tables for route-level and flight-level information, including:

- Route
- Departure and arrival information
- Flight frequency
- Lowest price
- Price history
- Airline
- Flight number
- Aircraft
- Departure time
- Arrival time
- Airline logo
- Individual flight price

The schemaless model keeps the storage layer lightweight while fitting the route and flight lookup patterns used by the application.

### Static Frontend

The frontend is a self-contained HTML/CSS/JavaScript application.

The interface is designed around an airport departure-board aesthetic and includes:

- World view with an interactive globe showing tracked routes
- List view for browsing routes without the globe
- Route colors that distinguish tracking modes
- Selectable globe routes with route details, including lowest price and weekly frequency
- Route cards with departure and arrival city imagery
- Complementary diagonal image edges for the departure and arrival visuals
- Expandable flight details
- Airline logos
- Flight prices
- Aircraft information
- 24-hour day/night flight timeline
- Departure and arrival markers
- Price-history graph
- Route frequency information
- Add-route and delete-route workflows
- Voice-assisted route entry
- Email subscription workflow

## SerpAPI integration

SerpAPI is a core part of Gatewatch rather than an additional cosmetic API integration.

Gatewatch uses the Google Flights engine to retrieve live flight options. The returned data is processed into route-level and flight-level records.

The application uses:

- `best_flights`
- `other_flights`
- Flight numbers
- Airlines
- Aircraft
- Departure and arrival times
- Flight duration
- Flight prices
- Airline logos
- Price insights
- Price history

SerpApi's Google Flights results expose flight options through `best_flights` and `other_flights`, while its Price Insights response provides timestamped `price_history` values that can be used to visualize price movement over time. citeturn0search5turn0search0

Gatewatch combines the available flight arrays when building its route-level flight set so that the monitored route represents the returned flight options rather than only the highlighted results.

## Route intelligence

The main value of Gatewatch comes from comparing route snapshots over time.

For example:

```text
Monday
BLR → LHR
18 flights
Lowest price: ₹37,000

        ↓ daily monitoring

Tuesday
BLR → LHR
17 flights
Lowest price: ₹42,000

        ↓

Gatewatch detects:
- Frequency decreased
- Lowest price increased
- A flight may have been removed
```

This makes the application useful for travelers who want to monitor a route rather than repeatedly perform the same search manually.

## Price history

Gatewatch can store price-history data returned by SerpAPI and display it as a compact graph in the route details section.

The history is represented as timestamp/price pairs:

```text
[
  [timestamp, price],
  [timestamp, price],
  [timestamp, price]
]
```

The frontend turns these points into a responsive SVG sparkline showing the movement of the route price over time.

SerpApi documents `price_insights.price_history` as timestamped price points where each entry contains a timestamp followed by the corresponding price. citeturn0search0

## Engineering decisions

### Quota isolation

The interactive route-add operation and the background monitoring operation use separate SerpApi keys.

This prevents interactive testing or heavy website usage from consuming the quota required by the scheduled monitoring system.

### Failure handling

The monitoring system distinguishes between:

- A successful response containing zero flights
- An unsuccessful upstream API request
- A route that has genuinely changed

This prevents an upstream API failure from being interpreted as a route with zero flights.

### Expired-route handling

Routes whose travel date has passed are removed or skipped before unnecessary monitoring work is performed.

This avoids spending API quota on routes that are no longer relevant.

### Flight-level tracking

Gatewatch stores individual flight information rather than only storing a route-level frequency.

This makes it possible to compare the actual flight set between monitoring runs and detect flights that have been added or removed.

### Responsive timeline

Each flight has a 24-hour local-time timeline showing:

- Day and night
- Departure time
- Arrival time
- Flight duration
- Flight path
- Departure and arrival markers
- Local timezone information

The timeline is independent of the flight duration, so the complete 24-hour day remains visible for every flight.

### Security trade-off

The application uses a shared access code for protected route-management operations.

This is suitable for the current single-user/personal deployment, but it is not intended to be a full multi-user authentication system.

## Repository structure

```text
.
├── http-function/       # HTTP-triggered Azure Function App
├── timer-function/      # Timer-triggered Azure Function App
└── frontend/            # Static HTML/CSS/JS frontend
```

## Tech stack

**Backend**

- Python
- Azure Functions
- HTTP triggers
- Timer triggers
- Azure Table Storage
- Azure Communication Services Email
- SerpAPI Google Flights API

**Frontend**

- HTML
- CSS
- Vanilla JavaScript
- SVG for the price-history graph and route visualizations
- Interactive globe and route selection
- MediaRecorder API for voice capture

**Infrastructure**

- Microsoft Azure
- Azure Static Web Apps
- Azure Functions
- Azure Table Storage
- GitHub-based deployment

## Prerequisites

- An Azure subscription
- Azure Functions Core Tools
- Python 3.x compatible with the selected Azure Functions runtime
- A SerpAPI account
- Separate SerpApi keys for interactive and scheduled workloads
- Azure Communication Services with Email enabled
- A verified email sender/domain
- A GitHub repository for deployment

## Azure resources

| Resource | Purpose |
|---|---|
| Storage account | Stores Azure Tables and supports the Function Apps |
| HTTP Function App | Serves the frontend API |
| Timer Function App | Performs scheduled route monitoring |
| Azure Communication Services | Sends route and frequency notifications |
| Static Web App | Hosts the Gatewatch frontend |

## Environment variables

Configure these values in each Function App under:

`Configuration → Application settings`

Do not rely on `local.settings.json` for production deployment.

### Timer Function App

| Variable | Purpose |
|---|---|
| `AzureWebJobsStorage` | Azure Storage connection |
| `SERPAPI_KEY` | SerpAPI key used by scheduled monitoring |
| `ACS_EMAIL_KEY` | Azure Communication Services access key |
| `ACS_ENDPOINT` | Azure Communication Services endpoint |

### HTTP Function App

| Variable | Purpose |
|---|---|
| `AzureWebJobsStorage` | Azure Storage connection |
| `ACCESS_CODE` | Shared secret for protected operations |
| `Serp_API2` | Separate SerpAPI key used by interactive route operations |
| `ACS_EMAIL_KEY` | Azure Communication Services access key |
| `ACS_ENDPOINT` | Azure Communication Services endpoint |

If additional AI or external-service functionality is enabled in a deployment, its credentials should be stored as Function App application settings rather than committed to the repository.

## API endpoints

The frontend communicates with the HTTP-triggered Function App through the following routes:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/fetch_route` | Fetch tracked route information |
| `GET` | `/api/fetch_flight` | Fetch flight-level information for a route |
| `GET` | `/api/fetch_price_data` | AI analysis of the pricing, tells whether it is a good time to book |
| `GET` | `/api/fetch_flight_data` | Analysis of the airline, aircraft, and route served |
| `POST` | `/api/add_route` | Add and initialize a tracked route |
| `POST` | `/api/add_email` | Add an email subscriber |
| `DELETE` | `/api/delete_route` | Remove a tracked route |
| `POST` | `/api/voice_text` | Extract departure, arrival, and date from a voice recording |

The `OPTIONS` field for route tracking modes is a numeric value:

| Value | Tracking mode |
|---:|---|
| `1` | New flights only |
| `2` | New flights and price changes |

Send these values as JSON numbers, not descriptive strings.

The `POST /api/voice_text` endpoint accepts raw WebM audio and uses Gemini to extract departure airport, arrival airport, and travel date. It returns JSON with `DEP`, `ARR`, and `DATE` fields. After successful recognition, the frontend uses this response to populate the route form.

Protected operations use the configured access mechanism implemented by the HTTP Function App.

## Local development

The frontend can be tested locally without changing the production API.

From the frontend directory:

```bash
python -m http.server 5500
```

Then open:

```text
http://localhost:5500
```

If the browser blocks API requests, verify that the Azure Function App CORS configuration allows the local development origin.

## Backend deployment

Deploy the two Function Apps independently:

```bash
cd http-function
func azure functionapp publish <your-http-function-app-name>
```

Then:

```bash
cd ../timer-function
func azure functionapp publish <your-timer-function-app-name>
```

## Frontend deployment

Create an Azure Static Web App and connect it to the GitHub repository.

Use:

```text
App location: frontend/
```

The Static Web App can then deploy the frontend automatically whenever changes are pushed to the configured branch.

## Data flow

### Adding a route

```text
User enters route
        |
        v
HTTP Function
        |
        v
SerpAPI Google Flights
        |
        v
Process flight options
        |
        +----> MasterTable
        |
        +----> AirlineDetails
        |
        v
Frontend displays route
```

### Monitoring a route

```text
Timer trigger
      |
      v
Read tracked routes
      |
      v
Check route date
      |
      v
Query SerpAPI
      |
      v
Compare current and stored data
      |
      +----> Frequency changed
      |
      +----> Flight added/removed
      |
      +----> Price changed
      |
      v
Update storage
      |
      v
Send email notification when required
```

## Project goals

Gatewatch is designed around five main goals:

1. Monitor flight routes instead of performing one-time searches.
2. Detect meaningful changes in flight availability and frequency.
3. Track price movement over time.
4. Notify users when something important changes.
5. Keep the system lightweight, serverless, and cost-conscious.
