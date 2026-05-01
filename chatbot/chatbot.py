def chatbot_reply(question):

    q = question.lower()

    if "ipc 420" in q:
        return "IPC 420 deals with cheating and fraud."

    if "fraud punishment" in q:
        return "Punishment may include imprisonment up to 7 years."

    if "cyber crime" in q:
        return "Cyber crime involves illegal activities using computers or internet."

    return "I do not have enough legal information for that question."