import DoBotArm as Dbt
import socket
import time

HOST = "192.168.2.200" # The server's hostname or IP address
PORT = 65432


def get_colour_name(r_mean, g_mean, b_mean):
    currentColor = ""
    # Bestimmt die prominenteste Farbe und setzt die Variable
    if (b_mean > g_mean and b_mean > r_mean) :
        currentColor = "blue"
    elif (g_mean > r_mean and g_mean > b_mean) :
        currentColor = "green"
    else:
        currentColor = "red"
    return currentColor


def rgbSort():
    homeX, homeY, homeZ = 250, 0, 50
    ctrlBot = Dbt.DoBotArm(homeX, homeY, homeZ) #Create DoBot Class Object with home position x,y,z
    ctrlBot.moveHome()
    print("---Manual Mode---")
    print("s - start RGB-Sort")
    print("q - exit manual mode")
    while True:
        inputCoords = input("$ ")
        if(inputCoords[0] == "s"):
            print("Starting RGB-Sort...")
            #Pick up part
            ctrlBot.moveArmXYZ(240.0,2.3,-43.0)
            ctrlBot.toggleSuction()
            #move to camera
            ctrlBot.moveArmXYZ(266.0,0.0,0.0)
            ctrlBot.moveArmXYZ(117.0,276.0,-18.0)
            color_name = ""
            time.sleep(5)
            #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            #    s.connect((HOST, PORT))
            #    try:
            #        #data = "get color"
             #       s.sendall(bytes("get color", "ascii"))
             #       data = s.recv(1024)
              #      print([data[0], data[1], data[2]])
             #       color_name = get_colour_name(data[0], data[1], data[2])
             #       s.sendall(bytes("close", "ascii"))
             #       s.close()
             #   except:
             #       print("TCP-Socket error")
                    #move home
            #        ctrlBot.moveArmXYZ(250.0,0.0,50.0)
            #        ctrlBot.toggleSuction()
            #        break;
            
           # print(color_name)           
          #  if(color_name == "red"):
                #move to red box
            #    ctrlBot.moveArmXYZ(255.0,-196.0,27.0)
          #      ctrlBot.toggleSuction()
                #move home
           #     ctrlBot.moveArmXYZ(250.0,0.0,50.0)
         #   elif(color_name == "green"):
                #move to green box
            #    ctrlBot.moveArmXYZ(243.0,56.0,24.0)
          #      ctrlBot.moveArmXYZ(130.0,-223.0,30.0)
          #      ctrlBot.toggleSuction()
                #move home
            #    ctrlBot.moveArmXYZ(250.0,0.0,50.0)
           # elif(color_name == "blue"):
                #move to blue box
            #    ctrlBot.moveArmXYZ(243.0,56.0,24.0)
            #    ctrlBot.moveArmXYZ(7.0,-253.0,34.0)
            #    ctrlBot.toggleSuction()
                #move home
           #     ctrlBot.moveArmXYZ(250.0,0.0,50.0)
          #  else:
                #move home
          #      ctrlBot.moveArmXYZ(250.0,0.0,50.0)
        
            #move to blue box
            ctrlBot.moveArmXYZ(243.0,56.0,24.0)
            ctrlBot.moveArmXYZ(7.0,-253.0,34.0)
            ctrlBot.toggleSuction()
            #move home
            ctrlBot.moveArmXYZ(250.0,0.0,50.0)
            
        elif(inputCoords[0] == "q"):
            break
        else:
            print("Unknown command")


#--Main Program--
def main():
    rgbSort()

main()
