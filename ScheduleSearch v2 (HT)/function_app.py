import os
import logging
import json
import requests
import tempfile
from google import genai
from datetime import datetime
from zoneinfo import ZoneInfo
import azure.functions as func
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient
from azure.communication.email import EmailClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceExistsError
from azure.core.exceptions import ResourceNotFoundError

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
                    "ARR_IMG":entity["ARR_IMG"],
                    "OPTIONS":entity["OPTIONS"]})

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
                                "Duration":entity["TIME"],
                                "Price":entity["PRICE"]})

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
    price_history = entity["PRICE_HISTORY"]

    prompt = f"""
    You are the travel advisory AI.
    Provide a concise, data-backed flight-booking recommendation for the route {dep} to {arr} for travel on {date}.

    Data Inputs:
    - 60-Day Price History (INR): {price_history}
    - Target Travel Date: {date}

    Analysis Requirements:
    1. **Price Trajectory:** Evaluate the 60-day trend to see if current rates are stabilizing, climbing, or dropping relative to recent history.
    2. **Demand Factors:** Identify relevant global events, holidays, conferences, or seasonal shifts around {date} in or connecting through {dep} and {arr}.
    3. **Timing Verdict:** Synthesize the numerical price action and external event pressures to assess whether to book now or wait.

    Formatting & Tone Constraints:
    - Write in a natural, conversational, yet professional style.
    - Organize using short sections with clear headings.
    - Use short paragraphs instead of long lists of bullet points.
    - Do NOT output raw data dumps, technical specification sheets, or rigid enumerations.
    - Clearly distinguish between historical price patterns and future event-driven expectations.
    - Do not guarantee price movements or claim absolute certainty.
    - Keep the final assessment practical and directly useful for a traveler making a decision.
    """
    response = gemini_client.models.generate_content(
    model="gemini-3.1-flash-lite",
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
    You are the flight information assistant.
    A traveller is about to book or fly on this specific flight and wants
    to know exactly what to expect — not just specs, but the real experience.

    Flight: {rk}
    Airline: {airline}
    Aircraft: {aircraft}
    Route: {dep} → {arr}
    Departure: {departure}
    Arrival: {arrival}

    Your job is to give them a warm, honest, traveller-focused briefing.
    Draw on what is generally known about this airline and aircraft type.

    Cover all of the following:

    AIRLINE
    - What kind of airline is this? (budget, full-service, hybrid)
    - What is the airline's general reputation among passengers?
    - Any standout strengths or common complaints travellers mention?

    AIRCRAFT
    - What is this aircraft like to fly on in plain terms?
    - Cabin width, seat comfort, window size, noise levels — anything
    that affects how the journey feels.
    - Is this aircraft considered modern or aging for this route?

    CABIN & SEATING
    - What cabin classes are available on this aircraft?
    - What are the seat pitch, width and recline like in each class?
    - Are there lie-flat beds, extra legroom options or premium economy?
    - Window, middle or aisle — any seating tips for this aircraft?

    FOOD & DRINK
    - Is food included or paid separately on this airline?
    - What is the quality and variety like for each cabin class?
    - Any specific meals or drinks this airline is known for?

    ENTERTAINMENT & CONNECTIVITY
    - Is there a seatback screen or does the airline use an app/streaming?
    - Is Wi-Fi available and what is it like (speed, cost, reliability)?
    - Are there USB/power outlets at every seat?

    WHAT TO PACK / PRACTICAL TIPS
    - Anything specific a traveller should bring or prepare for?
    - Any quirks about this airline's check-in, boarding or baggage policy
    that are worth knowing in advance?

    WRITING RULES:
    - Write in a warm, honest and conversational tone — like a well-travelled
    friend giving advice, not a brochure.
    - Use short paragraphs under clear headings. No long bullet lists.
    - Be specific where you can. Vague generalities are not helpful.
    - If something varies or cannot be confirmed, say so briefly and move on.
    - Do not invent reviews or ratings. Describe what is generally known.
    - Do not present typical configurations as guaranteed for this flight.
    - End with one practical sentence the traveller should remember.
    - Keep the total response between 350–450 words.
    """
    response = gemini_client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents=prompt)

    return func.HttpResponse(json.dumps({"analysis": response.text}),mimetype="application/json",status_code=200)

@app.route(route="add_email",methods=['POST'])
def add_email(req: func.HttpRequest) -> func.HttpResponse:

    CONTAINER_NAME = "gatewatchemail"
    BLOB_NAME = "subscribers.json"
    blob_service = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
    blob = blob_service.get_container_client(CONTAINER_NAME).get_blob_client(BLOB_NAME)
    master_email=json.loads(blob.download_blob().readall())
    

    data = req.get_json()
    email = data.get("email", "").strip().lower()
    
    if not email or "@" not in email:
        return func.HttpResponse("Invalid email", status_code=400)

    if email in master_email:
        return func.HttpResponse("Already subscribed", status_code=409)

    
    master_email.append(email)
    blob_service.get_container_client(CONTAINER_NAME).get_blob_client(BLOB_NAME).upload_blob(json.dumps(master_email), overwrite=True)
    message = {
                "senderAddress": "DoNotReply@b69c3249-d05b-47d9-a9a3-9fc4b60755d6.azurecomm.net",
                "recipients": {
                    "bcc": [{"address": email}]
                },
                "content": {
                    "subject": "Your subscription is confirmed!",
                    "html": f"""
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    </head>

                    <body style="
                        margin:0;
                        padding:0;
                        background-color:#1B1E20;
                        font-family:'IBM Plex Sans', Arial, Helvetica, sans-serif;
                    ">

                    <table role="presentation"
                        width="100%"
                        cellpadding="0"
                        cellspacing="0"
                        border="0"
                        style="background-color:#1B1E20; padding:40px 16px;">

                        <tr>
                            <td align="center">

                                <table role="presentation"
                                    width="560"
                                    cellpadding="0"
                                    cellspacing="0"
                                    border="0"
                                    style="
                                        width:100%;
                                        max-width:560px;
                                        background-color:#24282B;
                                        border:1px solid #4FD1A5;
                                        border-radius:8px;
                                    ">

                                    <!-- Envelope -->
                                    <tr>
                                        <td align="center"
                                            style="padding:42px 20px 24px;">

                                            <table role="presentation"
                                                cellpadding="0"
                                                cellspacing="0"
                                                border="0"
                                                width="100"
                                                style="
                                                    width:100px;
                                                    border:2px solid #4FD1A5;
                                                    border-radius:5px;
                                                    background-color:#1B2924;
                                                ">

                                                <tr>
                                                    <td align="center"
                                                        style="
                                                            height:65px;
                                                            color:#4FD1A5;
                                                            font-size:32px;
                                                            line-height:65px;
                                                        ">
                                                        ✉
                                                    </td>
                                                </tr>

                                            </table>

                                        </td>
                                    </tr>

                                    <!-- You're in -->
                                    <tr>
                                        <td align="center"
                                            style="
                                                padding:5px 30px 0;
                                                color:#4FD1A5;
                                                font-family:'IBM Plex Sans', Arial, Helvetica, sans-serif;
                                                font-size:34px;
                                                font-weight:600;
                                            ">
                                            You're in!
                                        </td>
                                    </tr>

                                    <!-- Subtitle -->
                                    <tr>
                                        <td align="center"
                                            style="
                                                padding:14px 30px 0;
                                                color:#E8E6E1;
                                                font-family:'IBM Plex Sans', Arial, Helvetica, sans-serif;
                                                font-size:18px;
                                                font-weight:400;
                                            ">
                                            Thank you for subscribing!
                                        </td>
                                    </tr>

                                    <!-- Description -->
                                    <tr>
                                        <td align="center"
                                            style="
                                                padding:32px 45px 44px;
                                                color:#8B9094;
                                                font-family:'IBM Plex Sans', Arial, Helvetica, sans-serif;
                                                font-size:14px;
                                                line-height:1.6;
                                            ">
                                            We'll keep you updated with flight deals,
                                            price changes and travel updates.
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
    return func.HttpResponse("New Email added successfully", status_code=201)

@app.route(route="voice_text", methods=['POST'])
def voice_text(req: func.HttpRequest) -> func.HttpResponse:

    client = genai.Client(api_key=os.environ["Gemini_API"])
    audio_file = req.get_body()

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_audio:
        temp_audio.write(audio_file)
        audio_path = temp_audio.name

    audio_file = client.files.upload(file=audio_path)
    interaction = client.interactions.create(model="gemini-3.5-transcribe",
    input=[
        {
            "type": "audio",
            "uri": audio_file.uri,
            "mime_type": audio_file.mime_type,
        }
    ],
    )
    spoken_text = interaction.output_text
    os.remove(audio_path)
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()

    rules=f"""
            Today's date is {today.isoformat()}
            Extract the departure city, arrival city and travel date
            from the following speech:

            {spoken_text}
            Return ONLY a JSON object with these exact fields:
            {{
                "DEP": "<IATA code or empty string>",
                "ARR": "<IATA code or empty string>",
                "DATE": "<YYYY-MM-DD or empty string>"
            }}
            
            Rules:
            - Convert city names to IATA airport codes (Mumbai=BOM, Delhi=DEL, Dubai=DXB, London=LHR, Singapore=SIN, etc.)
            - "next month" means the 1st of next month
            - "next week" means 7 days from today
            - "in 2 weeks" means 14 days from today
            - If something cannot be determined, use empty string
            - Return ONLY the JSON, no explanation

            Example:
            {{
            "DEP": "BLR",
            "ARR": "DXB",
            "DATE": "2026-12-11"
            }}
            """

    response = client.models.generate_content(model="gemini-2.0-flash",contents=rules)

    route_data = json.loads(response.text)

    return func.HttpResponse(json.dumps(route_data),mimetype="application/json",status_code=200,)


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
        options=data1["OPTIONS"]
        
        api_key= os.environ["Serp_API2"]
        response = requests.get("https://serpapi.com/search.json?engine=google_flights&departure_id="+dep+"&arrival_id="+arr+"&gl=in&hl=en&currency=INR&type=2&outbound_date="+date3+"&show_hidden=true&adults=1&stops=1&api_key="+api_key)
        data2=response.json()
        best_flights = data2.get("best_flights", [])
        other_flights = data2.get("other_flights", [])
        all_flights = best_flights + other_flights

        rk=dep+arr+date3

        try:
            table_client.get_entity(partition_key="Route",row_key=rk)

            return func.HttpResponse("This route and date is already being tracked",status_code=409)

        except ResourceNotFoundError:
            pass

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
                    "ARR_IMG":arr_image or "",
                    "OPTIONS":options
                }

        try:
            table_client.create_entity(new_entity)
        except ResourceExistsError:
            return func.HttpResponse("Could not add route", status_code=409)

        for flight in all_flights:
            segment = flight["flights"][0]

            airline=segment["airline"]
            airline_logo=flight.get("airline_logo", "")
            airplane=segment.get("airplane","")
            rk2=segment.get("flight_number","")

            dep2=segment["departure_airport"]["time"]
            arr2=segment["arrival_airport"]["time"]
            duration = flight.get("total_duration", 0)
            price2 = flight.get("price", 0)


            new_entity2 = {"PartitionKey":rk,
                            "RowKey":rk2,
                            "AIRLINE":airline,
                            "AIRCRAFT":airplane,
                            "DEPT":dep2,
                            "ARRT":arr2,
                            "AIRLINE_LOGO":airline_logo,
                            "TIME":duration,
                            "PRICE":price2}
            table_client2.create_entity(new_entity2)
            

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