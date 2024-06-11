import DoBotArm as Dbt
import socket
import time
import asyncio


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
    if b_mean > g_mean and b_mean > r_mean:
        return "blue"
    elif g_mean > r_mean and g_mean > b_mean:
        return "green"
    else:
        return "red"

async def sortDice():
    # Move to home location
    home_position = (255, 0, 50)
    ctrlBot = Dbt.DoBotArm(*home_position) #Create DoBot Class Object with home position x,y,z
    ctrlBot.moveHome()

    print("--- Manual Mode ---")
    print("s - start sort mode")
    print("q - exit manual mode")

    while True:
        inputCoords = input("$ ")
        if(inputCoords[0] == "s"):
            print("Starting...")

            # Q13 Dice Pos
            q13_pos = (255,-63,50)
            # Q15 Dice Pos
            q15_pos = (255,-20,50)
            # Q17 Dice Pos
            q17_pos = (255,16,50)
            # Q19 Dice Pos
            q19_pos = (255,59,50)


            # Pick up dice
            ctrlBot.moveArmXYZ(*q13_pos)
            ctrlBot.pickToggle(-43)
            #ctrlBot.toggleSuction()

            # Move to camera position
            camera_pos = (200,240,50)
            ctrlBot.moveArmXYZ(*camera_pos)

            # Receive hex value from camera
            host = '100.84.218.109'
            port = 8888
            hex_value = await tcp_client(host, port)

            # Convert hex to RGB and get color name
            r, g, b = hex_to_rgb(hex_value)
            color_name = get_colour_name(r, g, b)
            print(f"The dice color is: {color_name}")

            # Move to the color area and place the dice
            if(color_name == 'red'):
                area_red = (100, 90, -45)
                ctrlBot.moveArmXYZ(*area_red)
                time.sleep(5)
                ctrlBot.toggleSuction()

                # Move home
                ctrlBot.moveHome()

            elif(color_name == 'blue'):
                area_blue = (120, 90, -45)
                ctrlBot.moveArmXYZ(*area_blue)
                time.sleep(5)
                ctrlBot.toggleSuction()

                # Move home
                ctrlBot.moveHome()

            elif(color_name == 'green'):
                area_green = (140, 90, -45)
                ctrlBot.moveArmXYZ(*area_green)
                time.sleep(5)
                ctrlBot.toggleSuction()

                # Move home
                ctrlBot.moveHome()

        elif(inputCoords[0] == "q"):
            break
        else:
            print("Unknown command")


#--Main Program--
def main():
    asyncio.run(sortDice())

main()
