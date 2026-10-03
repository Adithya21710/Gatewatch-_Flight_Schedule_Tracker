import os
import logging
import json
import requests
from google import genai
import azure.functions as func
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient
from azure.communication.email import EmailClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceExistsError

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

#For Azure Table
storage_key=os.environ.get('AzureWebJobsStorage')
#For ACS
credential = AzureKeyCredential(os.environ["ACS_EMAIL_KEY"])
endpoint=os.environ["ACS_ENDPOINT"]
client = EmailClient(endpoint,credential)

@app.route(route="fetch_route",methods=["GET"])
def fetch_route(req: func.HttpRequest) -> func.HttpResponse:
    table_service = TableServiceClient.from_connection_string(conn_str=storage_key)
    table_client = table_service.get_table_client("MasterTable")
    

    routelist=[]

    entities=table_client.list_entities()
    for entity in entities:
        routelist.append({"PartitionKey": entity["PartitionKey"],
                    "RowKey": entity["RowKey"],
                    "DEP":entity["DEP"],
                    "ARR":entity["ARR"],
                    "FREQ":entity["FREQ"],
                    "DATE":entity["DATE"],
                    "PRICE_HISTORY":entity["PRICE_HISTORY"],
                    "LOWEST_PRICE":entity["LOWEST_PRICE"],
                    "PRICE_LEVEL":entity["PRICE_LEVEL"],
                    "CHEAPEST_PRICE":entity["CHEAPEST_PRICE"],
                    "CHEAPEST_AIRLINE":entity["CHEAPEST_AIRLINE"],
                    "CHEAPEST_AIRLINE_LOGO":entity["CHEAPEST_AIRLINE_LOGO"],
                    "CHEAPEST_FLIGHT_NUMBER":entity["CHEAPEST_FLIGHT_NUMBER"],
                    "DEP_IMG":entity["DEP_IMG"],
                    "ARR_IMG":entity["ARR_IMG"]})

    return func.HttpResponse(json.dumps(routelist), status_code=200)

@app.route(route="fetch_flight",methods=['GET'])
def fetch_flight(req: func.HttpRequest) -> func.HttpResponse:
    table_service = TableServiceClient.from_connection_string(conn_str=storage_key)
    table_client = table_service.get_table_client("AirlineDetails")

    dep=req.params.get("DEP")
    arr=req.params.get("ARR")
    date=req.params.get("DATE")
    rk=dep+arr+date 

    entities=table_client.list_entities()

    routelist2=[]

    for entity in entities:
        if rk==entity["PartitionKey"]:
            routelist2.append({"PartitionKey": entity["PartitionKey"],
                               "Flight_Number":entity["RowKey"],
                                "RowKey": entity["RowKey"],
                                "Airline":entity["AIRLINE"],
                                "Aircraft":entity["AIRCRAFT"],
                                "DEPT":entity["DEPT"],
                                "ARRT":entity["ARRT"],
                                "Airline_Logo":entity["AIRLINE_LOGO"],
                                "Duration":entity["TIME"]})

    return func.HttpResponse(json.dumps(routelist2), status_code=200)

@app.route(route="fetch_price_data",methods=['GET'])
def fetch_price_data(req: func.HttpRequest) -> func.HttpResponse:
    gemini_client = genai.Client(api_key=os.environ["Gemini_API"])
    table_service = TableServiceClient.from_connection_string(conn_str=storage_key)
    table_client = table_service.get_table_client("MasterTable")
    dep=req.params.get("DEP")
    arr=req.params.get("ARR")
    date=req.params.get("DATE")
    rk=dep+arr+date

    entity = table_client.get_entity(partition_key="Route",row_key=rk)
    price_history = entity["PRICE_LEVEL"]

    prompt = f"""
    You are the price-analysis AI for GATEWATCH INDIA.
    Analyze the following historical flight-price data on the route {dep}-{arr}.

    Each entry is:[timestamp, price_in_INR]

    Data:{price_history}

    Tasks:
    1. Convert the timestamps into dates.
    2. Identify the minimum, maximum and average price.
    3. Identify significant price increases and decreases.
    4. Identify periods where the price remained relatively low.
    5. Compare the current price with the historical prices.
    6. Based ONLY on the historical pattern, assess whether the
    current price appears relatively low, typical, or high.
    7. Give a booking-timing assessment based on the observed
    historical pattern.

    Important:
    Do NOT produce a long list of bullet points.
    - Do NOT give a technical specification sheet.
    - Use a natural, conversational style.
    - Organize the answer into a few short sections with clear headings.
    - Prefer short paragraphs over bullet points.
    - Keep the entire response concise and easy to scan.
    - Focus on information that is actually useful to a traveller.
    - Do not guarantee that prices will fall or rise.
    - Do not claim to predict the future with certainty.
    - Do not invent information that isn't present in the data.
    - Clearly distinguish historical observations from future expectations.
    - Keep the final assessment concise and useful to a traveller.
    """
    response = gemini_client.models.generate_content(
    model="gemini-3.8-flash",
    contents=prompt)

    return func.HttpResponse(json.dumps({"analysis": response.text}),mimetype="application/json",status_code=200)

@app.route(route="fetch_flight_data",methods=['GET'])
def fetch_flight_data(req: func.HttpRequest) -> func.HttpResponse:
    gemini_client = genai.Client(api_key=os.environ["Gemini_API"])
    table_service = TableServiceClient.from_connection_string(conn_str=storage_key)
    table_client = table_service.get_table_client("AirlineDetails")
    dep=req.params.get("DEP")
    arr=req.params.get("ARR")
    date=req.params.get("DATE")
    rk=req.params.get("RowKey")
    pk=dep+arr+date

    entity = table_client.get_entity(partition_key=pk,row_key=rk)

    aircraft = entity["AIRCRAFT"]
    airline = entity["AIRLINE"]
    departure = entity["DEPT"]
    arrival = entity["ARRT"]

    prompt = f"""
    You are the flight information assistant for GATEWATCH INDIA.

    Give the traveller a concise, friendly and easy-to-read overview of this
    specific flight:

    Flight: {rk}
    Airline: {airline}
    Aircraft: {aircraft}
    Route: {dep} → {arr}
    Departure: {departure}
    Arrival: {arrival}

    The goal is to help a traveller understand what their journey will be like.

    Cover the most useful information about:

    - The aircraft and what it is like to fly on.
    - The cabin classes that are normally available and the main difference
    between them.
    - Meals and drinks passengers can typically expect.
    - Seats, entertainment, Wi-Fi/connectivity and charging facilities.
    - The general passenger experience on this route.

    IMPORTANT:
    - Do NOT produce a long list of bullet points.
    - Do NOT give a technical specification sheet.
    - Use a natural, conversational style.
    - Organize the answer into a few short sections with clear headings.
    - Prefer short paragraphs over bullet points.
    - Keep the entire response concise and easy to scan.
    - Focus on information that is actually useful to a traveller.
    - Mention only the most relevant aircraft specifications.
    - Clearly distinguish between information that is typical and information
    that is confirmed for this particular flight.
    - Aircraft configurations, meals, seats, Wi-Fi and entertainment can vary
    by airline and aircraft, so do not present typical information as
    guaranteed.
    - Do not invent information. If something cannot be reliably determined,
    simply say that it may vary or is not available.

    Suggested structure:

    ### Your Flight
    Briefly introduce the flight, airline, aircraft and route.

    ### The Aircraft
    Give a short, traveller-focused description of the aircraft and what
    passengers can generally expect onboard.

    ### Cabin & Service
    Briefly explain the available cabin classes, seating experience,
    meals/drinks and onboard services.

    ### What to Expect
    Give a short overall impression of the passenger experience on this
    journey, including anything particularly useful for a traveller.

    End with a one-sentence practical takeaway for the passenger.

    Keep the response around 250–350 words maximum.
    """
    response = gemini_client.models.generate_content(
    model="gemini-3.8-flash",
    contents=prompt)

    return func.HttpResponse(json.dumps({"analysis": response.text}),mimetype="application/json",status_code=200)

@app.route(route="add_email",methods=['POST'])
def add_email(req: func.HttpRequest) -> func.HttpResponse:

    code = req.headers.get('code')   
    e_code=os.environ.get('ACCESS_CODE')
    if code==e_code:
        data = req.get_json()
        email = data.get("email", "").strip().lower()
        if not email or "@" not in email:
            return func.HttpResponse("Invalid email", status_code=400)

        if email in master_email:
            return func.HttpResponse("Already subscribed", status_code=409)

        CONTAINER_NAME = "gatewatchemail"
        BLOB_NAME = "subscribers.json"
        blob_service = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
        blob = blob_service.get_container_client(CONTAINER_NAME).get_blob_client(BLOB_NAME)
        master_email=json.loads(blob.download_blob().readall())
        master_email.append(email)
        blob_service.get_container_client(CONTAINER_NAME).get_blob_client(BLOB_NAME).upload_blob(json.dumps(master_email), overwrite=True)
        return func.HttpResponse("New Email added successfully", status_code=201)
    else:
        return func.HttpResponse("Access denied", status_code=403)


@app.route(route="add_route", methods=['POST'])
def add_route(req: func.HttpRequest) -> func.HttpResponse:

    code = req.headers.get('code')
    e_code=os.environ.get('ACCESS_CODE')
    if code==e_code:
        table_service = TableServiceClient.from_connection_string(conn_str=storage_key)
        table_client = table_service.get_table_client("MasterTable")
        table_client2 = table_service.get_table_client("AirlineDetails")

        data1 = req.get_json()


        dep=data1["DEP"].upper()
        arr=data1["ARR"].upper()
        date3=data1["DATE"]
        
        api_key= os.environ["Serp_API2"]
        response = requests.get("https://serpapi.com/search.json?engine=google_flights&departure_id="+dep+"&arrival_id="+arr+"&gl=in&hl=en&currency=INR&type=2&outbound_date="+date3+"&show_hidden=true&adults=1&stops=1&api_key="+api_key)
        data2=response.json()
        best_flights = data2.get("best_flights", [])
        other_flights = data2.get("other_flights", [])
        all_flights = best_flights + other_flights

        rk=dep+arr+date3

        freq=len(all_flights)

        cheapest = min(all_flights, key=lambda f: f.get("price", float("inf")), default=None)

        if cheapest:
            cheapest_price = cheapest.get("price")
            cheapest_logo = cheapest.get("airline_logo")
            leg = cheapest.get("flights", [{}])[0]
            cheapest_airline = leg.get("airline")
            cheapest_flight_number = leg.get("flight_number")
        else:
            cheapest_price = cheapest_airline = cheapest_logo = cheapest_flight_number = None

        price_insights = data2.get("price_insights", {})
        lowest_price = price_insights.get("lowest_price")
        price_level = price_insights.get("price_level")
        price_history_json = json.dumps(price_insights.get("price_history", []))

        airports_list = data2.get("airports") or [{}]
        airports = airports_list[0]
        dep_image = (airports.get("departure") or [{}])[0].get("image")
        arr_image = (airports.get("arrival") or [{}])[0].get("image")
        


        new_entity={"PartitionKey":"Route",
                    "RowKey":rk,
                    "DEP":dep,
                    "ARR":arr,
                    "FREQ":freq,
                    "DATE":date3,
                    "PRICE_HISTORY":price_history_json,
                    "LOWEST_PRICE":lowest_price or 0,
                    "PRICE_LEVEL":price_level or "",
                    "CHEAPEST_PRICE":cheapest_price or 0,
                    "CHEAPEST_AIRLINE":cheapest_airline or "",
                    "CHEAPEST_AIRLINE_LOGO":cheapest_logo or "",
                    "CHEAPEST_FLIGHT_NUMBER":cheapest_flight_number or "",
                    "DEP_IMG":dep_image or "",
                    "ARR_IMG":arr_image or ""
                }

        for flight in all_flights:
            segment = flight["flights"][0]

            airline=segment["airline"]
            airline_logo=flight.get("airline_logo", "")
            airplane=segment.get("airplane","")
            rk2=segment.get("flight_number","")

            dep2=segment["departure_airport"]["time"]
            arr2=segment["arrival_airport"]["time"]
            duration = flight.get("total_duration", 0)


            new_entity2 = {"PartitionKey":rk,
                            "RowKey":rk2,
                            "AIRLINE":airline,
                            "AIRCRAFT":airplane,
                            "DEPT":dep2,
                            "ARRT":arr2,
                            "AIRLINE_LOGO":airline_logo,
                            "TIME":duration}
            table_client2.create_entity(new_entity2)
            
        
        try:
            table_client.create_entity(new_entity)
        except ResourceExistsError:
            return func.HttpResponse("This route and date is already being tracked", status_code=409)

        CONTAINER_NAME = "gatewatchemail"
        BLOB_NAME = "subscribers.json"
        blob_service = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
        blob = blob_service.get_container_client(CONTAINER_NAME).get_blob_client(BLOB_NAME)
        subscribers =  json.loads(blob.download_blob().readall())

        message = {
            "senderAddress": "DoNotReply@b69c3249-d05b-47d9-a9a3-9fc4b60755d6.azurecomm.net",
            "recipients": {
                "bcc": [{"address": email} for email in subscribers]
            },
            "content": {
                "subject": "New Prompt Added",
                "html": f"""
                <html>
                <body style="
                    margin:0;
                    padding:25px 10px;
                    background:#ffffff;
                    font-family:Arial,Helvetica,sans-serif;
                ">

                <table width="100%" cellpadding="0" cellspacing="0"
                    style="
                        max-width:1000px;
                        margin:auto;
                        background:#101418;
                    ">

                <tr>
                <td style="padding:28px;">

                    <!-- STATUS -->
                    <table cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="
                                width:8px;
                                height:42px;
                                background:#4FD1A5;
                                border-radius:4px;
                            ">
                                &nbsp;
                            </td>

                            <td style="padding-left:14px;">
                                <div style="
                                    font-family:'Courier New',monospace;
                                    font-size:10px;
                                    color:#4FD1A5;
                                    letter-spacing:.12em;
                                ">
                                    ROUTE ADDED
                                </div>

                                <div style="
                                    margin-top:5px;
                                    font-size:24px;
                                    font-weight:bold;
                                    color:#E8E6E1;
                                ">
                                    {dep} → {arr}
                                </div>
                            </td>
                        </tr>
                    </table>


                    <!-- DETAILS -->
                    <table width="100%" cellpadding="0" cellspacing="0"
                        style="
                            margin-top:25px;
                            border-top:1px solid #33383B;
                        ">

                        <tr>
                            <td style="
                                padding-top:14px;
                                font-family:'Courier New',monospace;
                                font-size:10px;
                                color:#8B9094;
                            ">
                                FREQUENCY
                            </td>

                            <td align="right"
                                style="
                                    padding-top:14px;
                                    font-family:'Courier New',monospace;
                                    font-size:15px;
                                    color:#E8E6E1;
                                ">
                                {freq}x daily
                            </td>
                        </tr>

                        <tr>
                            <td style="
                                padding-top:10px;
                                font-family:'Courier New',monospace;
                                font-size:10px;
                                color:#8B9094;
                            ">
                                EFFECTIVE DATE
                            </td>

                            <td align="right"
                                style="
                                    padding-top:10px;
                                    font-family:'Courier New',monospace;
                                    font-size:13px;
                                    color:#E8E6E1;
                                ">
                                {date3}
                            </td>
                        </tr>

                    </table>

                </td>
                </tr>
                </table>

                </body>
                </html>
                """
            },
        }
        poller = client.begin_send(message)

        return func.HttpResponse("New Prompt Added Successfully",status_code=201)
    else:
        return func.HttpResponse("Access denied", status_code=403)
    
@app.route(route="delete_route",methods=["DELETE"])
def delete_route(req: func.HttpRequest) -> func.HttpResponse:
    code = req.headers.get('code')
    
    e_code=os.environ.get('ACCESS_CODE')

    if code==e_code:
        table_service = TableServiceClient.from_connection_string(conn_str=storage_key)
        table_client = table_service.get_table_client("MasterTable")
        table_client2 = table_service.get_table_client("AirlineDetails")

        partition_key = req.params.get("PartitionKey")
        row_key = req.params.get("RowKey")

        data=table_client.get_entity(partition_key=partition_key,row_key=row_key)
        dep=data["DEP"]
        arr=data["ARR"]
        freq=data["FREQ"]
        date=data["DATE"]
        price=data["CHEAPEST_PRICE"]

        entities = table_client2.query_entities(query_filter=f"PartitionKey eq '{row_key}'")
        for entity in entities:
            table_client2.delete_entity(partition_key=entity["PartitionKey"], row_key=entity["RowKey"])

        CONTAINER_NAME = "gatewatchemail"
        BLOB_NAME = "subscribers.json"
        blob_service = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
        blob = blob_service.get_container_client(CONTAINER_NAME).get_blob_client(BLOB_NAME)
        subscribers =  json.loads(blob.download_blob().readall())

        message = {
            "senderAddress": "DoNotReply@b69c3249-d05b-47d9-a9a3-9fc4b60755d6.azurecomm.net",
            "recipients": {
                "bcc": [{"address": email} for email in subscribers]
            },
            "content": {
                "subject": f'Prompt Deleted',
                "html": f"""
                <html>
                <body style="
                    margin:0;
                    padding:25px 10px;
                    background:#ffffff;
                    font-family:Arial,Helvetica,sans-serif;
                ">

                <table width="100%" cellpadding="0" cellspacing="0"
                    style="
                        max-width:1000px;
                        margin:auto;
                        background:#101418;
                    ">

                <tr>
                <td style="padding:28px;">

                    <!-- STATUS -->
                    <table cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="
                                width:8px;
                                height:42px;
                                background:#E1554F;
                                border-radius:4px;
                            ">
                                &nbsp;
                            </td>

                            <td style="padding-left:14px;">
                                <div style="
                                    font-family:'Courier New',monospace;
                                    font-size:10px;
                                    color:#E1554F;
                                    letter-spacing:.12em;
                                ">
                                    ROUTE REMOVED
                                </div>

                                <div style="
                                    margin-top:5px;
                                    font-size:24px;
                                    font-weight:bold;
                                    color:#E8E6E1;
                                ">
                                    {dep} → {arr}
                                </div>
                            </td>
                        </tr>
                    </table>


                    <!-- DETAILS -->
                    <table width="100%" cellpadding="0" cellspacing="0"
                        style="
                            margin-top:25px;
                            border-top:1px solid #33383B;
                        ">

                        <tr>
                            <td style="
                                padding-top:14px;
                                font-family:'Courier New',monospace;
                                font-size:10px;
                                color:#8B9094;
                            ">
                                FREQUENCY
                            </td>

                            <td align="right"
                                style="
                                    padding-top:14px;
                                    font-family:'Courier New',monospace;
                                    font-size:15px;
                                    color:#E8E6E1;
                                ">
                                {freq}x daily
                            </td>
                        </tr>

                        <tr>
                            <td style="
                                padding-top:10px;
                                font-family:'Courier New',monospace;
                                font-size:10px;
                                color:#8B9094;
                            ">
                                EFFECTIVE DATE
                            </td>

                            <td align="right"
                                style="
                                    padding-top:10px;
                                    font-family:'Courier New',monospace;
                                    font-size:13px;
                                    color:#E8E6E1;
                                ">
                                {date}
                            </td>
                        </tr>

                    </table>

                </td>
                </tr>
                </table>

                </body>
                </html>
                """
            },
            
        }
        poller = client.begin_send(message)

        table_client.delete_entity(partition_key=partition_key, row_key=row_key)


        return func.HttpResponse("Sucessfully Deleted",status_code=200)
    else:
        return func.HttpResponse("Access Denied",status_code=403)