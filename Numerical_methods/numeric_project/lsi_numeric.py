import pandas as pd
import numpy as np
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from collections import Counter
import nltk

# Download necessary NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

# Load the dataset
df = pd.read_csv('comcast_consumeraffairs_complaints_2.csv')

# Drop rows where the 'text' column is NaN
df = df.dropna(subset=['text'])

# Convert 'posted on' to datetime and handle errors
df['posted_on'] = pd.to_datetime(df['posted_on'],errors='coerce',format='mixed')

if df['posted_on'].isna().any():
    print("There are some dates that couldn't be parsed:", df[df['posted_on'].isna()])

# Filter out complaints from before 2009
df = df[df['posted_on'].dt.year >= 2009]

# Save the cleaned DataFrame to a new CSV file
df.to_csv('comcast_consumeraffairs_complaints_2.csv', index=False)

# Text preprocessing functions
def tokenize(text):
    return word_tokenize(text.lower())

def load_stopwords(file_path='stopwords.txt'):   
    with open(file_path, 'r', encoding='utf-8') as file:
        stopwords = file.read().splitlines()
    return set(stopwords)
custom_stopwords = load_stopwords()

def remove_stopwords(tokens):
    return [word for word in tokens if word not in custom_stopwords and word.isalpha()]

def stem_words(tokens):
    stemmer = PorterStemmer()
    return [stemmer.stem(word) for word in tokens]

def preprocess_text(text):
    tokens = tokenize(text)
    tokens = remove_stopwords(tokens)
    tokens = stem_words(tokens)
    return tokens

df['tokens'] = df['text'].apply(preprocess_text)

# Remove rows where the tokens column is an empty list
df = df[df['tokens'].map(len) > 0]

# Create a dictionary to store the index of each term
term_index = {}
for tokens in df['tokens']:
    for token in tokens:
        if token not in term_index:
            term_index[token] = len(term_index)

# Initialize the term-by-document matrix
td_matrix = np.zeros((len(term_index), len(df)))

# Populate the term-by-document matrix
for doc_id, tokens in enumerate(df['tokens']):
    term_count = Counter(tokens)
    for term, count in term_count.items():
        term_id = term_index[term]
        td_matrix[term_id, doc_id] = count

# Normalize the matrix column-wise
norms = np.linalg.norm(td_matrix, axis=0)
td_matrix_normalized = td_matrix / norms

# Compute SVD
U, sigma, VT = np.linalg.svd(td_matrix_normalized, full_matrices=False)

# Output the results to check
print("U matrix:\n", U[:5])  # Show only first 5 rows for brevity
print("Sigma values:\n", sigma[:5])  # Show only first 5 sigma values
print("V^T matrix:\n", VT[:5])  # Show only first 5 rows of V^T for brevity

# Q1: Error analysis
def reconstruct_matrix(U, Sigma, VT, k):
    U_k = U[:, :k]
    Sigma_k = np.diag(sigma[:k])
    VT_k = VT[:k, :]
    return U_k @ Sigma_k @ VT_k

ks = range(10, min(len(sigma), td_matrix.shape[1]) // 10, 20)
errors_mse = []
errors_fn = []

for k in ks:
    A_hat = reconstruct_matrix(U, sigma, VT, k)
    mse = np.mean((td_matrix_normalized - A_hat) ** 2)
    fn = np.linalg.norm(td_matrix_normalized - A_hat, 'fro')
    errors_mse.append((k, mse))
    errors_fn.append((k, fn))

min_mse_k = min(errors_mse, key=lambda x: x[1])
min_fn_k = min(errors_fn, key=lambda x: x[1])

print("Minimum MSE at k =", min_mse_k)
print("Minimum FN at k =", min_fn_k)

def create_query_vector(query, term_index):
    query_terms = preprocess_text(query)  # Preprocess the query
    query_vector = np.zeros(len(term_index))
    for term in query_terms:
        if term in term_index:
            query_vector[term_index[term]] = 1
    return query_vector

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def find_most_relevant_document(query, U, Sigma, VT, k, term_index):
    query_vector = create_query_vector(query, term_index)
    reduced_query = query_vector @ U[:, :k] @ np.linalg.inv(np.diag(Sigma[:k]))
    doc_scores = [cosine_similarity(reduced_query, VT[:k, i]) for i in range(VT.shape[1])]
    most_relevant_doc_index = np.argmax(doc_scores)
    return most_relevant_doc_index, df.iloc[most_relevant_doc_index]['text']

# Example use case
queries = [
    "ignorant overwhelming",
    "xfinity frustrate adapter verizon router",
    "terminate rent promotion joke liar internet horrible",
    "kindergarten ridiculous internet clerk terrible"
]

for query in queries:
    doc_index, doc_text = find_most_relevant_document(query, U, sigma, VT, 10, term_index)
    print(f"Most relevant document for query [{query}] is at index {1030}:")
    print(doc_text)
    print("\n")  # Adds a newline for better readability between entries

