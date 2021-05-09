##############################################################################
# server.py
##############################################################################

import socket
import select
import random
import chatlib
import user
import question

# GLOBALS
users = []
questions = []
logged_users = {}  # a dictionary of client sockets to usernames
messages_to_send = []  # tuples of socket (str) and message (str), to attempt sending at end of each loop

ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"
SIZE_RECV_BUFF = 1024
POINTS_PER_Q = 5


# Helper Socket methods

def build_and_send_message(conn, code, data):
	"""
	Builds a new message using chatlib, wanted code and message.
	Prints debug info, then sends it to the given socket.
	Parameters: conn (socket object), code (str), data (str)
	Returns: Nothing
	"""
	msg = chatlib.build_message(code, data)
	conn.send(msg.encode())
	
	print("[SERVER] ", msg)	  # Debug print


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
		print("[CLIENT] ", full_msg)  # Debug print
		return cmd, data
	except:
		print("[CLIENT] FAILED TO RECEIVE OR PARSE")  # Debug print
		return "", ""


# Data Loaders #

def load_questions():
	"""
	Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
	Receives: -
	Returns: questions dictionary
	"""
	global questions
	questions = [
		question.Question("1", "what type is Pikachu?", "Electric", "Fire", "Water", "Grass", "1"),
		question.Question("2", "what type is Squirtle?", "Electric", "Fire", "Water", "Grass", "3"),
		question.Question("3", "what type is Charmander?", "Electric", "Fire", "Water", "Grass", "2"),
		question.Question("4", "what type is Bulbasaur?", "Electric", "Fire", "Water", "Grass", "4")
		]
	
	return questions


def load_user_database():
	"""
	Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
	Receives: -
	Returns: user dictionary
	"""
	global users
	users = [
			user.User("test", "test", 0),
			user.User("yossi", "123", 50),
			user.User("master", "master", 200)
			]
	return users

	
# SOCKET CREATOR

def setup_socket():
	"""
	Creates new listening socket and returns it
	Receives: -
	Returns: the socket object
	"""
	server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_sock.bind((SERVER_IP, SERVER_PORT))
	print("server is up")
	server_sock.listen()
	print("listening for clients...")
	
	return server_sock


# MESSAGE HANDLING

def handle_question_message(conn, data):
	global questions

	msg = ""
	try:
		q = random.choice(questions)
		msg = q.get_question()
		msg = chatlib.join_data(msg)
		msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["question"], msg)
	except:
		msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["error"], "an error occurred while getting your question!!")
	finally:
		messages_to_send.append((conn, msg))


def handle_correct_answer(conn, player, q_id):
	player.score += POINTS_PER_Q
	player.add_asked_question(q_id)
	msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["correct_answer"], "")
	messages_to_send.append((conn, msg))


def handle_wrong_answer(conn, player, q):
	player.add_asked_question(q.id)
	msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["wrong_answer"], str(q.correct))
	messages_to_send.append((conn, msg))


def handle_answer_message(conn, data):
	try:
		username = logged_users[conn]
		player = next(player for player in users if player.username == username)
		q_id, answer = chatlib.split_data(data, 2)
		q = next(q for q in questions if q.id == q_id)
		if q.correct == answer:
			handle_correct_answer(conn, player, q_id)
		else:
			handle_wrong_answer(conn, player, q)
	except:
		msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["error"], "an error occurred when checking your answer!")
		messages_to_send.append((conn, msg))


def handle_getscore_message(conn, data):
	global users
	msg = ""
	try:
		username = logged_users[conn]
		player = next(player for player in users if player.username == username)
		score = player.score
		msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["player_score"], score)
	except:
		msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["error"], "an error occurred during score retrieval!")
	finally:
		messages_to_send.append((conn, msg))


def handle_highscore_message(conn, data):
	global users
	msg = ""
	try:
		sorted_by_score = sorted(users, key=lambda user_iter: user_iter.score, reverse=True)
		top_scores = sorted_by_score[:5]
		highscores_as_str = ""
		for player in top_scores:
			highscores_as_str += str(player.username)
			highscores_as_str += "\t"
			highscores_as_str += str(player.score)
			highscores_as_str += "\n"
		msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["highscore_list"], highscores_as_str)
	except:
		msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["error"], "an error occurred during high score retrieval!")
	finally:
		messages_to_send.append((conn, msg))


def handle_logged_message(conn, data):
	global logged_users

	msg = ""
	try:
		logged = []
		for player in logged_users:
			username = logged_users[player]
			logged.append(username)
		msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["logged_users"], logged)
	except:
		msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["error"], "an error occurred while preparing user list!")
	finally:
		messages_to_send.append((conn, msg))


def handle_logout_message(conn, data):
	"""
	Closes the given socket (in later chapters, also remove user from logged_users dictionary)
	Receives: socket
	Returns: None
	"""
	global logged_users
	try:
		conn.close()
		del logged_users[conn]
	except:
		pass


def handle_login_message(conn, data):
	"""
	Gets socket and message data of login message. Checks  user and pass exists and match.
	If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
	Receives: socket and data
	Returns: None (sends answer to client)
	"""
	global users
	global logged_users

	msg = ""
	try:
		(username, password) = chatlib.split_data(data, 2)
		player = next(player for player in users if player.username == username)
		if player is None:
			msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["login_failed_msg"], "invalid username")
		else:
			if password == player.password:
				msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["login_ok_msg"], "")
				logged_users[conn] = username
			else:
				msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["login_failed_msg"], "wrong password")
	except socket.error:
		print("HOW DID WE GET HERE?")
		msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["login_failed_msg"], "something went very wrong")
	finally:
		messages_to_send.append((conn, msg))


def handle_client_message(conn, cmd, data):
	"""
	Gets message code and data and calls the right function to handle command
	Recieves: socket, message code and data
	Returns: None
	"""
	global logged_users	 # To be used later
	
	cmd_handlers = {
		chatlib.PROTOCOL_CLIENT["login_msg"]: handle_login_message,
		chatlib.PROTOCOL_CLIENT["logout_msg"]: handle_logout_message,
		chatlib.PROTOCOL_CLIENT["get_logged_users"]: handle_logged_message,
		chatlib.PROTOCOL_CLIENT["get_question"]: handle_question_message,
		chatlib.PROTOCOL_CLIENT["send_answer"]: handle_answer_message,
		chatlib.PROTOCOL_CLIENT["get_player_score"]: handle_getscore_message,
		chatlib.PROTOCOL_CLIENT["get_highscores"]: handle_highscore_message
	}

	if conn in logged_users:
		if cmd == chatlib.PROTOCOL_CLIENT["login_msg"]:
			msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["error"], "you are already signed in!")
			messages_to_send.append((conn, msg))
			return
	elif cmd != chatlib.PROTOCOL_CLIENT["login_msg"]:
		msg = chatlib.build_message(chatlib.PROTOCOL_SERVER["error"], "you should sign in first!")
		messages_to_send.append((conn, msg))
		return

	cmd_handlers[cmd](conn, data)  # calls the appropriate handler


def main():
	# Initializes global users and questions dictionaries using load functions, will be used later
	global users
	global questions
	
	print("Welcome to Trivia Server!")
	
	server_sock = setup_socket()
	users = load_user_database()
	load_questions()
	client_sockets = []

	while True:
		ready_to_read, ready_to_write, in_error = select.select([server_sock] + client_sockets, client_sockets, [])
		for sock in ready_to_read:
			if sock is server_sock:
				(client_sock, client_addr) = sock.accept()
				print("new client joined!", client_addr)
				client_sockets.append(client_sock)
			else:
				try:
					cmd, data = recv_message_and_parse(sock)
					if cmd is None:
						client_sockets.remove(sock)
						sock.close()
					else:
						handle_client_message(sock, cmd, data)
				except socket.error:
					client_sockets.remove(sock)
					sock.close()

		for message in messages_to_send:
			current_sock, data = message
			if current_sock in ready_to_write:
				try:
					current_sock.send(data.encode())
					print("[SERVER]  ", data)
					messages_to_send.remove(message)
				except socket.error:
					pass


if __name__ == '__main__':
	main()

