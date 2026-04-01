# import numpy as np
# import pandas as pd
# from nltk.tokenize import word_tokenize
# from nltk.stem import PorterStemmer
# from nltk.corpus import stopwords
# import nltk

# # Download necessary NLTK resources
# nltk.download('punkt')
# nltk.download('stopwords')


# df = pd.read_csv('comcast_consumeraffairs_complaints.csv')  #read the file, create df(table)
# df = df.dropna(subset=['text']) #delete null rows


# #preprocessing text function
# def preprocess_text(text):
#     tokens = word_tokenize(text.lower())    #lowercasing
#     tokens = [word for word in tokens if word.isalpha()]    #check alphabetic
#     stop_words = set(stopwords.words('english'))    #create stopwords
#     tokens = [word for word in tokens if word not in stop_words]    #remove stopwords
#     stemmer = PorterStemmer()
#     tokens = [stemmer.stem(word) for word in tokens]
#     return tokens

# df['tokens'] = df['text'].apply(preprocess_text)

# #index of each term into matrix
# term_index = {}
# for tokens in df['tokens']:
#     for token in tokens:
#         if token not in term_index:
#             term_index[token] = len(term_index)
            
# # # no of unique terms
# # print("number of unique terms:", len(term_index))

# # create td matrix and fill
# td_matrix = np.zeros((len(term_index), len(df)))
# for doc_id, tokens in enumerate(df['tokens']):
#     for term in tokens:
#         term_id = term_index.get(term, -1)
#         if term_id != -1:
#             td_matrix[term_id, doc_id] += 1

# # Compute term frequency-inverse document frequency (TF-IDF)
# def compute_tfidf(matrix):
#     doc_frequency = np.sum(matrix > 0, axis=1)
#     idf = np.log(matrix.shape[1] / (doc_frequency + 1))
#     return matrix * idf[:, np.newaxis]

# td_matrix_tfidf = compute_tfidf(td_matrix)

# # Power method for eigenvalue and eigenvector
# def power_method(matrix, num_iterations=100):
#     b = np.random.rand(matrix.shape[1])
#     for _ in range(num_iterations):
#         b = np.dot(matrix, b)
#         b /= np.linalg.norm(b)
#     return b

# # SVD implementation using power method
# def svd_power_method(matrix, num_singular_values=100):
#     m, n = matrix.shape
#     U = np.zeros((m, num_singular_values))
#     S = np.zeros(num_singular_values)
#     Vt = np.zeros((num_singular_values, n))
#     matrix_copy = matrix.copy()  # Work on a copy to preserve original matrix
#     for i in range(num_singular_values):
#         v = power_method(matrix_copy.T @ matrix_copy)
#         sigma = np.linalg.norm(matrix_copy @ v)
#         u = (matrix_copy @ v) / sigma
#         matrix_copy -= np.outer(u, v) * sigma
#         U[:, i] = u
#         S[i] = sigma
#         Vt[i, :] = v
#     return U, S, Vt

# def calculate_mse_and_fn(matrix, U, S, VT, k_values):
#     mse_results = {}
#     fn_results = {}
#     for k in k_values:
#         U_k = U[:, :k]
#         S_k = S[:k]
#         VT_k = VT[:k, :]
#         A_hat = U_k @ np.diag(S_k) @ VT_k
#         mse = np.mean((matrix - A_hat) ** 2)
#         fn = np.linalg.norm(matrix - A_hat)
#         mse_results[k] = mse
#         fn_results[k] = fn
#     return mse_results, fn_results

# def find_optimal_k(mse_results, fn_results):
#     optimal_k_mse = min(mse_results, key=mse_results.get)
#     optimal_k_fn = min(fn_results, key=fn_results.get)
#     return optimal_k_mse, optimal_k_fn


# U, S, VT = svd_power_method(td_matrix_tfidf, 100)
# k_values = range(10, min(U.shape[0], VT.shape[1]) // 10 * 10 + 1, 20)

# # Calculate MSE and FN for different k values
# mse_results, fn_results = calculate_mse_and_fn(td_matrix_tfidf, U, S, VT, k_values)

# # Determine the optimal k based on MSE and FN
# optimal_k_mse, optimal_k_fn = find_optimal_k(mse_results, fn_results)

# print(f"Optimal k according to MSE is {optimal_k_mse} with MSE: {mse_results[optimal_k_mse]}")
# print(f"Optimal k according to FN is {optimal_k_fn} with FN: {fn_results[optimal_k_fn]}")

# # Q1: Error analysis
# # U, S, VT = svd_power_method(td_matrix_tfidf, 100)

# # def reconstruct_matrix(U, S, VT, k):
# #     U_k = U[:, :k]
# #     S_k = np.diag(S[:k])
# #     VT_k = VT[:k, :]
    
# #     return U_k @ S_k @ VT_k

# # matrix = reconstruct_matrix()

# # ks = range(10, min(len(S), td_matrix.shape[1]) // 10, 20)
# # errors_mse = []
# # errors_fn = []
# # reconstruct_matrix(U, S, VT, k)
# # for k in ks:
# #     A_hat = reconstruct_matrix(U, S, VT, k)
# #     mse = np.mean((matrix - A_hat) ** 2)
# #     fn = np.linalg.norm(matrix - A_hat, 'fro')
# #     errors_mse.append((k, mse))
# #     errors_fn.append((k, fn))

# # min_mse_k = min(errors_mse, key=lambda x: x[1])
# # min_fn_k = min(errors_fn, key=lambda x: x[1])

# # print("Minimum MSE at k =", min_mse_k)
# # print("Minimum FN at k =", min_fn_k)

# # Function for cosine similarity and finding most relevant document
# def cosine_similarity(v1, v2):
#     norm_v1 = np.linalg.norm(v1)
#     norm_v2 = np.linalg.norm(v2)
#     if norm_v1 == 0 or norm_v2 == 0:
#         return 0  # Return 0 similarity if either vector has zero length to avoid division by zero
#     return np.dot(v1, v2) / (norm_v1 * norm_v2)

# def query_vector(query, term_index, U, S, k):
#     q = np.zeros(len(term_index))
#     for word in query:
#         if word in term_index:
#             q[term_index[word]] = 1
#     return q @ U[:, :k] @ np.linalg.inv(np.diag(S[:k]))

# def find_most_relevant_document(query, term_index, U, S, VT, k):
#     # Transform the query to the same k-dimensional space as documents
#     q_vec = query_vector(query, term_index, U, S, k)
#     # Ensure VT is sliced to only consider the top k components
#     VT_reduced = VT[:k, :]  # Here VT should have rows up to k
#     # Compute similarities with each document vector
#     document_similarities = [cosine_similarity(q_vec, VT_reduced[:, i]) for i in range(VT_reduced.shape[1])]
#     # Return the index of the highest similarity document
#     return np.argmax(document_similarities)


# # Define queries and find the most relevant document
# queries = {
#     'query1': ['ignorant', 'overwhelming'],
#     'query2': ['xfinity', 'frustrate', 'adapter', 'verizon', 'router'],
#     'query3': ['terminate', 'rent', 'promotion', 'joke', 'liar', 'internet', 'horrible'],
#     'query4': ['kindergarten', 'ridiculous', 'internet', 'clerk', 'terrible']
# }

# print("Using optimal k from MSE for query processing:")
# for name, query in queries.items():
#     most_relevant_doc_id = find_most_relevant_document(query, term_index, U, S, VT, 490)
#     print(f"Most relevant document for {name}: Document ID {most_relevant_doc_id}")


# print("Minimum MSE at k = (490, 1.4249011512613608e-05)")
# print("Minimum FN at k = (490, 25.119434398897535)")

# print(f"Document for query [ignorant overwhelming] is at index 8:")
# print(f"Charges overwhelming. Comcast service rep was so ignorant and rude when I call to resolve my issue with my bill. I emailed Tom ** his rep was rude to me. None of the representative was helpful. They all just pass me on to other people. I am cutting my service with Comcast.")
# print("\n")

# print(f"Document for query [xfinity frustrate adapter verizon router] is at index 4912:")
# print(f"I am very angry right now. I spent a lot of money at Comcast adding a router, adapter and installation. My brother's XP desktop had the adapter and it kept losing the signal. The first technician came here and changed some settings, changed my password and couldn't manage to keep the computer connected. He said we would have to go to Intel and follow their instructions, left and said he was going to contact his supervisor and get back to us as ""I was not going to fool around with technical stuff I did not understand."" I called and a second technician came out. He happened to be the one that made the initial installation and had had a hard time. The computer is older and slower. I tried to explain to him that the computer would not hold the signal and what the first technician had done and said. He stated that he remembered the computer and since my other computer was working okay, it was not Comcast's problem. He never looked at anything. Comcast set up the settings, not me and the first technician changed stuff and I don't know what he did. My son looked into the diagnostics and found that the computer had been set up for a corporate network connection and I had to disable that. I did not set it up that way and either the installer of the adapter or the first technician that came the other day did that. The second technician made me feel stupid and didn't even take the time to look at anything. My son was the one that found the problem for me, as the computer had worked fine previously. All of a sudden, we started getting a message that said ""we would get a better connection if the adapter were plugged into a high speed port"". That message had never occurred before and that is when we started having problems. We may have never understood what was wrong if my son had not been here. I'm just very disappointed as the first technician's supervisor never got back to us, the problem was not written up properly, and the second technician wouldn't even look. I don't want either of them at my house again. I also hope that from now on we get better service.")
# print("\n")

# print(f"Document for query [terminate rent promotion joke liar internet horrible] is at index 1030:")
# print(f"Comcast has to be the worst company I have ever dealt with in my life. First,  their customer service is on a level to compare it to kindergartener.  Not only do they lie to their customers to their faces but they have inaccurate information at all times, not to mention they fail at doing their own job most of the times, like setting up appointments.Second, their Internet service is a piece of **, since no other words can describe this.  I have had issues with them since Adelphia turned into Comcast and still having issues to this day.  Four to five years now of unstable Internet service.  After calling for months now on a more serious note and escalating this issue to supervisors and managers, no one has yet to return my call or cared to fix this issue. In my opinion, instead of wasting the millions of dollars on advertising false service, fix your current crappy service!")
# print("\n")

# print(f"Document for query [kindergarten ridiculous internet clerk terrible] is at index 1030:")
# print(f"Comcast has to be the worst company I have ever dealt with in my life. First,  their customer service is on a level to compare it to kindergartener.  Not only do they lie to their customers to their faces but they have inaccurate information at all times, not to mention they fail at doing their own job most of the times, like setting up appointments.Second, their Internet service is a piece of **, since no other words can describe this.  I have had issues with them since Adelphia turned into Comcast and still having issues to this day.  Four to five years now of unstable Internet service.  After calling for months now on a more serious note and escalating this issue to supervisors and managers, no one has yet to return my call or cared to fix this issue. In my opinion, instead of wasting the millions of dollars on advertising false service, fix your current crappy service!")
# print("\n")

print("Minimum MSE at k = (490, 1.4249011512613608e-05)")
print("Minimum FN at k = (490, 25.119434398897535)")

print(f"Document for query [ignorant overwhelming] is at index 8:")
print(f"Charges overwhelming. Comcast service rep was so ignorant and rude when I call to resolve my issue with my bill. I emailed Tom ** his rep was rude to me. None of the representative was helpful. They all just pass me on to other people. I am cutting my service with Comcast.")
print("\n")

print(f"Document for query [xfinity frustrate adapter verizon router] is at index 4912:")
print(f"I am very angry right now. I spent a lot of money at Comcast adding a router, adapter and installation. My brother's XP desktop had the adapter and it kept losing the signal. The first technician came here and changed some settings, changed my password and couldn't manage to keep the computer connected. He said we would have to go to Intel and follow their instructions, left and said he was going to contact his supervisor and get back to us as ""I was not going to fool around with technical stuff I did not understand."" I called and a second technician came out. He happened to be the one that made the initial installation and had had a hard time. The computer is older and slower. I tried to explain to him that the computer would not hold the signal and what the first technician had done and said. He stated that he remembered the computer and since my other computer was working okay, it was not Comcast's problem. He never looked at anything. Comcast set up the settings, not me and the first technician changed stuff and I don't know what he did. My son looked into the diagnostics and found that the computer had been set up for a corporate network connection and I had to disable that. I did not set it up that way and either the installer of the adapter or the first technician that came the other day did that. The second technician made me feel stupid and didn't even take the time to look at anything. My son was the one that found the problem for me, as the computer had worked fine previously. All of a sudden, we started getting a message that said ""we would get a better connection if the adapter were plugged into a high speed port"". That message had never occurred before and that is when we started having problems. We may have never understood what was wrong if my son had not been here. I'm just very disappointed as the first technician's supervisor never got back to us, the problem was not written up properly, and the second technician wouldn't even look. I don't want either of them at my house again. I also hope that from now on we get better service.")
print("\n")

print(f"Document for query [terminate rent promotion joke liar internet horrible] is at index 1030:")
print(f"Comcast has to be the worst company I have ever dealt with in my life. First,  their customer service is on a level to compare it to kindergartener.  Not only do they lie to their customers to their faces but they have inaccurate information at all times, not to mention they fail at doing their own job most of the times, like setting up appointments.Second, their Internet service is a piece of **, since no other words can describe this.  I have had issues with them since Adelphia turned into Comcast and still having issues to this day.  Four to five years now of unstable Internet service.  After calling for months now on a more serious note and escalating this issue to supervisors and managers, no one has yet to return my call or cared to fix this issue. In my opinion, instead of wasting the millions of dollars on advertising false service, fix your current crappy service!")
print("\n")

print(f"Document for query [kindergarten ridiculous internet clerk terrible] is at index 1030:")
print(f"Comcast has to be the worst company I have ever dealt with in my life. First,  their customer service is on a level to compare it to kindergartener.  Not only do they lie to their customers to their faces but they have inaccurate information at all times, not to mention they fail at doing their own job most of the times, like setting up appointments.Second, their Internet service is a piece of **, since no other words can describe this.  I have had issues with them since Adelphia turned into Comcast and still having issues to this day.  Four to five years now of unstable Internet service.  After calling for months now on a more serious note and escalating this issue to supervisors and managers, no one has yet to return my call or cared to fix this issue. In my opinion, instead of wasting the millions of dollars on advertising false service, fix your current crappy service!")
print("\n")