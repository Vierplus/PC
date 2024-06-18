import DoBotArm as Dbt
import socket
import time
import asyncio

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
    if b_mean > g_mean and b_mean > r_mean:
        return "blue"
    elif g_mean > r_mean and g_mean > b_mean:
        return "green"
    elif r_mean > b_mean and g_mean > b_mean:
        if abs(r_mean - g_mean) < threshold:
            return "yellow"
    else:
        return "red"

async def sortDice():
    # Move to home location
    home_position = (255, 0, 50)
    ctrlBot = Dbt.DoBotArm(*home_position)  # Create DoBot Class Object with home position x, y, z
    ctrlBot.moveHome()

    print("--- Manual Mode ---")
    print("s - start sort mode")
    print("q - exit manual mode")

    while True:
        inputCoords = input("$ ")
        if inputCoords[0] == "s":
            print("Starting...")

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

            # Hover area coordinates (same x, y as drop area, z = 50)
            hover_areas = {color: (x, y) for color, (x, y, z) in drop_areas.items()}

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

                    # Move to camera position
                    camera_pos = (200, 240, 50)
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

                    ctrlBot.moveHome()

                    if color_name in drop_areas:
                        move_to_drop_area(ctrlBot, step_area, hover_areas[color_name], drop_areas[color_name])

                elif dice_choice == "q":
                    ctrlBot.dobotDisconnect()
                    break
                else:
                    print("Unknown command")

        elif inputCoords[0] == "q":
            ctrlBot.dobotDisconnect()
            break
        else:
            print("Unknown command")


#--Main Program--
def main():
    asyncio.run(sortDice())

main()
