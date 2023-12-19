from flask import Flask, render_template, request, redirect, url_for
from flask import flash
import os
import socket

app = Flask(__name__)
app.secret_key = 'your_secret_key'

portNum = -1
myID = -1

@app.route('/dashboard')
def dashboard():
    global myID
    filesList = []
    if myID == -1:
        flash('You need to login first!')
        return redirect(url_for('login'))
    else:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect(('localhost', portNum))

        # Send client choice to server
        msg = 'LIST/' + str(myID)
        clientSocket.send(msg.encode('utf-8'))

        # Get the filename list
        response = clientSocket.recv(1024).decode('utf-8')
        resArr = str(response).split('/')

        if resArr[0] == 'EMPTY':
            print(f"The storage is empty.")
        elif resArr[0] ==  'OK':
            for i in range(1, len(resArr), 1):
                print(f"{i}. {str(resArr[i])}")
                filesList.append(str(resArr[i]))

        clientSocket.close()
    return render_template('dashboard.html',files=filesList)

@app.route('/')
def index():
    if myID != -1:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))
    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']

        if password == password2:
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
                flash("Sign up successful.")
            elif req == 'SIGNUP_FAIL':
                print(f"This email is already registered.")
                flash("This email is already registered.")

            masterSocket.close()
            return render_template('login.html')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global myID
    global portNum
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

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
                masterSocket.close()
                return redirect(url_for('dashboard'))

        masterSocket.close()

    return render_template('login.html')

@app.route('/upload', methods=['POST'])
def upload():
    global myID
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if myID != -1:
        fileName = file.filename
        file.save('myUploads/' + str(fileName))
        
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect(('localhost', portNum))

        size = int(os.path.getsize('myUploads/' + str(fileName)))
        msg = 'UPLOAD/' + str(myID) + '/' + str(fileName) + '/' + str(size)
        clientSocket.send(msg.encode('utf-8'))
        
        response = clientSocket.recv(1024).decode('utf-8')
        if response == 'OK':
            # Open file and send it in 1024 chunks
            with open('myUploads/' + str(fileName), 'rb') as file:
                data = file.read(1024)
                while data:
                    clientSocket.send(data)
                    data = file.read(1024)
            print(f"File {fileName} sent.")
        elif response == 'ERROR':
            print(f"Uploading file {fileName} exceeds your storage limit.")

        clientSocket.close()
        
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/download/<filename>')
def download(filename):
    global myID
    global portNum
    if myID != -1:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect(('localhost', portNum))

        fileToDownload = str(filename)
        
        # Send client choice to server
        msg = 'DOWNLOAD/' + str(myID) + '/' + str(fileToDownload)
        clientSocket.send(msg.encode('utf-8'))

        # Get the downloaded file if it exists
        response = clientSocket.recv(1024).decode('utf-8')
        print(response)
        if response == 'OK':
            with open(fileToDownload, 'wb') as file:
                while True:
                    data = clientSocket.recv(1024)
                    if not data:
                        break
                    file.write(data)
            print(f"File {fileToDownload} downloaded and stored.")
        else:
            print(f"File {fileToDownload} not found on the server.")

        clientSocket.close()
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    global myID
    global portNum

    fileToDelete = str(filename)
    if myID != -1:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect(('localhost', portNum))

        # Send client choice to server
        msg = 'DELETE/' + str(myID) + '/' + str(fileToDelete)
        clientSocket.send(msg.encode('utf-8'))

        # Get the response from the server
        response = clientSocket.recv(1024).decode('utf-8')
        if response == 'OK':
            print(f"File deleted successfully.")
        elif response == 'ERROR':
            print(f"Specified file doesn't exist or couldn't be deleted.")

        clientSocket.close()
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/rename/<filename>', methods=['POST'])
def rename(filename):
    global myID
    global portNum
    if myID != -1:
        originalFilename = str(filename)
        newFilename = str(request.form['new_name'])

        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect(('localhost', portNum))

        # Send client choice to server
        msg = 'RENAME/' + str(myID) + '/' + str(originalFilename) + '/' + str(newFilename)
        clientSocket.send(msg.encode('utf-8'))

        # Get the response from the server
        response = clientSocket.recv(1024).decode('utf-8')
        if response == 'OK':
            print(f"Filename changed successfully.")
        elif response == 'ERROR':
            print(f"Unable to change filename to specified name.")

        clientSocket.close()
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    global myID
    global portNum
    myID = -1
    portNum = -1
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)