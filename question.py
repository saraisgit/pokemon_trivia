class Question:
    def __init__(self, id_num, q, a, b, c, d, correct):
        self.id = id_num
        self.q = q
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.correct = correct

    def get_question(self):
        return self.id, self.q, self.a, self.b, self.c, self.d
