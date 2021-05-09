# Protocol Constants

CMD_FIELD_LENGTH = 16  # Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4   # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10**LENGTH_FIELD_LENGTH-1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol
DATA_DELIMITER = "#"  # Delimiter in the data part of the message

# Protocol Messages 
# In this dictionary we will have all the client and server command names

PROTOCOL_CLIENT = {
	"login_msg": "LOGIN",
	"logout_msg": "LOGOUT",
	"get_logged_users": "LOGGED",
	"get_question": "GET_QUESTION",
	"send_answer": "SEND_ANSWER",
	"get_player_score": "MY_SCORE",
	"get_highscores": "HIGHSCORE"
}  # .. Add more commands if needed


PROTOCOL_SERVER = {
	"login_ok_msg": "LOGIN_OK",
	"login_failed_msg": "LOGIN_FAILED",
	"logged_users": "LOGGED_ANSWER",
	"question": "YOUR_QUESTION",
	"correct_answer": "CORRECT_ANSWER",
	"wrong_answer": "WRONG_ANSWER",
	"player_score": "YOUR_SCORE",
	"highscore_list": "ALL_SCORE",
	"error": "ERROR",
	"out_of_questions": "NO_QUESTION"
}  # ..  Add more commands if needed


def build_message(cmd, data):
	"""
	Gets command name (str) and data field (str) and creates a valid protocol message
	Returns: str, or None if error occurred
	"""
	try:
		if len(cmd) > CMD_FIELD_LENGTH:
			raise
		data_len = len(str(data))
		if data_len > MAX_DATA_LENGTH:
			raise
		full_msg = cmd.ljust(CMD_FIELD_LENGTH) + DELIMITER + str(data_len).rjust(LENGTH_FIELD_LENGTH, '0') + DELIMITER + str(data)
	except:
		full_msg = None
	finally:
		return full_msg


def parse_message(data):
	"""
	Parses protocol message and returns command name and data field
	Returns: cmd (str), data (str). If some error occurred, returns None, None
	"""
	try:
		parsed = data.split(DELIMITER)
		data_len = int(parsed[1])
		if data_len < 0 or data_len > MAX_DATA_LENGTH:
			raise
		cmd = parsed[0].strip()
		msg = parsed[2]
		if data_len is not len(msg):
			raise
	except:
		return None, None
	else:
		return cmd, msg

	
def split_data(msg, expected_fields):
	"""
	Helper method. gets a string and number of expected fields in it. Splits the string 
	using protocol's data field delimiter (|#) and validates that there are correct number of fields.
	Returns: list of fields if all ok. If some error occurred, returns None
	"""
	try:
		broken_down = msg.split(DATA_DELIMITER)
		if len(broken_down) is not expected_fields:
			return None
	except:
		return None
	else:
		return broken_down


def join_data(msg_fields):
	"""
	Helper method. Gets a list, joins all of it's fields to one string divided by the data delimiter. 
	Returns: string that looks like cell1#cell2#cell3
	"""
	joined = ""
	for field in msg_fields:
		joined += str(field)
		if field is not msg_fields[-1]:
			joined += DATA_DELIMITER
	return joined
