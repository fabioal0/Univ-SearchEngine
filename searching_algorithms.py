import math
from timeit import default_timer as timer
import Stemmer 

class search_alg:


    def __init__(self, language):
        self._index = None
        self._language = language
        self._queries = ''
        self._scores = dict()
        self._time_start = []
        self._time_end = []


    def calc_scores(self, index, choice):

        self._index = index

        # Create english stemmer
        stemmer = Stemmer.Stemmer(self._language)

        # Get queries from file
        f = open("./Files/Data/queries.txt", "r")
        self._queries = f.read().splitlines()
        f.close()

        # Calculate scores for each query based in ltc - 0 or bm25 - 1 and save results
        if choice == '0':
            for q_number, query in enumerate(self._queries):

                # Get start time (evaluation purposes only)
                self._time_start.append(timer())

                # Get query score using ltc
                score = self.__query_ltc(query, self._index, stemmer)

                # Get start time (evaluation purposes only)
                self._time_end.append(timer())

                # Save query score
                self._scores[q_number] = score

        elif choice == '1':
            for q_number, query in enumerate(self._queries):

                # Get start time (evaluation purposes only)
                self._time_start.append(timer())

                # Get query score using bm25
                score = self.__query_bm25(query, self._index, stemmer)

                # Get start time (evaluation purposes only)
                self._time_end.append(timer())

                # Save query score
                self._scores[q_number] = score


    def __query_ltc(self, line, index, stemmer):

        words = dict()
        result = dict()
        score = dict()

        factor = 0

        # Get words in lowercase from the query
        tmp = line.lower().split(' ')

        # Stemming words
        tmp = [stemmer.stemWord(k) for k in tmp]

        # Count the number of occurrences of each word
        for word in tmp:
            if word not in words:
                words[word] = 1
            else:
                words[word] += 1

        # Fill result dictionary (key = word ; value = weight)
        for word in words:
            if word in index:

                # Get idf from the word
                idf = index[word][0]

                # Calculate term frequency ( 1 + log(Number of times that one word occurs in this query)).
                tf_log = 1 + math.log(words[word], 10)

                # Calculate weight (term frequency * inverse document frequency)
                wt = tf_log * idf

            else:
                # If word not in the index weight = 0
                wt = 0

            # Fill dictionary
            result[word] = wt

            # Calculate the sum of all (weight ** 2) for all terms in the query
            factor += wt**2

        # Calculate the square root of the sum of all (weight ** 2) for all terms in the query
        factor = math.sqrt(factor)

        # Normalize query weight terms and calculate score
        for k in result.keys():
            if factor != 0 :
                result[k] /= factor
            if k in index:

                # Calculate score for each document ( sum(for each word in the query, word query weight * word doc weight) )
                for v in index[k][1:]:
                    if v[0] not in score:
                        score[v[0]] = v[1] * result[k]
                    else:
                        score[v[0]] += v[1] * result[k]

        # Sort by value and pass it to %
        score = {k: v * 100 for k, v in sorted(score.items(), key=lambda item: item[1], reverse=True)}

        return score


    def __query_bm25(self, line, index, stemmer):

        score = dict()

        # Get words in lowercase from the query
        words = list(set(line.lower().split(' ')))

        # Stemming words
        words = [stemmer.stemWord(k) for k in words]

        # Calculate score for each document ( sum(for each word in the query, idf * word doc weight) )
        for k in words:
            if k in index:
                for v in index[k][1:]:
                    if v[0] not in score:
                        score[v[0]] = v[1] * index[k][0]
                    else:
                        score[v[0]] += v[1] * index[k][0]

        # Sort by value and pass it to %
        score = {k: v * 100 for k, v in sorted(score.items(), key=lambda item: item[1], reverse=True)}

        return score


    def get_queries(self):
        return self._queries

    
    def get_scores(self):
        return self._scores


    def get_time_start(self):
        return self._time_start


    def get_time_end(self):
        return self._time_end