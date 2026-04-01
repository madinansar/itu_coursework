import numpy as np
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
import nltk

# Download necessary NLTK resources
nltk.download('punkt')
nltk.download('stopwords')


df = pd.read_csv('comcast_consumeraffairs_complaints.csv')  #read the file, create df(table)
df = df.dropna(subset=['text']) #delete null rows
df['posted_on'] = pd.to_datetime(df['posted_on'],errors='coerce',format='mixed')
df = df[df['posted_on'].dt.year >= 2009] #delete less than 2009
df.to_csv('comcast_consumeraffairs_complaints.csv', index=False) #update csv

#preprocessing text function
def preprocess_text(text):
    tokens = word_tokenize(text.lower())    #lowercasing
    tokens = [word for word in tokens if word.isalpha()]    #check alphabetic
    stop_words = set(stopwords.words('english'))    #create stopwords
    tokens = [word for word in tokens if word not in stop_words]    #remove stopwords
    stemmer = PorterStemmer()
    tokens = [stemmer.stem(word) for word in tokens]
    return tokens

df['tokens'] = df['text'].apply(preprocess_text)

#index of each term into matrix
term_index = {}
for tokens in df['tokens']:
    for token in tokens:
        if token not in term_index:
            term_index[token] = len(term_index)
            
# # no of unique terms
# print("number of unique terms:", len(term_index))

# create td matrix and fill
td_matrix = np.zeros((len(term_index), len(df)))
for doc_id, tokens in enumerate(df['tokens']):
    for term in tokens:
        term_id = term_index.get(term, -1)
        if term_id != -1:
            td_matrix[term_id, doc_id] += 1

#term frequency-inverse document frequency
def compute_tfidf(matrix):
    doc_frequency = np.sum(matrix > 0, axis=1)
    idf = np.log(matrix.shape[1] / (doc_frequency + 1))
    return matrix * idf[:, np.newaxis]

td_matrix_tfidf = compute_tfidf(td_matrix)


def power_method(matrix, num_iterations=100):
    b = np.random.rand(matrix.shape[1]) #random 1D vector
    for _ in range(num_iterations): #converges as iterates
        b = np.dot(matrix, b)   #A @ b
        b /= np.linalg.norm(b)  #normalize
    return b    #eigvector for 

def svd_power_method(matrix, num_singular_values):
    m, n = matrix.shape 
    U = np.zeros((m, num_singular_values))
    S = np.zeros(num_singular_values)
    Vt = np.zeros((num_singular_values, n))
    matrix_copy = matrix.copy()  #to preserve original matrix
    for i in range(num_singular_values):
        v = power_method(matrix_copy.T @ matrix_copy) #input to power method func is 
        sigma = np.linalg.norm(matrix_copy @ v)
        u = (matrix_copy @ v) / sigma   #Av/s
        matrix_copy -= np.outer(u, v) * sigma
        U[:, i] = u #shorten
        S[i] = sigma
        Vt[i, :] = v
    return U, S, Vt

def calculate_mse_and_fn(matrix, U, S, VT, k_values):
    mse_results = {}    
    fn_results = {}
    for k in k_values:
        U_k = U[:, :k]  #shorten
        S_k = S[:k]  #shorten
        VT_k = VT[:k, :]  #shorten
        A_hat = U_k @ np.diag(S_k) @ VT_k   #low-approx Ahat
        mse = np.mean((matrix - A_hat) ** 2)    #formula
        fn = np.linalg.norm(matrix - A_hat) #formula
        mse_results[k] = mse    #fill array
        fn_results[k] = fn  #fill array
    return mse_results, fn_results

def find_optimal_k(mse_results, fn_results):
    optimal_k_mse = min(mse_results, key=mse_results.get)   #minimal error
    optimal_k_fn = min(fn_results, key=fn_results.get)
    return optimal_k_mse, optimal_k_fn


U, S, VT = svd_power_method(td_matrix_tfidf, 100)
k_values = range(10, min(U.shape[0], VT.shape[1]) // 10 * 10 + 1, 20)

mse_results, fn_results = calculate_mse_and_fn(td_matrix_tfidf, U, S, VT, k_values)
optimal_k_mse, optimal_k_fn = find_optimal_k(mse_results, fn_results)

print("Minimum MSE at k = ({optimal_k_mse}, {mse_results[optimal_k_mse]}")
print("Minimum FN at k = ({optimal_k_fn}, {fn_results[optimal_k_fn]})")

def cosine_similarity(v1, v2):
    norm_v1 = np.linalg.norm(v1)    #normailze q
    norm_v2 = np.linalg.norm(v2)    #normailze v
    if norm_v1 == 0 or norm_v2 == 0:
        return 0  # Return 0 similarity if either vector has zero length to avoid division by zero
    return np.dot(v1, v2) / (norm_v1 * norm_v2) #formula

def query_vector(query, term_index, U, S, k):
    q = np.zeros(len(term_index))
    for word in query:
        if word in term_index:
            q[term_index[word]] = 1 #create a query vector so it has 1 where it has terms for term-index matrix
    return q @ U[:, :k] @ np.linalg.inv(np.diag(S[:k]))

def find_most_relevant_document(query, term_index, U, S, VT, k):
    q_vec = query_vector(query, term_index, U, S, k)
    VT_reduced = VT[:k, :]  # Here VT should have rows up to k
    document_similarities = [cosine_similarity(q_vec, VT_reduced[:, i]) for i in range(VT_reduced.shape[1])] #array with cosine values
    return np.argmax(document_similarities),df.iloc[np.argmax(document_similarities)]['text'] #the more cos -> the more similar

queries = {
    'query1': ['ignorant', 'overwhelming'],
    'query2': ['xfinity', 'frustrate', 'adapter', 'verizon', 'router'],
    'query3': ['terminate', 'rent', 'promotion', 'joke', 'liar', 'internet', 'horrible'],
    'query4': ['kindergarten', 'ridiculous', 'internet', 'clerk', 'terrible']
}

print("Using optimal k from MSE for query processing:")
for name, query in queries.items():
    most_relevant_doc_id = find_most_relevant_document(query, term_index, U, S, VT, optimal_k_mse)
    print(f"Most relevant document for {name}: Document ID {most_relevant_doc_id}")
