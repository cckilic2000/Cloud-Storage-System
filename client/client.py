import socket
import os

portNum = -1
myID = "-1"

def uploadFile(connection, filename, id):
    # Send client choice to server
    size = int(os.path.getsize(filename))
    msg = 'UPLOAD/' + str(id) + '/' + str(filename) + '/' + str(size)
    connection.send(msg.encode('utf-8'))

    response = connection.recv(1024).decode('utf-8')
    if response == 'OK':
        # Open file and send it in 1024 chunks
        with open(filename, 'rb') as file:
            data = file.read(1024)
            while data:
                connection.send(data)
                data = file.read(1024)
        print(f"File {filename} sent.")
    elif response == 'ERROR':
        print(f"Uploading file {filename} exceeds your storage limit.")

def downloadFile(connection, filename, id):
    # Send client choice to server
    msg = 'DOWNLOAD/' + str(id) + '/' + str(filename)
    connection.send(msg.encode('utf-8'))

    # Get the downloaded file if it exists
    response = connection.recv(1024).decode('utf-8')
    if response == 'OK':
        with open(filename, 'wb') as file:
            while True:
                data = connection.recv(1024)
                if not data:
                    break
                file.write(data)
        print(f"File {filename} downloaded and stored.")
    else:
        print(f"File {filename} not found on the server.")

def listFiles(connection, id):
    # Send client choice to server
    msg = 'LIST/' + str(id)
    connection.send(msg.encode('utf-8'))

    # Get the filename list
    response = connection.recv(1024).decode('utf-8')
    resArr = str(response).split('/')

    # For spacing
    print(f"\n")

    if resArr[0] == 'EMPTY':
        print(f"The storage is empty.")
    elif resArr[0] ==  'OK':
        for i in range(1, len(resArr), 1):
            print(f"{i}. {str(resArr[i])}")

    # For spacing
    print(f"\n")

def deleteFile(connection, filename, id):
    # Send client choice to server
    msg = 'DELETE/' + str(id) + '/' + str(filename)
    connection.send(msg.encode('utf-8'))
    
    # Get the response from the server
    response = connection.recv(1024).decode('utf-8')
    if response == 'OK':
        print(f"File deleted successfully.")
    elif response == 'ERROR':
        print(f"Specified file doesn't exist or couldn't be deleted.")

def renameFile(connection, filename, newFilename, id):
    # Send client choice to server
    msg = 'RENAME/' + str(id) + '/' + str(filename) + '/' + str(newFilename)
    connection.send(msg.encode('utf-8'))

    # Get the response from the server
    response = connection.recv(1024).decode('utf-8')
    if response == 'OK':
        print(f"Filename changed successfully.")
    elif response == 'ERROR':
        print(f"Unable to change filename to specified name.")

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
                    myID = str(reqArr[1])
                    print(f"Assigned port is {portNum}.")
                    print(f"My id is {myID}")
                    isLoggedIn = True
                    break

            masterSocket.close()
            # Sign up screen
        elif s == '2':
            # Getting user credentials
            email = input("Enter your email: ")
            password = input("Enter your password: ")
            rePassword = input("Enter your password again: ")

            if password == rePassword:
                # Connecting to master server to get assigned a port number
                print(f"Connecting to master server...")
                masterSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                masterSocket.connect(('localhost', 8888))
            
                # Send user credentials to be added to the database
                msg = 'SIGN_UP/' + email + '/' + password
                masterSocket.send(msg.encode('utf-8'))

                # Receive response from MasterServer
                req = masterSocket.recv(1024).decode('utf-8')

                if req == 'SIGNUP_COMPLETE':
                    print(f"Sign up successful.")
                elif req == 'SIGNUP_FAIL':
                    print(f"This email is already registered.")

                masterSocket.close()
            else:
                print(f"Passwords don't match please try again.")

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

            print("\n1. Upload file\n2. Download file\n3. List my files\n4. Delete file\n5. Rename a file\n6. Log out")
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
                listFiles(clientSocket, myID)

                # close connection to finish transaction then reconnect
                clientSocket.close()
                isReconnect = True
            elif choice == '4':
                # Get filename and call delete func
                filename = input("Enter the name of the file to delete: ")
                deleteFile(clientSocket, filename, myID)

                # close connection to finish transaction then reconnect
                clientSocket.close()
                isReconnect = True
            elif choice == '5':
                # Get the filename and new filename and call func
                filename = input("Enter the name of the file to rename: ")
                newFilename = input("Enter the new name of the file: ")
                renameFile(clientSocket, filename, newFilename, myID)

                # close connection to finish transaction then reconnect
                clientSocket.close()
                isReconnect = True
            elif choice == '6':
                # Exit
                break
            else:
                print("Invalid choice. Please try again.")

        clientSocket.close()


if __name__ == "__main__":
    main()