import os
import json
import logging
import requests
import azure.functions as func
from datetime import date
from azure.communication.email import EmailClient
from azure.core.credentials import AzureKeyCredential
from azure.data.tables import TableServiceClient


#For Azure Table
storage_key=os.environ.get('AzureWebJobsStorage')
#For ACS
credential = AzureKeyCredential(os.environ["ACS_EMAIL_KEY"])
endpoint=os.environ["ACS_ENDPOINT"]
client = EmailClient(endpoint,credential)


app = func.FunctionApp()


def emailfreq(dep,arr,date2,flight_number,airline,aircraft,dep_time,arr_time,airline_logo):
    message = {
            "senderAddress": "DoNotReply@b69c3249-d05b-47d9-a9a3-9fc4b60755d6.azurecomm.net",
            "recipients": {
                "bcc": [
                            {"address": "autoalpha72110@gmail.com"}
                        ]
            },
            #"content": {
            #    "subject": f'A new flight has been added by {airline} on {dep} - {arr}',
            #    "plainText": f'{airline} is adding a new flight on\n\nRoute:{dep} - {arr}\nOld Frequency: {old}x daily\nNew Frequency: {new}x daily\nDate: {date2}',
            #},
            "content": {
        "subject": f"New flight added by {airline} on {dep} - {arr}",
        "html": f""" 
        <html> 
        <body style="margin:0; padding:0; background:#101418; color:#E8E6E1; 
                    font-family:Arial, Helvetica, sans-serif;"> 

        <table width="100%" cellpadding="0" cellspacing="0" 
            style="background:#101418; padding:25px 10px;"> 
        <tr> 
        <td> 

        <table width="100%" cellpadding="0" cellspacing="0" 
            style="max-width:1000px; margin:auto;"> 
        <tr> 

        <!-- AIRLINE --> 
        <td width="25%" valign="middle" 
            style="padding:20px 10px 20px 20px;"> 

            <table cellpadding="0" cellspacing="0"> 
                <tr> 
                    <td valign="middle" style="padding-right:12px;"> 
                        <img src="{airline_logo}" 
                            width="45" 
                            height="45" 
                            alt="{airline}" 
                            style="display:block;"> 
                    </td> 

                    <td valign="middle"> 
                        <div style="font-size:18px; 
                                    font-weight:bold; 
                                    color:#E8E6E1;"> 
                            {airline} 
                        </div> 

                        <div style="font-size:17px; 
                                    margin-top:5px; 
                                    color:#F2A93B;"> 
                            {flight_number} 
                        </div> 
                    </td> 
                </tr> 
            </table> 

        </td> 


        <!-- AIRCRAFT --> 
        <td width="20%" valign="middle" 
            style="font-family:'Courier New',monospace; 
                font-size:14px; 
                color:#8B9094;"> 
            {aircraft} 
        </td> 


        <!-- FLIGHT TIMELINE --> 
        <td width="55%" valign="middle" 
            style="padding:10px 20px 10px 0;"> 

            <!-- TIMES --> 
            <table width="100%" cellpadding="0" cellspacing="0"> 
                <tr> 
                    <!-- LANDING / ARRIVAL TIME --> 
                    <td align="left" 
                        style="font-family:'Courier New',monospace; 
                            font-size:13px; 
                            color:#4FD1A5;"> 
                        {arr_time} 
                    </td> 

                    <!-- DEPARTURE TIME --> 
                    <td align="right" 
                        style="font-family:'Courier New',monospace; 
                            font-size:13px; 
                            color:#E8E6E1;"> 
                        {dep_time} 
                    </td> 
                </tr> 
            </table> 


            <!-- DOTTED FLIGHT PATH --> 
            <table width="100%" cellpadding="0" cellspacing="0" 
                style="margin-top:8px;"> 
                <tr> 

                    <td width="4%" align="left"></td> 

                    <td width="92%" 
                        style="border-top:2px dotted #8B9094; 
                            height:1px; 
                            font-size:1px; 
                            line-height:1px;"> 
                        &nbsp; 
                    </td> 

                    <td width="4%" align="right"></td> 

                </tr> 
            </table> 


            <!-- 24 HOUR DAY/NIGHT BAR --> 
            <table width="100%" cellpadding="0" cellspacing="0" 
                style="height:30px; 
                        margin-top:8px; 
                        border-radius:18px; 
                        overflow:hidden;"> 

                <tr> 

                    <!-- FULL 24-HOUR GRADIENT --> 
                    <td 
                        style="
                            height:30px;
                            background:linear-gradient(
                                90deg,
                                #252833 0%,
                                #292c36 18%,
                                #39404d 22%,
                                #7c735e 25%,
                                #d0a85a 29%,
                                #e0b45d 33%,
                                #e0b45d 68%,
                                #d0a85a 71%,
                                #7c735e 75%,
                                #39404d 78%,
                                #292c36 82%,
                                #252833 100%
                            );
                        ">
                        &nbsp;
                    </td> 

                </tr> 
            </table> 


            <!-- HOURS --> 
            <table width="100%" cellpadding="0" cellspacing="0" 
                style="font-family:'Courier New',monospace; 
                        font-size:11px; 
                        color:#8B9094; 
                        margin-top:6px;"> 

                <tr> 
                    <td align="left">00</td> 
                    <td align="center">06</td> 
                    <td align="center">12</td> 
                    <td align="center">18</td> 
                    <td align="right">24</td> 
                </tr> 

            </table> 


            <!-- TIMEZONE --> 
            <table width="100%" cellpadding="0" cellspacing="0" 
                style="font-family:'Courier New',monospace; 
                        font-size:11px; 
                        color:#8B9094; 
                        margin-top:10px;"> 

                <tr> 
                    <td align="center"> 
                        {dep} · UTC+5:30 
                    </td> 

                    <td align="center"> 
                        {arr} · UTC+1 
                    </td> 
                </tr> 

            </table> 

        </td> 

        </tr> 
        </table> 

        </td> 
        </tr> 
        </table> 

        </body> 
        </html> 
        """
}
            
        }
    logging.info(f"Email sent for frequency change on {dep}-{arr}")
    poller = client.begin_send(message)

def emailprice(dep,arr,old_price,new_price,old_airline,new_airline,old_logo,new_logo):
    if old_price<new_price:
        nameplate="increased"
    else:
        nameplate="decreased"
    message = {
            "senderAddress": "DoNotReply@b69c3249-d05b-47d9-a9a3-9fc4b60755d6.azurecomm.net",
            "recipients": {
                "bcc": [
                            {"address": "autoalpha72110@gmail.com"}
                        ]
            },
            "content": {
                "subject": f'Price has {nameplate} on {dep} - {arr}',
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
                <td style="padding:35px 28px;">

                <table width="100%" cellpadding="0" cellspacing="0">
                <tr>

                <!-- ROUTE -->
                <td width="25%" valign="middle"
                    style="padding-right:25px;">

                    <div style="
                        font-family:'Courier New',monospace;
                        font-size:11px;
                        color:#8B9094;
                        margin-bottom:7px;
                    ">
                        PRICE {nameplate.upper()}
                    </div>

                    <div style="
                        font-family:Arial,Helvetica,sans-serif;
                        font-size:22px;
                        font-weight:bold;
                        color:#E8E6E1;
                    ">
                        {dep} → {arr}
                    </div>

                </td>


                <!-- PRICE SECTION -->
                <td width="75%" valign="middle">

                    <!-- OLD / NEW PRICE -->
                    <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>

                        <!-- OLD PRICE -->
                        <td align="left"
                            style="
                                font-family:'Courier New',monospace;
                                font-size:11px;
                                color:#8B9094;
                            ">

                            OLD PRICE

                            <br>

                            <img src="{old_logo}"
                                width="24"
                                height="24"
                                alt="{old_airline}"
                                style="
                                    display:inline-block;
                                    vertical-align:middle;
                                    margin-top:7px;
                                    margin-right:5px;
                                ">

                            <span style="
                                font-size:18px;
                                color:#8B9094;
                                vertical-align:middle;
                            ">
                                ₹{old_price}
                            </span>

                            <br>

                            <span style="
                                font-size:9px;
                                color:#8B9094;
                            ">
                                {old_airline}
                            </span>

                        </td>


                        <!-- NEW PRICE -->
                        <td align="right"
                            style="
                                font-family:'Courier New',monospace;
                                font-size:11px;
                                color:{'#E1554F' if nameplate == 'increased' else '#4FD1A5'};
                            ">

                            NEW PRICE

                            <br>

                            <img src="{new_logo}"
                                width="24"
                                height="24"
                                alt="{new_airline}"
                                style="
                                    display:inline-block;
                                    vertical-align:middle;
                                    margin-top:7px;
                                    margin-right:5px;
                                ">

                            <span style="
                                font-size:18px;
                                color:{'#E1554F' if nameplate == 'increased' else '#4FD1A5'};
                                vertical-align:middle;
                            ">
                                ₹{new_price}
                            </span>

                            <br>

                            <span style="
                                font-size:9px;
                                color:#8B9094;
                            ">
                                {new_airline}
                            </span>

                        </td>

                    </tr>
                    </table>


                    <!-- HORIZONTAL PRICE BAR -->
                    <table width="100%" cellpadding="0" cellspacing="0"
                        style="margin-top:12px;">

                    <tr>

                        <td style="
                            height:12px;
                            border-radius:7px;
                            background:
                                linear-gradient(
                                    90deg,
                                    #252833 0%,
                                    #39404D 18%,
                                    {'#E1554F' if nameplate == 'increased' else '#4FD1A5'} 50%,
                                    #39404D 82%,
                                    #252833 100%
                                );
                        ">
                            &nbsp;
                        </td>

                    </tr>
                    </table>


                    <!-- CHANGE -->
                    <table width="100%" cellpadding="0" cellspacing="0"
                        style="margin-top:8px;">

                    <tr>

                        <td align="left"
                            style="
                                font-family:'Courier New',monospace;
                                font-size:9px;
                                color:#8B9094;
                            ">
                            PRICE CHANGE
                        </td>

                        <td align="right"
                            style="
                                font-family:'Courier New',monospace;
                                font-size:10px;
                                color:{'#E1554F' if nameplate == 'increased' else '#4FD1A5'};
                            ">

                            {'▲' if nameplate == 'increased' else '▼'}
                            ₹{abs(new_price - old_price)}

                        </td>

                    </tr>
                    </table>

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
    logging.info(f"Email sent for frequency change on {dep}-{arr}")
    poller = client.begin_send(message)

def emaildate(dep,arr):
    message = {
            "senderAddress": "DoNotReply@b69c3249-d05b-47d9-a9a3-9fc4b60755d6.azurecomm.net",
            "recipients": {
                "bcc": [
                            {"address": "autoalpha72110@gmail.com"}
                        ]
            },
            "content": {
                "subject": f'Date expired for route',
                "plainText": f'Date expired for {dep} - {arr} today.\n\nThe route has been dropped from database.',
            },
            
        }
    logging.info(f"Email sent for date change on {dep}-{arr}")
    poller = client.begin_send(message)

def emailerror():
    message = {
            "senderAddress": "DoNotReply@b69c3249-d05b-47d9-a9a3-9fc4b60755d6.azurecomm.net",
            "recipients": {
                "to": [{"address": "autoalpha72110@gmail.com"}]
            },
            "content": {
                "subject": f'API Fault (IN)',
                "plainText": f'API fault detected, please check immediately',
            },
            
        }
    logging.info(f"Email sent for error")
    poller = client.begin_send(message)
    
def dictcheck():
    table_service = TableServiceClient.from_connection_string(conn_str=storage_key)
    table_client = table_service.get_table_client("MasterTable")
    table_client2 = table_service.get_table_client("AirlineDetails")

    api_key= os.environ["SERPAPI_KEY"]

    entities=table_client.list_entities()
    for entity in entities:
        pk1=entity["PartitionKey"]
        rk1=entity["RowKey"]
        dep=entity["DEP"]
        arr=entity["ARR"]
        date1=entity["DATE"]
        freq=int(entity["FREQ"])
        cheapest_price=int(entity["CHEAPEST_PRICE"])
        cheapest_airline=entity["CHEAPEST_AIRLINE"]
        cheapest_airline_logo=entity["CHEAPEST_AIRLINE_LOGO"]

        if date.fromisoformat(date1) <= date.today():
                emaildate(dep,arr)
                table_client.delete_entity(partition_key=pk1, row_key=rk1)
                for entity2 in table_client2.list_entities():
                    if entity2["PartitionKey"]==rk1:
                        table_client2.delete_entity(partition_key=rk1,row_key=entity2["RowKey"])

        
        response = requests.get("https://serpapi.com/search.json?engine=google_flights&departure_id="+dep+"&arrival_id="+arr+"&gl=in&hl=en&currency=INR&type=2&outbound_date="+date1+"&show_hidden=true&adults=1&stops=1&api_key="+api_key)
        
        if response.status_code != 200:
            emailerror()
            return
        
        data=response.json()
        
        best_flights = data.get("best_flights", [])
        other_flights = data.get("other_flights", [])
        all_flights = best_flights + other_flights

        new_freq=len(all_flights)

        if freq!=new_freq:
            entity["FREQ"]=new_freq
            table_client.update_entity(entity)
            #emailfreq(dep,arr,freq,new_freq,date1)

        
        entities2 = table_client2.query_entities(query_filter=f"PartitionKey eq '{rk1}'")
        existing_flights = {entity["RowKey"]: entity for entity in entities2}

        current_flights = {}
        for itinerary in all_flights:
            for flight in itinerary.get("flights", []):
                flight_number = flight.get("flight_number")

                current_flights[flight_number] = {
                    "AIRLINE": flight.get("airline"),
                    "AIRCRAFT": flight.get("airplane"),
                    "DEPT": flight["departure_airport"]["time"],
                    "ARRT": flight["arrival_airport"]["time"],
                    "AIRLINE_LOGO": flight.get("airline_logo")
                }

        for flight_number, flight_data in current_flights.items():
            if flight_number not in existing_flights:
                new_entity2 = {"PartitionKey":rk1,
                                "RowKey":flight_number,
                                "AIRLINE":flight_data["AIRLINE"],
                                "AIRCRAFT":flight_data["AIRCRAFT"],
                                "DEPT":flight_data["DEPT"],
                                "ARRT":flight_data["ARRT"],
                                "AIRLINE_LOGO":flight_data["AIRLINE_LOGO"]}
                emailfreq(dep,arr,date1,flight_number,flight_data["AIRLINE"],flight_data["AIRCRAFT"],flight_data["DEPT"],flight_data["ARRT"],flight_data["AIRLINE_LOGO"])
             

        cheapest = min(all_flights, key=lambda f: f.get("price", float("inf")), default=None)
        cheapest_price2 = cheapest.get("price")
        cheapest_logo2 = cheapest.get("airline_logo")
        leg = cheapest.get("flights", [{}])[0]
        cheapest_airline2 = leg.get("airline")
        cheapest_flight_number2 = leg.get("flight_number")
        price_insights = data.get("price_insights", {})
        lowest_price2 = price_insights.get("lowest_price")
        price_level2 = price_insights.get("price_level")
        price_history_json2 = json.dumps(price_insights.get("price_history", []))

        if cheapest_airline!=cheapest_airline2 or cheapest_price!=cheapest_price2:
            entity["PRICE_HISTORY"]=price_history_json2
            entity["LOWEST_PRICE"]=lowest_price2
            entity["PRICE_LEVEL"]=price_level2
            entity["CHEAPEST_PRICE"]=cheapest_price2
            entity["CHEAPEST_AIRLINE"]=cheapest_airline2
            entity["CHEAPEST_AIRLINE_LOGO"]=cheapest_logo2
            entity["CHEAPEST_FLIGHT_NUMBER"]=cheapest_flight_number2
            table_client.update_entity(entity)
            emailprice(dep,arr,cheapest_price,cheapest_price2,cheapest_airline,cheapest_airline2,cheapest_airline_logo,cheapest_logo2)



@app.timer_trigger(schedule="* * * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Starting search')
    dictcheck()

    logging.info('Python timer trigger function executed.')