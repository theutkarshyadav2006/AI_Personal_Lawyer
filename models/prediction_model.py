import pickle

model = pickle.load(open("models/model.pkl","rb"))
vectorizer = pickle.load(open("models/vectorizer.pkl","rb"))

def predict_case(text):

    vec = vectorizer.transform([text])

    prediction = model.predict(vec)

    return prediction[0]