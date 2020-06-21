import socket
import os
import sys
import tqdm
from fernet import Fernet

global keys

all_file = ''

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER_HOST = "192.168.100.5"
SERVER_PORT = 9999

BUFFER_SIZE = 4096
SEPARATOR = "|"

socket.connect((SERVER_HOST, SERVER_PORT))

print("Wait....")


def recv_msg():
    global keys
    # receive the file info
    # receive using client socket, not server socket
    received = socket.recv(BUFFER_SIZE).decode('ascii')
    # print(received)

    file_name, file_size = received.split(SEPARATOR)
    file_name = 'recv_' + file_name
    # print(file_name, file_size)
    # remove absolute path if there is
    file_name = os.path.basename(file_name)
    # convert to integer
    file_size = int(file_size)
    socket.send("...".encode('ascii'))

    # start receiving the file from the socket
    # and writing to the file stream
    progress = tqdm.tqdm(range(file_size), f"Receiving {file_name}", unit="B", unit_scale=True, unit_divisor=1024)

    try:
        with open(file_name, "wb") as f:
            for _ in progress:
                # read 1024 bytes from the socket (receive)
                bytes_read = socket.recv(BUFFER_SIZE)
                socket.send(".".encode('ascii'))
                if not bytes_read:
                    print("\nDone")
                    socket.close()
                    f.close()
                    decrypt(file_name, keys)
                    break
                # write to the file the bytes we just received
                f.write(bytes_read)
                # update the progress bar
                progress.update(len(bytes_read))
            f.close()

    except ConnectionAbortedError:
        sys.exit(1)


def decrypt(filename, key):
    print("Decrypting...")

    f = Fernet(key)
    with open(filename, "rb") as fr:
        # read the encrypted data
        encrypted_data = fr.read()
    # decrypt data
    decrypted_data = f.decrypt(encrypted_data)
    # write the original file
    with open(filename, "wb") as fl:
        fl.write(decrypted_data)

    print("Finished")
    sys.exit()


while True:
    global keys

    msg = str(socket.recv(1024).decode('ascii'))

    if msg == 'pswrd':
        password = input("Enter the password: ")
        socket.send(password.encode('ascii'))
        recved_msg = socket.recv(1024).decode('ascii')

        if recved_msg == 'True':
            # recv_msg()
            details = socket.recv(1024).decode('ascii')
            file_n, file_s = details.split(SEPARATOR)
            file_s = int(file_s)
            socket.send("...".encode('ascii'))

            with open("t_" + file_n, "wb") as fw:
                byte_read = socket.recv(file_s)
                if not byte_read:
                    break
                # write to the file the bytes we just received
                fw.write(byte_read)

            socket.send("Done".encode('ascii'))
            keys = open("t_key.key", "rb").read()

        else:
            print("Wrong password!!!")
            print("Connect again.")
            socket.close()
            break

    elif msg == "Sending...":
        recv_msg()
        break

    elif msg == "list":
        socket.send(str("Received").encode("ascii"))

    elif msg == "quit" or msg == 'over' or msg == 'rm':
        socket.close()
        break
