import numpy as np
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
import nltk
nltk.download('punkt')
nltk.download('stopwords')

df = pd.read_csv('comcast_consumeraffairs_complaints.csv')
df.dropna(subset = ['text'], inplace = True)
df['tokens'] = df['text'].apply(lambda text: [PorterStemmer().stem(word) for word in word_tokenize(text.lower()) if word.isalpha() and word not in set(stopwords.words('english'))])

term_index = {token: idx for idx, tokens in enumerate(df['tokens']) for token in set(tokens)}
td_matrix = np.zeros((len(term_index), len(df)))
for doc_id in
