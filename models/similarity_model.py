from sklearn.metrics.pairwise import cosine_similarity

def find_similar_cases(input_vector, case_vectors):
    similarity = cosine_similarity(input_vector, case_vectors)
    return similarity