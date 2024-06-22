import customtkinter as ctk
import DoBotArm as Dbt
import socket
import time
import asyncio
import pymongo
from asyncua import Client
from datetime import datetime

# MongoDB connection URI (replace with your MongoDB URI)
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

def get_colour_name(r_mean, g_mean, b_mean):
    threshold = 50  # Define a threshold for how close red and green should be to each other
    # Check for blue
    if b_mean > g_mean and b_mean > r_mean:
        return "blue"
    # Check for yellow (red is dominant and close enough to green)
    elif r_mean > b_mean and r_mean > g_mean and abs(r_mean - g_mean) < threshold:
        return "yellow"
    # Check for green
    elif g_mean > r_mean and g_mean > b_mean:
        return "green"
    # If none of the above conditions are true, default to red
    else:
        return "red"

async def sortDice(app, mode):
    # Move to home location
    home_position = (255, 0, 50)
    ctrlBot = Dbt.DoBotArm(*home_position)  # Create DoBot Class Object with home position x, y, z
    ctrlBot.moveHome()

    async def handle_dice(dice_choice):
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
            color_name = get_colour_name(r, g, b)
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
                "measurement_timestamp": formatted_datetime,
                "component_color_hex": hex_value,
                "component_color_name": color_name,
                "current_temp_c": temperature,
                "current_humidity": humidity
            }
            result = await collection.insert_one(data_to_insert)
            print(f"Data saved to MongoDB with ID: {result.inserted_id}")
            
            ctrlBot.moveHome()

            if color_name in drop_areas:
                move_to_drop_area(ctrlBot, step_area, hover_areas[color_name], drop_areas[color_name])
        else:
            print("Unknown command")
            ctrlBot.moveHome()
            ctrlBot.dobotDisconnect()

    if mode == "manual":
        for dice_choice in ["1", "2", "3", "4"]:
            await handle_dice(dice_choice)
    elif mode == "automatic":
        for dice_choice in dice_positions.keys():
            await handle_dice(dice_choice)

    ctrlBot.dobotDisconnect()

class CustomTkinterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Custom Tkinter GUI")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Status area
        self.status_label = ctk.CTkLabel(root, text="Status: ", anchor="w")
        self.status_label.pack(side="top", fill="x", padx=10, pady=10)
        
        # Button frame for main buttons (Manual, Automatic, Reset, Exit)
        self.main_button_frame = ctk.CTkFrame(root)
        self.main_button_frame.pack(pady=10)
        
        self.manual_button = ctk.CTkButton(self.main_button_frame, text="Manual Mode", command=self.run_manual_mode)
        self.manual_button.pack(side="left", padx=5)
        
        self.automatic_button = ctk.CTkButton(self.main_button_frame, text="Automatic Mode", command=self.run_automatic_mode)
        self.automatic_button.pack(side="left", padx=5)
        
        self.reset_button = ctk.CTkButton(self.main_button_frame, text="Reset Position", command=lambda: self.update_status("Position Reset"))
        self.reset_button.pack(side="left", padx=5)
        
        self.exit_button = ctk.CTkButton(self.main_button_frame, text="Exit", command=root.quit)
        self.exit_button.pack(side="left", padx=5)
        
        # Button frame for additional buttons (Q13, Q15, Q17, Q19)
        self.additional_button_frame = ctk.CTkFrame(root)
        self.additional_button_frame.pack(pady=10)
        
        buttons = ["Q13", "Q15", "Q17", "Q19"]
        for btn_text in buttons:
            button = ctk.CTkButton(self.additional_button_frame, text=btn_text, command=lambda text=btn_text: self.update_status(f"Button {text} clicked"))
            button.pack(side="left", padx=5)

    def update_status(self, message):
        self.status_label.configure(text=f"Status: {message}")

    def run_manual_mode(self):
        self.update_status("Manual Mode selected")
        asyncio.create_task(sortDice(self, "manual"))

    def run_automatic_mode(self):
        self.update_status("Automatic Mode selected")
        asyncio.create_task(sortDice(self, "automatic"))

if __name__ == "__main__":
    root = ctk.CTk()
    app = CustomTkinterApp(root)
    root.mainloop()
