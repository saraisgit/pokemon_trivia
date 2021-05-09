class User:
    def __init__(self, username, password, score):
        self.username = username
        self.password = password
        self.score = score
        self.questions_asked = []

    def add_points(self, points_to_add):
        self.score += points_to_add

    def add_asked_question(self, question_number):
        self.questions_asked.append(question_number)