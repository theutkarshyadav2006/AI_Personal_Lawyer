import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download('punkt')
nltk.download('stopwords')

def clean_text(text):

    tokens = word_tokenize(text.lower())

    filtered = []

    for word in tokens:
        if word not in stopwords.words('english'):
            filtered.append(word)

    return " ".join(filtered)