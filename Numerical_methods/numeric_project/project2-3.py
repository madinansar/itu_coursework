import numpy as np
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

''' 
github_url = 'https://gist.github.com/sebleier/554280' #get stopwords
get_words = requests.get(github_url)
if get_words.status_code == 200: #HTTP code check for success
    stopwords = set(get_words.text.split())
else:
    stopwords = set()
'''

def data_preprocess(text):
    stopword = set(stopwords.words('english'))
    stemming = PorterStemmer()
    lemmatizing = WordNetLemmatizer()
    processed_data = word_tokenize(text.lower()) #tokenize the text in csv
    processed_data = [term for term in processed_data if term not in stopword] #remove stopwords given in github list
    processed_data = [stemming.stem(term) for term in processed_data] 
    processed_data = [lemmatizing.lemmatize(term) for term in processed_data]
    return processed_data

def svd(A, singval_num, iter_num=100):
    t, d = A.shape
    A_copy = A.copy()
    
    #initialization of U, Σ, and VT 
    U = np.zeros((t, singval_num)) #txt size
    singular = np.zeros(singval_num) #txd size
    VT = np.zeros((singval_num, d)) #dxd size
    
    ATA = np.dot(A_copy.T, A_copy) #Dot product of A^T and A
    
    for i in range(singval_num):
        x = np.random.rand(ATA.shape[1]) #randomly selected vector x0 with size t*1
        for iteration in range(iter_num):
            x = np.dot(ATA, x)
            x_norm = np.linalg.norm(x)
            x /= x_norm #obtain x1 for the next iteration
        v = x
        s = np.linalg.norm(np.dot(A_copy, v))
        u = np.dot(A_copy, v) / s
        A_copy -= s * np.outer(u, v)
        U[:, i] = u
        singular[i] = s
        VT[i, :] = v
        
    return U, singular, VT

def mse_calc(A, A_appr):
    return np.mean((A - A_appr)** 2)

def frb_calc(A, A_appr):
    return np.linalg.norm(A - A_appr)

def q_vector(query, U, S, k, index):
    q = np.zeros(len(index))
    for term in query:  
        if term in index: #if term exists in original terms puts 1, else 0
            q[index[term]] = 1
        else:
            q[index[term]] = 0     
    S_inverse = np.linalg.inv(np.diag(S[:k])) #inverse of singular value matrix
            
    return np.dot(q , np.dot(U[:, :k], S_inverse)) #formula of query vector 
    
def cos_sim(q, d): 
    q_norm = np.linalg.norm(q)
    d_norm = np.linalg.norm(d)
    if q_norm != 0 or d_norm != 0: #division by zero is not possible
        sim = np.dot(q, d) / (q_norm * d_norm) #calculate cosine similarity
        return sim
    else:
        return 0 
    
############################################################

read_data = pd.read_csv("comcast_consumeraffairs_complaints.csv") #read dataset

read_data.dropna(subset=['text']) #remove rows with missing values

read_data['processed_data'] = read_data['text'].apply(data_preprocess)

index = {}
for processed_data in read_data['processed_data']: #create dictionary for terms
    for i in processed_data:
        if i not in index:
            index[i] = len(index)

term_by_doc_matrix = np.zeros((len(index), len(read_data))) #create term by document matrix
for document, read_data in enumerate(read_data['processed_data']):
    for i in read_data:
        term = index.get(i, -1)
        if term != -1:
            term_by_doc_matrix[term, document] += 1

doc_frequency = np.sum(term_by_doc_matrix > 0, axis=1)
idf = np.log(term_by_doc_matrix.shape[1] / (doc_frequency + 1))
tfidf = term_by_doc_matrix * idf[:, np.newaxis]

U, S, VT = svd(tfidf, 100)
k_val = range(10, min(U.shape[0], VT.shape[1])// 10 * 10 + 1, 20) #k value range as defined in pdf

mse_val = []
frb_val = []

for k in k_val:
    Uk = U[:, :k]
    Sk = S[:k]
    diagonalize = np.diag(Sk)
    Vtk = VT[:k, :]
    A_appr = np.dot(Uk, np.dot(diagonalize, Vtk))
    mse_val.append(mse_calc(tfidf, A_appr))
    frb_val.append(frb_calc(tfidf, A_appr))
     
k_mse = np.argmin(mse_val)
k_frb = np.argmin(frb_val)

print("Optimal k for least MSE = ", mse_val[k_mse], ": ", k_mse)
print("Optimal k for least FN = ", frb_val[k_frb], ": ", k_frb)

queries = {
    '1': ['ignorant', 'overwhelming'],
    '2': ['xfinity', 'frustrate', 'adapter', 'verizon', 'router'],
    '3': ['terminate', 'rent', 'promotion', 'joke', 'liar', 'internet', 'horrible'],
    '4': ['kindergarten', 'ridiculous', 'internet', 'clerk', 'terrible']
}

for number, query in queries.items():
    q = q_vector(query, U, S, k, index)
    Vt = VT[:k, :]
    similarity = []
    for i in range(Vt.shape[1]):
        cosine_sim = cos_sim(q, Vt[:, i])
        similarity.append(cosine_sim)
        
    most_rel_doc = np.argmax(similarity)
    print("Most relevant document for query", number, ": ", most_rel_doc)

