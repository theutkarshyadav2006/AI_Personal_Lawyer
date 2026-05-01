import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle

data = pd.read_csv("dataset/legal_cases.csv")

X = data["case_text"]
y = data["outcome"]

vectorizer = TfidfVectorizer()

X_vector = vectorizer.fit_transform(X)

model = LogisticRegression()

model.fit(X_vector,y)

pickle.dump(model,open("models/model.pkl","wb"))
pickle.dump(vectorizer,open("models/vectorizer.pkl","wb"))

print("Model trained successfully")