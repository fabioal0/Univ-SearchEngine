import math

class rank_alg:

    def __init__(self, index, docs_len):
        self._index = index
        self._lenghts = docs_len

    def doc_lnc(self):

        tmp = dict()

        # Replace number of occurrences of one word in one document by its weight
        for k in self._index.keys():

            # Calculate idf ( log(number of docs / number of docs where the word appears) )
            idf = math.log(len(self._lenghts) / len(self._index[k]), 10)

            # Save idf in the first position of the list associated to that word
            self._index[k] = [idf] + self._index[k]

            # Calculate weight and the sum of all (weight ** 2) for all terms in one document
            for v in self._index[k][1:]:

                # Calculate term frequency ( 1 + log(Number of times that one word occurs in this doc)).
                tf_log = 1 + math.log(v[1], 10)

                # Calculate weight (term frequency * inverse document frequency (1 here idf value na query) )
                wt = tf_log

                # Replace number of occurrences by weight
                v[1] = wt

                # Fill tmp dictionary (key = document id ; value = sum of all (weight ** 2) for all terms in one document)
                if v[0] not in tmp:
                    tmp[v[0]] = wt**2
                else:
                    tmp[v[0]] += wt**2

        # Normalize documents weight terms
        for k in self._index.keys():
            for v in self._index[k][1:]:
                v[1] /= math.sqrt(tmp[v[0]])


    def rsv_bm25(self):

        tmp = dict()

        # Calculate average document length
        avdl = sum(self._lenghts.values())/len(self._lenghts)

        # Replace number of occurrences of one word in one document by its weight
        for k in self._index.keys():

            # Calculate idf ( log(number of docs / number of docs where the word appears) )
            idf = math.log(len(self._lenghts) / len(self._index[k]), 10)

            # Save idf in the first position of the list associated to that word
            self._index[k] = [idf] + self._index[k]

            # Calculate and save the weight
            # Weight = ( (k1 + 1) * Term frequency ) /
            #          ( k1 * ((1 - b) + b * document length / average document length) + Term frequency )
            for v in self._index[k][1:]:
                res = (2.2 * v[1]) / (1.2 * (0.25 + 0.75 * self._lenghts[v[0]]/avdl) * v[1])

                # Replace number of occurrences by weight
                v[1] = res

                # Fill tmp dictionary (key = document id ; value = sum of all (weight ** 2) for all terms in one document)
                if v[0] not in tmp:
                    tmp[v[0]] = res**2
                else:
                    tmp[v[0]] += res**2

        # Normalize documents weight terms
        for k in self._index.keys():
            for v in self._index[k][1:]:
                v[1] /= math.sqrt(tmp[v[0]])


    def get_index(self):
        return self._index