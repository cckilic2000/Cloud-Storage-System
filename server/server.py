import socket
import threading
import os

portNum = -1

# Server file receive function
def receiveFile(connection, filename, id):
    path = '../database/' + str(id) + '/' + str(filename)
    with open(path, 'wb') as file:
        while True:
            data = connection.recv(1024)
            if not data:
                break
            file.write(data)
        print(f"File {filename} received and stored.")

# Server file send function
def sendFile(connection, filename, id):
    path = '../database/' + str(id) + '/' + str(filename)
    with open(path, 'rb') as file:
        data = file.read(1024)
        while data:
            connection.send(data)
            data = file.read(1024)

def handleClient(connection, address):
    print(f"Connection from {address}...")

    # Read the first request which is the clients choice of either downlaod or upload
    request = connection.recv(1024).decode('utf-8')
    requestArr = str(request).split('/')
    if requestArr[0] == 'UPLOAD':
        # Extract client ID
        clientID = requestArr[1]
        # Recieve filename and call receive file func
        filename = connection.recv(1024).decode('utf-8')
        print(f"Client requested a file upload to server...")
        print(f"Filename: {filename}...")
        path = '../database/' + str(clientID)
        if not os.path.exists(path):
            os.mkdir(path)
        receiveFile(connection, filename, clientID)
        print(f"File {filename} uploaded to the server.")

    elif requestArr[0] == 'DOWNLOAD':
        # Extract client ID
        clientID = requestArr[1]
        # Recieve filename and call send file func if file exist
        filename = connection.recv(1024).decode('utf-8')
        print(f"Client requested a file download from server...")
        print(f"Filename: {filename}...")
        path = '../database/' + str(clientID) + '/' + str(filename)
        if os.path.exists(path):
            # Send file if exists
            connection.send(b'OK')
            sendFile(connection, filename, clientID)
            print(f"File {filename} sent to the client.")
        else:
            connection.send(b'ERROR')
            print(f"File {filename} not found on the server.")

    connection.close()

def main():
    global portNum
    # Connecting to master server to get assigned a port number
    print(f"Connecting to master server...")
    masterSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    masterSocket.connect(('localhost', 8888))

    while True:
        # Send identifier message
        masterSocket.send(b'SERVER_REGISTRATION')
        # Receive request
        req = masterSocket.recv(1024).decode('utf-8')

        if req == 'PORTS_FULL':
            print(f"All ports are occupied try again later.")
        else:
            portNum = int(req)
            print(f"Assigned port is {portNum}.")
            break

    masterSocket.close()

    if not (portNum == -1):
        # Start listening on the assigned port for clients
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind(('localhost', portNum))
        serverSocket.listen()

        print(f"Server listening on port {portNum}...")

        while True:
            # Start client thread when a client connects
            conn, addr = serverSocket.accept()
            clientThread = threading.Thread(target=handleClient, args=(conn, addr))
            clientThread.start()


if __name__ == "__main__":
    main()