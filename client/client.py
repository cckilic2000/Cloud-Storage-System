import socket
import os

portNum = -1
myID = -1

def uploadFile(connection, filename, id):
    # Send client choice to server
    msg = 'UPLOAD/' + str(id)
    connection.send(msg.encode('utf-8'))
    # Send filename to server
    connection.send(filename.encode('utf-8'))
    
    # Open file and send it in 1024 chunks
    with open(filename, 'rb') as file:
        data = file.read(1024)
        while data:
            connection.send(data)
            data = file.read(1024)

    print(f"File {filename} uploaded to the server.")

def downloadFile(connection, filename, id):
    # Send client choice to server
    msg = 'DOWNLOAD/' + str(id)
    connection.send(msg.encode('utf-8'))
    # Send filename to server
    connection.send(filename.encode('utf-8'))

    # Get the downloaded file if it exists
    response = connection.recv(1024)
    if response == b'OK':
        with open(filename, 'wb') as file:
            while True:
                data = connection.recv(1024)
                if not data:
                    break
                file.write(data)
        print(f"File {filename} downloaded and stored.")
    else:
        print(f"File {filename} not found on the server.")

def main():
    global portNum
    global myID
    isLoggedIn = False

    # Login or Sign up
    while not isLoggedIn:
        print("\n1. Login\n2. Sign up")
        s = input("Enter your choice: ")

        # Login screen
        if s == '1':
            # Getting user credentials
            email = input("Enter your email: ")
            password = input("Enter your password: ")

            # Connecting to master server to get assigned a port number
            print(f"Connecting to master server...")
            masterSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            masterSocket.connect(('localhost', 8888))

            while True:
                # Send identifier message
                msg = 'CLIENT_REGISTRATION/' + email + '/' + password
                masterSocket.send(msg.encode('utf-8'))
                # Receive request
                req = masterSocket.recv(1024).decode('utf-8')
                reqArr = str(req).split('/')

                # No active running servers
                if reqArr[0] == 'NO_SERVERS':
                    print(f"There are no servers running try again later.")
                    return
                # Wrong credentials are provided
                elif reqArr[0] == 'WRONG_CREDENTIALS':
                    print(f"Wrong credentials!")
                    break
                # Logged-in
                else:
                    # Extract port number and user id from master server message
                    portNum = int(reqArr[0])
                    myID = int(reqArr[1])
                    print(f"Assigned port is {portNum}.")
                    print(f"My id is {myID}")
                    isLoggedIn = True
                    break

            masterSocket.close()
        elif s == '2':
            # Getting user credentials
            email = input("Enter your email: ")
            password = input("Enter your password: ")

            # Connecting to master server to get assigned a port number
            print(f"Connecting to master server...")
            masterSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            masterSocket.connect(('localhost', 8888))
            
            # Send user credentials to be added to the database
            msg = 'SIGN_UP/' + email + '/' + password
            masterSocket.send(msg.encode('utf-8'))

            masterSocket.close()

    if not (portNum == -1):
        # Establish connection
        isReconnect = False
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect(('localhost', portNum))
        print(f"Connecting to server on port {portNum}...")

        while True:
            # Reconnects after a single transaction is done
            if isReconnect:
                print("client reconnect")
                clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                clientSocket.connect(('localhost', portNum))
                isReconnect = False

            print("\n1. Upload file\n2. Download file\n3. Quit")
            choice = input("Enter your choice: ")

            # Handle client choice
            if choice == '1':
                # Get filename and call upload func
                filename = input("Enter the name of the file to upload: ")
                uploadFile(clientSocket, filename, myID)

                # close connection to finish transaction then reconnect
                clientSocket.close()
                isReconnect = True
            elif choice == '2':
                # Get filename and call download func
                filename = input("Enter the name of the file to download: ")
                downloadFile(clientSocket, filename, myID)

                # close connection to finish transaction then reconnect
                clientSocket.close()
                isReconnect = True
            elif choice == '3':
                # Exit
                break
            else:
                print("Invalid choice. Please try again.")

        clientSocket.close()


if __name__ == "__main__":
    main()