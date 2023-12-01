import socket
import threading
import os
import json

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

    # Read storage size from size.json
    fileSize = os.path.getsize(path)
    dirSize = 0
    with open('../database/' + str(id) + '/size.json', 'r') as file:
        dataJson = json.load(file)
        dirSize = int(dataJson['size']) + fileSize

    # Check if the storage limit is exceeded
    if int(dirSize) <=  104857600: # 10 MB
        print(f"File {filename} received and stored.")

        # Update size.json
        sizeJson = {"size":str(dirSize)}
        jsonObj = json.dumps(sizeJson, indent=2)
        with open('../database/' + str(id) + '/size.json',"w") as file:
            file.write(jsonObj)
    else:
        path = '../database/' + str(id) + '/' + str(filename)
        os.remove(path)
        print(f"File {filename} not stored. Limit exceeded.")

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
        
        # Recieve filename
        filename = connection.recv(1024).decode('utf-8')
        print(f"Client requested a file upload to server...")
        print(f"Filename: {filename}...")

        # Check if the client has a directory or not
        path = '../database/' + str(clientID)
        if not os.path.exists(path):
            os.mkdir(path)
            # Create size file
            sizeJson = {"size":"0"}
            jsonObj = json.dumps(sizeJson, indent=2)
            with open(path + "/size.json","w") as file:
                file.write(jsonObj)

        # Check if there is already a file with the provided files name
        path = '../database/' + str(clientID) + '/' + str(filename)
        base , extension = os.path.splitext(filename)
        counter = 1
        while os.path.exists(path):
            filename = str(base) + str(counter) + str(extension)
            path = '../database/' + str(clientID) + '/' + str(filename)
            counter = counter + 1

        # Receive file
        receiveFile(connection, filename, clientID)

    elif requestArr[0] == 'DOWNLOAD':
        # Extract client ID
        clientID = requestArr[1]
        
        # Recieve filename and call send file func if file exist
        filename = connection.recv(1024).decode('utf-8')

        if filename != 'size.json':
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
        else:
            connection.send(b'ERROR')

    elif requestArr[0] == 'LIST':
        # Extract client ID
        clientID = requestArr[1]

        print(f"Client requested a file list from server...")

        # Construct the path
        path = '../database/' + str(clientID)
        if os.path.exists(path):
            if len(os.listdir(path)) == 0:
                connection.send(b'EMPTY')
                print(f"Requested file list is empty.")
            else:
                dirList = os.listdir(path)
                files = 'OK'
                for i in range(0, len(dirList), 1):
                    if str(dirList[i]) != 'size.json':
                        files = files + '/' + str(dirList[i])
                connection.send(str(files).encode('utf-8'))
                print(f"File  list is sent to client.")
        else:
            connection.send(b'EMPTY')
            print(f"Requested file list is empty.")

    elif requestArr[0] == 'DELETE':
        # Extract client ID
        clientID = requestArr[1]

        # Recieve filename and call delete file func if file exist
        filename = connection.recv(1024).decode('utf-8')
        print(f"Client requested a file delete from server...")
        print(f"Filename: {filename}...")
        path = '../database/' + str(clientID) + '/' + str(filename)

        if os.path.exists(path) and filename != 'size.json':
            # Reduce size.json by filesize
            delSize = os.path.getsize(path)

            dirSize = 0
            with open('../database/' + str(clientID) + '/size.json', 'r') as file:
                dataJson = json.load(file)
                dirSize = int(dataJson['size']) - delSize
            
            # Update size.json
            sizeJson = {"size":str(dirSize)}
            jsonObj = json.dumps(sizeJson, indent=2)
            with open('../database/' + str(clientID) + '/size.json',"w") as file:
                file.write(jsonObj)

            # Delete file if exists
            os.remove(path)
            print(f"File {filename} deleted from the server.")
            connection.send(b'OK')
        else:
            connection.send(b'ERROR')
            print(f"File {filename} not found on the server.")
    elif requestArr[0] == 'RENAME':
        # Extract client ID
        clientID = requestArr[1]

        # Receive filenames
        filenames = connection.recv(1024).decode('utf-8')
        filenamesArr = str(filenames).split('/')
        print(f"Client requested a file rename from server...")
        print(f"Filename: {filenamesArr[0]}, New Filename: {filenamesArr[1]}...")
        
        # Form paths
        baseOld , extension = os.path.splitext(filenamesArr[0])
        baseNew , extensionNew = os.path.splitext(filenamesArr[1])
        newFilename = str(baseNew) + str(extension)
        pathOld = '../database/' + str(clientID) + '/' + str(filenamesArr[0])
        pathNew = '../database/' + str(clientID) + '/' + str(newFilename)

        if os.path.exists(pathOld) and filenamesArr[0] != 'size.json' and newFilename != 'size.json' and not os.path.exists(pathNew):
            os.rename(pathOld,pathNew)
            connection.send(b'OK')
            print(f"Rename from {filenamesArr[0]} to {newFilename} is successfull.")
        else:
            connection.send(b'ERROR')
            print(f"Unable to rename file {filenamesArr[0]} to {filenamesArr[1]}.")

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