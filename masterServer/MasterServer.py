import socket
import threading
import json
from datetime import datetime
from uuid import uuid4

serverPorts = [1230,1231,1232,1233,1234,1235,1236,1237,1238,1239]
numberOfServers = 0
servers = []
clientIndex = 0

# Json file reader for user credentials
def readJSON(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

# Writing on a json file for user sign up
def writeJSON(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def handleConn(conn, addr):
    global serverPorts
    global numberOfServers
    global servers
    global clientIndex

    print(f"Connection received from address: {addr}...")
    # Receive identifier message
    req = conn.recv(1024).decode('utf-8')
    reqArr = str(req).split('/')

    # Handle request
    if reqArr[0] == 'SERVER_REGISTRATION':
        print(f"{addr} is requesting server registration...")
        
        # Check if there exist free ports
        if numberOfServers == 10:
            print(f"All ports are occupied at the moment.")
            # Send all ports are occupied message
            conn.send(b'PORTS_FULL')
        elif numberOfServers < 10:
            # Send the port number to the server
            portNum = serverPorts[numberOfServers]
            print(f"Port number {portNum} is registered to server {addr}.")
            numberOfServers = numberOfServers + 1
            servers.append(portNum)
            msg = str(portNum)
            conn.send(msg.encode('utf-8'))
    elif reqArr[0] == 'CLIENT_REGISTRATION':
        print(f"{addr} is requesting client registration...")

        # Login credentials
        email = reqArr[1]
        password = reqArr[2]

        # Read JSON file to check the provided user credentials
        jsonData = readJSON('userCredentials.json')
        users = jsonData['users']
        userID = "-1"

        # Check credentials
        for i in range(len(users)):
            if email == users[i][0] and password == users[i][1]:
                userID = users[i][2]
                break
        
        # If user not found
        if userID == "-1":
            print(f"{addr} provided wrong credentials")
            conn.send(b'WRONG_CREDENTIALS')
        # Check if there are any servers registered
        elif len(servers) == 0:
            print(f"No servers are registered at the moment.")
            # Send no servers to connect message
            conn.send(b'NO_SERVERS')
        elif len(servers) > 0:
            # Send the port number to the client
            portNum = servers[clientIndex]
            print(f"Port number {portNum} is registered to client {addr}.")
            clientIndex = clientIndex + 1
            if clientIndex == len(servers):
                clientIndex = 0

            # Send port and userId informarion to the client
            msg = str(portNum) + '/' + str(userID)
            conn.send(msg.encode('utf-8'))
    elif reqArr[0] == 'SIGN_UP':
        print(f"{addr} is requesting sign up...")

        # Provided user credentials for the sign up
        email = reqArr[1]
        password = reqArr[2]

        # Add new user to the database json file
        jsonData = readJSON('userCredentials.json')
        newID = datetime.now().strftime('%Y%m%d%H%M%S%f') + str(uuid4())
        newUser = [email , password , newID]
        jsonData['users'].append(newUser)

        # Write the updated data back to the JSON file
        writeJSON('userCredentials.json', jsonData)

    conn.close()

def main():
    # Open connection on masterServer port
    masterSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    masterSocket.bind(('localhost', 8888))
    masterSocket.listen()

    print("Master Server started listening port 8888")

    while True:
        # Start the connection handling thread when a connection is established
        conn, addr = masterSocket.accept()
        connThread = threading.Thread(target=handleConn, args=(conn, addr))
        connThread.start()


if __name__ == "__main__":
    main()

# Before signup check if the user already exists and notify client if it does
# Handle if file doesnt exist in all cases
# Same user logging in twice
# Add logout functionality
# Take password twice while signing up
# Check type for email??? Is it really an email or not
# Make server port list infinite all servers should be registered
# Hash passwords???
# Can we use userID without showing it to the client for security reasons
# Delete file functionality
###############################
# Use locks???
    # MasterServer global variables
    # Server database files
###############################
# Test all cases/bug fix
# UI for client
# Total storage limits for clients???
# Where to store data??? Database directory seems primitive
# Put user credentials in a database??? If we put them in a database we may not need to hash passwords