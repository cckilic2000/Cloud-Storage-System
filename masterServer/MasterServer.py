import socket
import threading
import json
from datetime import datetime
from uuid import uuid4
import bcrypt

serverPorts = [1230,1231,1232,1233,1234,1235,1236,1237,1238,1239]
numberOfServers = 0
servers = []
clientIndex = 0
saltForHashing = b'$2b$12$PMWv6mC/0oWGBefn0sBWju'

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
    global saltForHashing

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

        # Getting hashed password
        hashedPass = str(bcrypt.hashpw(str(password).encode('utf-8'), saltForHashing))

        # Read JSON file to check the provided user credentials
        jsonData = readJSON('userCredentials.json')
        users = jsonData['users']
        userID = "-1"

        # Check credentials
        for i in range(len(users)):
            if email == users[i][0] and hashedPass == users[i][1]:
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

        # Read the JSON file
        jsonData = readJSON('userCredentials.json')

        # Check if the user already exists
        doesExists = False
        for i in range(len(jsonData['users'])):
            if email == jsonData['users'][i][0]:
                doesExists = True
                break

        if not doesExists:
            # Hashing the password
            hashedPass = str(bcrypt.hashpw(str(password).encode('utf-8'), saltForHashing))

            # Generate new id for the user
            newID = datetime.now().strftime('%Y%m%d%H%M%S%f') + str(uuid4())
        
            # Create user
            newUser = [email , hashedPass , newID]
            jsonData['users'].append(newUser)

            # Write the updated data back to the JSON file
            writeJSON('userCredentials.json', jsonData)

            # Notify user
            conn.send(b'SIGNUP_COMPLETE')
        else:
            conn.send(b'SIGNUP_FAIL')

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

# Upload not sending response message from server to client
# When file is deleted subtract from size.json
# Upload directory functionality
# User creates directory structure
###############################
# Use locks???
    # MasterServer global variables
    # Server database files
###############################
# Can we use userID without showing it to the client for security reasons or use addr of client in server
# Test all cases/bug fix
# UI for client
# Where to store data??? Database directory seems primitive

# Passwords for users cihan, dilay, furkan: 1234
# Passwords for user test@gmail.com: 12345