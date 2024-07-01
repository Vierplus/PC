# Defined Imports
import DoBotArm as Dbt
import socket
import time
import asyncio
import pymongo
from asyncua import Client
import requests
from datetime import datetime, timezone

# MongoDB connection URI (replace with your MongoDB URI
mongo_uri = "mongodb://vierplus:4plus@100.108.16.72:27017/VM_DB?authSource=admin"
client = pymongo.MongoClient(mongo_uri)

# Select database and collection
db = client.get_database()
collection = db.get_collection("Data_Collection")
    
# Dice positions
dice_positions = {
    "1": (255, -63, 50),
    "2": (255, -20, 50),
    "3": (255, 16, 50),
    "4": (255, 59, 50)
}

# Step area between home and drop areas
step_area = (177, -182, 50)

# Drop area coordinates
drop_areas = {
    "red": (-47, -243, -42),
    "blue": (-6, -243, -42),
    "green": (31, -243, -42),
    "yellow": (73, -244, -42)
}

hover_areas = {color: (x, y) for color, (x, y, z) in drop_areas.items()}

# Camera position
camera_pos = (176, 215, 50)

# function to move dice to the drop area
def move_to_drop_area(ctrlBot, step_area, hover_area, drop_area):
    ctrlBot.moveArmXYZ(*step_area)
    ctrlBot.moveArmXY(*hover_area)
    ctrlBot.moveArmXYZ(*drop_area)
    time.sleep(1)
    ctrlBot.toggleSuction()
    ctrlBot.moveArmXY(*hover_area)
    ctrlBot.moveArmXYZ(*step_area)
    ctrlBot.moveHome()

def get_current_awattar_prices():
    url = "https://api.awattar.at/v1/marketdata"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        current_time = datetime.now(timezone.utc)
        prices = data.get('data', [])

        for price_entry in prices:
            start_time = datetime.fromtimestamp(price_entry['start_timestamp'] / 1000, timezone.utc)
            end_time = datetime.fromtimestamp(price_entry['end_timestamp'] / 1000, timezone.utc)

            if start_time <= current_time <= end_time:
                return price_entry['marketprice'] / 10  # Umrechnung in Cent/kWh
    else:
        print(f"Fehler bei der API-Abfrage: {response.status_code}")
        return None

async def opcua_client(url, namespace, device_name, temperature_name, humidity_name):
    client = Client(url=url, timeout=10)
    await client.connect()

    try:
        nsidx = await client.get_namespace_index(namespace)
        print(f"Namespace Index for '{namespace}': {nsidx}")

        temperature_var = await client.nodes.root.get_child(
            ["0:Objects", f"{nsidx}:Raspi", f"{nsidx}:{device_name}", f"{nsidx}:{temperature_name}"]
        )
        humidity_var = await client.nodes.root.get_child(
            ["0:Objects", f"{nsidx}:Raspi", f"{nsidx}:{device_name}", f"{nsidx}:{humidity_name}"]
        )

        temperature = await temperature_var.read_value()
        humidity = await humidity_var.read_value()
        
        print(f"Received temperature: {temperature}")
        print(f"Received humidity: {humidity}")
        
        return temperature, humidity
    finally:
        await client.disconnect()

async def tcp_client(host, port):
    reader, writer = await asyncio.open_connection(host, port)
    writer.write("get_hex".encode())
    await writer.drain()

    data = await reader.read(100)
    hex_value = data.decode().strip()
    print(f'Received hex value: {hex_value}')

    writer.close()
    await writer.wait_closed()
    return hex_value

def hex_to_rgb(hex_value):
    hex_value = hex_value.lstrip('#')
    if len(hex_value) != 6:
        raise ValueError("Input hex value must be 6 characters long.")
    r = int(hex_value[0:2], 16)
    g = int(hex_value[2:4], 16)
    b = int(hex_value[4:6], 16)
    return r, g, b

def get_colour_name(r_mean, g_mean, b_mean, component_no):
    current_price = get_current_awattar_prices()
    if current_price is not None:
        print(f"Aktueller Strompreis: {current_price} Cent/kWh")
    else:
        print("Keine aktuellen Preise verfügbar.")
    
    threshold = 35  # Define a threshold for how close red and green should be to each other
    component_no += 1
    # Check for blue
    if b_mean > g_mean and b_mean > r_mean:
        return "blue", component_no, current_price
    # Check for yellow (red is dominant and close enough to green)
    elif r_mean > b_mean and g_mean > b_mean and abs(r_mean - g_mean) < threshold:
        print(abs(r_mean - g_mean))
        return "yellow", component_no, current_price
    # Check for green
    elif g_mean > r_mean and g_mean > b_mean:
        print(abs(r_mean - g_mean))
        return "green", component_no, current_price
    # If none of the above conditions are true, default to red
    else:
        return "red", component_no, current_price
    

async def sortDice():

    component_no = 0
    
    # Move to home location
    home_position = (255, 0, 50)
    ctrlBot = Dbt.DoBotArm(*home_position)  # Create DoBot Class Object with home position x, y, z
    ctrlBot.moveHome()
    
    while True:
        print("--- Manual Mode ---")
        print("s - start sort mode")               # starts the sortmode where each position can be selected one by one.
        print("a - start continuous sort mode")    # start the sort mode where each position will be activated one after another.
        print("q - quit program")                  # quits the whole program, used for when the Robot did not calibrate at the beginning.
        print("c - camera position")               # Moves to camera position for setting up the camera.
        print("ä - get color")                     # activates the camera and gives back the hex code, for testing purposes.
        
        inputCoords = input("$ ")
        if inputCoords[0] == "s":
            print("Starting...")

            while True:
                print("Choose the dice to sort:")
                print("1: q13")
                print("2: q15")
                print("3: q17")
                print("4: q19")
                print("q - exit sort mode")

                dice_choice = input("$ ")

                if dice_choice in dice_positions:
                    # Pick up dice from the chosen position
                    ctrlBot.moveArmXYZ(*dice_positions[dice_choice])
                    ctrlBot.pickToggle(-43)
                    ctrlBot.toggleSuction()
                    ctrlBot.pickToggle(30)

                    ctrlBot.moveArmXYZ(*camera_pos)

                    # Receive hex value from camera
                    host = '100.84.218.109'
                    port = 8888
                    hex_value = await tcp_client(host, port)

                    # Convert hex to RGB and get color name
                    r, g, b = hex_to_rgb(hex_value)
                    color_name, component_no, current_price = get_colour_name(r, g, b, component_no)
                    print(f"The dice color is: {color_name}")

                    # Get temperature and humidity from OPC UA server
                    server_url = "opc.tcp://100.84.218.109:4840/freeopcua/server/"
                    namespace = "VierPlus"
                    device_name = "FBS-VierPlus"
                    temperature_name = "Temperature"
                    humidity_name = "Humidity"
                    temperature, humidity = await opcua_client(server_url, namespace, device_name, temperature_name, humidity_name)
                    print(f"Temperature: {temperature} °C, Humidity: {humidity} %")

                    # Get current datetime in local timezone
                    current_datetime = datetime.now()

                    # Format datetime as string with 24-hour format
                    formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

                    # Save data to MongoDB
                    data_to_insert = {
                        "current_price": current_price * 0.2,
                        "component_no": component_no,
                        "measurement_timestamp": formatted_datetime,
                        "component_color_hex": hex_value,
                        "component_color_name": color_name,
                        "current_temp_c": temperature,
                        "current_humidity": humidity
                    }
                    result = collection.insert_one(data_to_insert)
                    print(f"Data saved to MongoDB with ID: {result.inserted_id}")
                    
                    ctrlBot.moveHome()

                    if color_name in drop_areas:
                        move_to_drop_area(ctrlBot, step_area, hover_areas[color_name], drop_areas[color_name])
                elif dice_choice == "q":
                    break
                else:
                    print("Unknown command")
        
        elif inputCoords[0] == "q":
            ctrlBot.moveHome()
            ctrlBot.dobotDisconnect()
            exit()
        
        elif inputCoords[0] == "a":
            for i in dice_positions:
                # Pick up dice from the chosen position
                ctrlBot.moveArmXYZ(*dice_positions[i])
                ctrlBot.pickToggle(-43)
                ctrlBot.toggleSuction()
                ctrlBot.pickToggle(30)

                ctrlBot.moveArmXYZ(*camera_pos)

                # Receive hex value from camera
                host = '100.84.218.109'
                port = 8888
                hex_value = await tcp_client(host, port)

                # Convert hex to RGB and get color name
                r, g, b = hex_to_rgb(hex_value)
                color_name, component_no, current_price = get_colour_name(r, g, b, component_no)
                print(f"The dice color is: {color_name}")

                # Get temperature and humidity from OPC UA server
                server_url = "opc.tcp://100.84.218.109:4840/freeopcua/server/"
                namespace = "VierPlus"
                device_name = "FBS-VierPlus"
                temperature_name = "Temperature"
                humidity_name = "Humidity"
                temperature, humidity = await opcua_client(server_url, namespace, device_name, temperature_name, humidity_name)
                print(f"Temperature: {temperature} °C, Humidity: {humidity} %")

                # Get current datetime in local timezone
                current_datetime = datetime.now()

                # Format datetime as string with 24-hour format
                formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

                # Save data to MongoDB
                data_to_insert = {
                    "current_price": current_price * 0.2,
                    "component_no": component_no,
                    "measurement_timestamp": formatted_datetime,
                    "component_color_hex": hex_value,
                    "component_color_name": color_name,
                    "current_temp_c": temperature,
                    "current_humidity": humidity
                }
                result = collection.insert_one(data_to_insert)
                print(f"Data saved to MongoDB with ID: {result.inserted_id}")

                ctrlBot.moveHome()

                if color_name in drop_areas:
                    move_to_drop_area(ctrlBot, step_area, hover_areas[color_name], drop_areas[color_name])
        
        elif inputCoords[0] == "c":
            ctrlBot.moveArmXYZ(*camera_pos)
            input()
            ctrlBot.moveHome()
        
        elif inputCoords[0] == "ä":
                # Receive hex value from camera
                host = '100.84.218.109'
                port = 8888
                hex_value = await tcp_client(host, port)

                # Convert hex to RGB and get color name
                r, g, b = hex_to_rgb(hex_value)
                color_name, component_no, current_price = get_colour_name(r, g, b, component_no)
                print(f"The dice color is: {color_name}")
        else:
            print("Unknown command")
            print("--------------------------------------------------------------------")

#--Main Program--
def main():
    asyncio.run(sortDice())

main()
