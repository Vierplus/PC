# import DoBotArm as Dbt
# import socket
# import time

# HOST = "192.168.2.200" # The server's hostname or IP address
# PORT = 65432


# def get_colour_name(r_mean, g_mean, b_mean):
#     currentColor = ""
#     # Bestimmt die prominenteste Farbe und setzt die Variable
#     if (b_mean > g_mean and b_mean > r_mean) :
#         currentColor = "blue"
#     elif (g_mean > r_mean and g_mean > b_mean) :
#         currentColor = "green"
#     else:
#         currentColor = "red"
#     return currentColor


# def rgbSort():
#     homeX, homeY, homeZ = 250, 0, 50
#     ctrlBot = Dbt.DoBotArm(homeX, homeY, homeZ) #Create DoBot Class Object with home position x,y,z
#     ctrlBot.moveHome()
#     print("---Manual Mode---")
#     print("s - start RGB-Sort")
#     print("q - exit manual mode")
#     while True:
#         inputCoords = input("$ ")
#         if(inputCoords[0] == "s"):
#             print("Starting RGB-Sort...")
#             #Pick up part
#             ctrlBot.moveArmXYZ(240.0,2.3,-43.0)
#             ctrlBot.toggleSuction()
#             #move to camera
#             ctrlBot.moveArmXYZ(266.0,0.0,0.0)
#             ctrlBot.moveArmXYZ(117.0,276.0,-18.0)
#             color_name = ""
#             time.sleep(5)
#             #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#             #    s.connect((HOST, PORT))
#             #    try:
#             #        #data = "get color"
#              #       s.sendall(bytes("get color", "ascii"))
#              #       data = s.recv(1024)
#               #      print([data[0], data[1], data[2]])
#              #       color_name = get_colour_name(data[0], data[1], data[2])
#              #       s.sendall(bytes("close", "ascii"))
#              #       s.close()
#              #   except:
#              #       print("TCP-Socket error")
#                     #move home
#             #        ctrlBot.moveArmXYZ(250.0,0.0,50.0)
#             #        ctrlBot.toggleSuction()
#             #        break;
            
#            # print(color_name)           
#           #  if(color_name == "red"):
#                 #move to red box
#             #    ctrlBot.moveArmXYZ(255.0,-196.0,27.0)
#           #      ctrlBot.toggleSuction()
#                 #move home
#            #     ctrlBot.moveArmXYZ(250.0,0.0,50.0)
#          #   elif(color_name == "green"):
#                 #move to green box
#             #    ctrlBot.moveArmXYZ(243.0,56.0,24.0)
#           #      ctrlBot.moveArmXYZ(130.0,-223.0,30.0)
#           #      ctrlBot.toggleSuction()
#                 #move home
#             #    ctrlBot.moveArmXYZ(250.0,0.0,50.0)
#            # elif(color_name == "blue"):
#                 #move to blue box
#             #    ctrlBot.moveArmXYZ(243.0,56.0,24.0)
#             #    ctrlBot.moveArmXYZ(7.0,-253.0,34.0)
#             #    ctrlBot.toggleSuction()
#                 #move home
#            #     ctrlBot.moveArmXYZ(250.0,0.0,50.0)
#           #  else:
#                 #move home
#           #      ctrlBot.moveArmXYZ(250.0,0.0,50.0)
        
#             #move to blue box
#             ctrlBot.moveArmXYZ(243.0,56.0,24.0)
#             ctrlBot.moveArmXYZ(7.0,-253.0,34.0)
#             ctrlBot.toggleSuction()
#             #move home
#             ctrlBot.moveArmXYZ(250.0,0.0,50.0)
            
#         elif(inputCoords[0] == "q"):
#             break
#         else:
#             print("Unknown command")


# #--Main Program--
# def main():
#     rgbSort()

# main()





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

            # Pick up dices
            ctrlBot.moveArmXYZ(*q13_pos)
            ctrlBot.pickToggle(-43)
            ctrlBot.toggleSuction()
            ctrlBot.pickToggle(30)

            # Move to camera position
            camera_pos = (200,240,50)
            ctrlBot.moveArmXYZ(*camera_pos)

            # Receive hex value from camera
            host = '100.84.218.109'
            port = 8888
            hex_value = await tcp_client(host, port)

            print(hex_value)
            # Convert hex to RGB and get color name
            r, g, b = hex_to_rgb(hex_value)
            color_name = get_colour_name(r, g, b)
            print(f"The dice color is: {color_name}")

            ctrlBot.moveHome()


            # Move to the color area and place the dice    
            if(color_name == 'red'):
                area_red = (-47, -243, -42)
                ctrlBot.moveArmXYZ(177, -182, 50)
                ctrlBot.moveArmXYZ(-47, -243, 50)
                ctrlBot.moveArmXYZ(*area_red)
                time.sleep(1)
                ctrlBot.toggleSuction()
                ctrlBot.moveArmXYZ(-47, -243, 50)
                ctrlBot.moveArmXYZ(177, -182, 50)

                # Move home
                ctrlBot.moveHome()

            elif(color_name == 'blue'):
                area_blue = (-6, -243, -42)
                ctrlBot.moveArmXYZ(177, -182, 50)
                ctrlBot.moveArmXYZ(-6, -243, 50)
                ctrlBot.moveArmXYZ(*area_blue)
                time.sleep(1)
                ctrlBot.toggleSuction()
                ctrlBot.moveArmXYZ(-6, -243, 50)
                ctrlBot.moveArmXYZ(177, -182, 50)

                # Move home
                ctrlBot.moveHome()

            elif(color_name == 'green'):
                area_green = (31, -243, -45)
                ctrlBot.moveArmXYZ(177, -182, 50)
                ctrlBot.moveArmXYZ(31, -243, 50)
                ctrlBot.moveArmXYZ(*area_green)
                time.sleep(1)
                ctrlBot.toggleSuction()
                ctrlBot.moveArmXYZ(31, -243, 50)
                ctrlBot.moveArmXYZ(177, -182, 50)

                # Move home
                ctrlBot.moveHome()

        elif(inputCoords[0] == "q"):
            ctrlBot.dobotDisconnect()
            break
        else:
            print("Unknown command")


#--Main Program--
def main():
    asyncio.run(sortDice())

main()
