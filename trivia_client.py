import socket
import chatlib  # communication protocol

SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678
SIZE_RECV_BUFF = 1024
POINTS_PER_Q = 5

# HELPER SOCKET METHODS


def build_and_send_message(conn, code, data=""):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Paramaters: conn (socket object), code (str), data (str)
    Returns: Nothing
    """
    msg = chatlib.build_message(code, data)
    conn.send(msg.encode())


def recv_message_and_parse(conn):
    """
    Receives a new message from given socket,
    then parses the message using chatlib.
    Parameters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occurred, will return None, None
    """
    try:
        full_msg = conn.recv(SIZE_RECV_BUFF).decode()
        cmd, data = chatlib.parse_message(full_msg)
        return cmd, data
    except:
        return None, None


def connect(): # connects to server and returns socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    return sock


def error_and_exit(error_msg):
    print("ERROR: " + error_msg)
    exit()


def build_send_recv_parse(conn, code, data=""):
    build_and_send_message(conn, code, data)
    return recv_message_and_parse(conn)


def login(conn):
    while True:
        username = input("Please enter username: ")
        password = input("please enter password: ")
        outgoing_data = chatlib.join_data((username, password))
        outgoing_cmd = chatlib.PROTOCOL_CLIENT["login_msg"]
        build_and_send_message(conn, outgoing_cmd, outgoing_data)

        incoming_cmd, incoming_data = recv_message_and_parse(conn)
        if incoming_cmd == chatlib.PROTOCOL_SERVER["login_ok_msg"]:
            return
        print("Login failed: " + incoming_cmd)


def logout(conn):
    outgoing_cmd = chatlib.PROTOCOL_CLIENT["logout_msg"]
    build_and_send_message(conn, outgoing_cmd)

    return


def get_score(conn):
    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_player_score"])
    if cmd != chatlib.PROTOCOL_SERVER["player_score"]:
        error_and_exit("wrong server cmd")
    else:
        print("Your current score is " + data)
    return


def get_highscores(conn):
    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_highscores"])
    # if cmd != chatlib.PROTOCOL_SERVER["highscore_list"]:
    #     error_and_exit("wrong server cmd")
    # else:
    print("Highscores: \n" + data)
    return


def play_question(conn):
    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_question"])
    if cmd != chatlib.PROTOCOL_SERVER["question"]:
        error_and_exit("wrong server cmd")
    else:
        data = chatlib.split_data(data, 6)
        if data is None:
            print("splitting failed")
        print(data[0], data[1] + "?\n"
              "1." + data[2] + "\n"
              "2." + data[3] + "\n"
              "3." + data[4] + "\n"
              "4." + data[5] + "\n")

    question_num = data[0]
    answer = input()
    answer_cmd = chatlib.PROTOCOL_CLIENT["send_answer"]
    joined_answer = chatlib.join_data((question_num, answer))
    cmd, result_data = build_send_recv_parse(conn, answer_cmd, joined_answer)
    if cmd == chatlib.PROTOCOL_SERVER["correct_answer"]:
        print("Correct! You just earned " + str(POINTS_PER_Q) + " points!")
    elif cmd == chatlib.PROTOCOL_SERVER["wrong_answer"]:
        print("Sorry, you were wrong. The correct answer is: " + str(result_data) + ". " + data[int(result_data) + 1])
    else:
        error_and_exit("wrong server cmd")

    return


def get_logged_users(conn):
    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_logged_users"])
    if cmd != chatlib.PROTOCOL_SERVER["logged_users"]:
        error_and_exit("wrong server cmd")
    else:
        print("The following players are currently online: " + data)

    return


# command function dictionary
input_commands = {"1": play_question,
                  "2": get_score,
                  "3": get_highscores,
                  "4": get_logged_users,
                  "5": logout}


def main():
    sock = connect()
    login(sock)

    while True:
        action = input("What would you like to do? \n"
                       "1. Answer a question \n"
                       "2. Check your score \n"
                       "3. Get Highscore table \n"
                       "4. Find out who's online\n"
                       "5. Quit\n")
        input_commands[action](sock)
        if action == "5":
            break

    sock.close()


if __name__ == '__main__':
    main()
