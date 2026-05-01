from gensim.summarization import summarize

def summarize_case(text):
    summary = summarize(text, ratio=0.2)
    return summary