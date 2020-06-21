import socket
import os
import tqdm
import threading
from fernet import Fernet
from queue import Queue

NO_OF_THREADS = 2
JOB_NUMBER = [1, 2]
queue = Queue()
all_connections = []
all_address = []

global SERVER_HOST
global SERVER_PORT
global server

SEPARATOR = "|"
BUFFER_SIZE = 1024 * 4  # 4KB


# Creating a Socket
def create_socket():
    try:
        global SERVER_HOST
        global SERVER_PORT
        global server
        server_name = socket.gethostname()
        SERVER_HOST = socket.gethostbyname(server_name)
        SERVER_PORT = 9999
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    except socket.error as msg:
        print('Error in creating a socket: ' + str(msg))


# Binding port
def bind_socket():
    try:
        global SERVER_HOST
        global SERVER_PORT
        global server

        print("Binding port: " + str(SERVER_PORT))
        server.bind((SERVER_HOST, SERVER_PORT))
        server.listen(5)
        print(f"Sheller> Listening as {SERVER_HOST}:{SERVER_PORT}")
        # print("Sheller> ", end='')

    except socket.error as msg:
        print("Socket Binding error: " + str(msg))
        bind_socket()


# Accepting a connection and saving it to the list
# 1st Thread
def accept_socket():
    for c in all_connections:
        c.close()

    del all_connections[:]
    del all_address[:]

    while True:
        try:
            conn, address = server.accept()
            server.setblocking(1)  # This prevents timeout from happening

            result = verify_socket(conn, address)

            if result:
                all_connections.append(conn)
                all_address.append(address)

                print(
                    "The Connections has been established successfully : " + str(address[0]) + " | " + str(address[1]))
                print("Sheller> ", end='')

            else:
                print("Connection cannot be established to: " + str(address[0]) + " | " + str(address[1]))
                print("Sheller> ", end='')

        except socket.error as msg:
            print("Sheller> Error accepting connections :( -> " + str(msg))


def verify_socket(conn, addr):
    msg = "pswrd"
    file_name = "key.key"
    file_size = os.path.getsize(file_name)

    conn.send(msg.encode('ascii'))
    recv_pass = conn.recv(1024).decode('ascii')

    if recv_pass == 'Password123' and trusted_client(addr):
        conn.send("True".encode('ascii'))
        conn.send(f"{file_name}{SEPARATOR}{file_size}".encode('ascii'))
        print(conn.recv(1024).decode('ascii'))

        with open(file_name, "rb") as f:
            bytes_read = f.read()

            if bytes_read:
                conn.sendall(bytes_read)
        f.close()

        print("File sent!!!")
        print(conn.recv(1024).decode('ascii'))

        return True

    else:
        conn.send("False".encode('ascii'))
        return False


def trusted_client(addr):
    try:
        open("log.txt").read()
    except FileNotFoundError:
        with open("log.txt", "w+") as f:
            f.write("Log File")
        f.close()

    with open("log.txt", "r+") as f:
        log = f.read()

        if addr[0] in log:
            print("Sheller> This is a trusted client")
            return True

        else:
            print(f"Sheller> A new connection with ip {addr[0]} is trying to connect!")

            choice = input("Sheller> Do you want to allow the connection?(y/n): ")

            if choice == 'y':
                # with open("log.txt") as fw:
                f.write(addr[0] + "\n")
                # fw.close()
                return True

            elif choice == 'n':
                print("The connection as been rejected!!!")
                return False

            else:
                print("Sheller> Enter a valid input!!!")
                return False


# Creating our own shell.
# This will also allow us to see the different clients/organization that are connected to us at the moment.
# 2nd Thread
# Sheller> list
# Connection ID     IP Address      Port Number
#       0           192.167.0.1        8080
#       1           255.255.255.255    ....

def start_shell():
    # cmd = ''
    while True:
        cmd = input("Sheller> ")

        if cmd == 'list':
            list_connection()

        elif 'rm' in cmd:
            try:
                to_be_removed = [int(i) for i in cmd[3:].split(" ")]

                for conn in to_be_removed:
                    all_connections[conn].send(str("rm").encode('ascii'))
                    all_connections[conn].close()
                    del all_connections[conn]
                    del all_address[conn]

                print("Sheller> Successfully removed the clients! \n")

            except ValueError:
                print("Sheller> Connection can't be terminated :(") 
                print("Sheller> Please type the command properly.")

        elif 'send' in cmd:

            count = 0
            file_name = cmd[5:]
            file_name_encrypt = "encrypt_" + file_name

            try:
                os.path.getsize(file_name)

            except FileNotFoundError:
                print("Invalid File Name.")
                start_shell()

            print("Encrypting and sending!!!")
            print("Please wait for few seconds.")

            encrypt(file_name, file_name_encrypt, key)
            file_size = os.path.getsize(file_name_encrypt)

            for i, conn in enumerate(all_connections):
                smsg = "Sending..."

                print(smsg)
                conn.send(smsg.encode('ascii'))

                conn.send(f"{file_name_encrypt}{SEPARATOR}{file_size}".encode('ascii'))
                print(conn.recv(1024).decode('ascii'))

                print("\nSheller> Sending data file to: " + str(all_address[i][0]) + " | " + str(all_address[i][1]))
                # start sending the file
                progress = tqdm.tqdm(range(file_size), f"Sending {file_name_encrypt}", unit="B", unit_scale=True,
                                     unit_divisor=1024)

                with open(file_name_encrypt, "rb") as f:
                    for _ in progress:
                        # read the bytes from the file
                        bytes_read = f.read(BUFFER_SIZE)
                        if not bytes_read:
                            conn.close()
                            del all_connections[i]
                            del all_address[i]
                            f.close()
                            print("Packets sent: " + str(count))
                            print("done")
                            start_shell()
                            # file transmitting is done
                            break
                        # we use sendall to assure transmission in
                        # busy networks
                        conn.sendall(bytes_read)
                        if conn.recv(1024).decode('ascii'):
                            count += 1

                        # update the progress bar
                        progress.update(len(bytes_read))

        elif cmd == 'quit' or cmd == 'over':
            for conn in all_connections:
                conn.send(str(cmd).encode('ascii'))
                conn.close()

        else:
            print("Command not recognized :'( ")


def list_connection():
    print("                ----- Clients -----                  ")
    print("Connection ID      IP Address          Port Number \n")
    # results = ""
    for i, conn in enumerate(all_connections):
        try:
            conn.send("list".encode('ascii'))  #
            conn.recv(201480)

        except socket.error:
            del all_connections[i]
            del all_address[i]
            print("Offline")
            continue

        results = "      " + str(i) + "           " + str(all_address[i][0]) + "           " + str(
            all_address[i][1]) + "    \n"

        print(results)


# Given a filename (str) and key (bytes), it encrypts the file and write it into the file
def encrypt(filename, filename_encrpt, keys):
    f = Fernet(keys)
    with open(filename, "rb") as file:
        # read all file data
        file_data = file.read()
    # encrypt data
    encrypted_data = f.encrypt(file_data)
    # write the encrypted file
    with open(filename_encrpt, "wb") as file:
        file.write(encrypted_data)


def create_workers():
    for i in range(NO_OF_THREADS):
        t = threading.Thread(target=work)
        t.daemon = True
        t.start()


def work():
    while True:
        x = queue.get()
        if x == 1:
            create_socket()
            bind_socket()
            accept_socket()
        if x == 2:
            if all_connections is not None:
                start_shell()

        queue.task_done()


def create_jobs():
    for x in JOB_NUMBER:
        queue.put(x)

    queue.join()


if __name__ == "__main__":
    gen_key = Fernet.generate_key()
    with open("key.key", "wb") as key_file:
        key_file.write(gen_key)

    key = open("key.key", "rb").read()

    create_workers()
    create_jobs()
