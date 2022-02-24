import csv
import json
import math
import re
import statistics
import sys
from timeit import default_timer as timer
import Stemmer
import os
import psutil

symbols = ['!', '@', '#', '&', '(', ')', '-', '[', '{', '}', ']', ':', ';', '\'', '?', '/', '*',
           '`', '~', '$', '^', '+', '=', '<', '>', '"', '\\',
           '.', ',', '_', '–', '%']

stop_words = ['a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and',
              'any', 'are', 'aren\'t', 'as', 'at', 'be', 'because', 'been', 'before',
              'being', 'below', 'between', 'both', 'but', 'by', 'can\'t', 'cannot',
              'could', 'couldn\'t', 'did', 'didn\'t', 'do', 'does', 'doesn\'t', 'doing',
              'don\'t', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had',
              'hadn\'t', 'has', 'hasn\'t', 'have', 'haven\'t', 'having', 'he', 'he\'d',
              'he\'ll', 'he\'s', 'her', 'here', 'here\'s', 'hers', 'herself', 'him',
              'himself', 'his', 'how', 'how\'s', 'i', 'i\'d', 'i\'ll', 'i\'m', 'i\'ve',
              'if', 'in', 'into', 'is', 'isn\'t', 'it', 'it\'s', 'its', 'itself', 'let\'s',
              'me', 'more', 'most', 'mustn\'t', 'my', 'myself', 'no', 'nor', 'not', 'of',
              'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours',
              'ourselves', 'out', 'over', 'own', 'same', 'shan\'t', 'she', 'she\'d',
              'she\'ll', 'she\'s', 'should', 'shouldn\'t', 'so', 'some', 'such', 'than',
              'that', 'that\'s', 'the', 'their', 'theirs', 'them', 'themselves', 'then',
              'there', 'there\'s', 'these', 'they', 'they\'d', 'they\'ll', 'they\'re',
              'they\'ve', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up',
              'very', 'was', 'wasn\'t', 'we', 'we\'d', 'we\'ll', 'we\'re', 'we\'ve',
              'were', 'weren\'t', 'what', 'what\'s', 'when', 'when\'s', 'where', 'where\'s',
              'which', 'while', 'who', 'who\'s', 'whom', 'why', 'why\'s', 'with', 'won\'t',
              'would', 'wouldn\'t', 'you', 'you\'d', 'you\'ll', 'you\'re', 'you\'ve', 'your',
              'yours', 'yourself', 'yourselves']

token_specification = [
    ('SITE', r'.https://.+'),  # Site
    ('EMAIL', r'.[a-z.-]+@[a-z]+(\.[a-z]+)+'),  # Email
    ('WORD', r'( |\()([a-z0-9]+-)?[a-z]{3}[a-z]*(-[a-z0-9]+)*'),  # Word  2019-nCoV  SARS-CoV-2
    ('NUMBER', r'.\d+(\.\d+)?'),  # Integer or decimal number
]


def read_file(doc_name, option, option1):

    index = dict()
    dl = dict()
    titles = []

    # Get rules
    tok_reg = '|'.join('(?P<%s>%s)' % exp for exp in token_specification)

    # Create english stemmer
    stemmer = Stemmer.Stemmer('english')

    # Read csv file data
    with open(doc_name, newline='', encoding="utf8") as csv_file:
        rows = csv.DictReader(csv_file)
        for ID, row in enumerate(rows):

            # Check if the documents have data
            if row['abstract'] != '':

                # If list >4GB write data to file and clean the list. Else append title and id to the list.
                if titles.__sizeof__() + row['title'].__sizeof__() > 4 * 1024 ** 3:
                    write_titles(titles)
                    titles.clear()
                else:
                    titles.append((row['title'], row['cord_uid']))

                # Chose tokenizer simples - 0 or custom - 1.
                # Collect all tokens and the number of times that they appear on the document.
                if option == '0':
                    tokens = s_tokenizer(row['abstract'])
                elif option == '1':
                    tokens = custom_tokenizer(row['abstract'], tok_reg, stemmer)
                else:
                    tokens = s_tokenizer(row['abstract'])

                # Append data to the index ( key = word ; value = [[doc_id, count], [doc_id, count], ...] )
                create_index(tokens, row['cord_uid'], index)

                # Calculate document length
                dl[row['cord_uid']] = sum(tokens.values())

    # Calculate average document length
    avdl = sum(dl.values())/len(dl)

    # Chose method of calculate weight lnc - 0 or bm25 - 1.
    # Replace count by weight.
    if option1 == '0':
        doc_lnc(index, len(dl))
    elif option1 == '1':
        rsv_bm25(index, len(dl), dl, avdl)
    else:
        print('invalid choice')
        sys.exit()

    return index, titles


def s_tokenizer(text):

    res = dict()

    # Set symbols to replace in the text (digits + symbols inside symbols variable)
    regex = re.compile(r"\d|" + "|".join(map(re.escape, symbols)))

    # Replace symbols by empty space in the text
    result = regex.sub(lambda match: ' ', text)

    # Lower case text
    text = re.sub(r'[A-Z]+', lambda pat: pat.group(0).lower(), result)

    # Split words in the text by space
    result = re.split(r"\s+", text)

    #  Fill res dictionary (key = word ; value = number of occurrences in this document)
    for k in result:

        # Filter words with less tha 3 characters
        if len(k) > 2:

            # Count the number of occurrences of one word
            if k in res:
                res[k] += 1
            else:
                res[k] = 1

    return res


def custom_tokenizer(data, tok_reg, stemmer):

    result = dict()

    # Lower case text
    text = re.sub(r'[A-Z]+', lambda pat: pat.group(0).lower(), data)

    # Get words that respect predetermined rules
    words, others = get_words(text, tok_reg)

    # Remove stop words
    words = {k: v for k, v in words.items() if k not in stop_words}

    # Fill result dictionary (key = word ; value = number of occurrences in this document)
    for k, v in words.items():

        # Stemming resulting words
        tmp = stemmer.stemWord(k)

        # Filter stop words
        if tmp not in stop_words:

            # Join counts from same word after stemming
            if tmp in result:
                result[tmp] += v
            else:
                result[tmp] = v

    # Merge stemmed words with expressions that dont need stemming (digits, emails and websites)
    result.update(others)

    return result


def get_words(data, tok_reg):

    words = dict()
    others = dict()

    # Separate words from other expressions based on the rules defined in token_specification variable
    for mo in re.finditer(tok_reg, data):
        if mo.lastgroup == 'WORD':

            # Count the number of occurrences of one word
            if mo.group()[1:] in words:
                words[mo.group()[1:]] += 1
            else:
                words[mo.group()[1:]] = 1
        else:

            # Count the number of occurrences of other expression
            if mo.group()[1:] in others:
                others[mo.group()[1:]] += 1
            else:
                others[mo.group()[1:]] = 1

    return words, others


def doc_lnc(index, doc_count):

    tmp = dict()

    # Replace number of occurrences of one word in one document by its weight
    for k in index.keys():

        # Calculate idf ( log(number of docs / number of docs where the word appears) )
        idf = math.log(doc_count / len(index[k]), 10)

        # Save idf in the first position of the list associated to that word
        index[k] = [idf] + index[k]

        # Calculate weight and the sum of all (weight ** 2) for all terms in one document
        for v in index[k][1:]:

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
    for k in index.keys():
        for v in index[k][1:]:
            v[1] /= math.sqrt(tmp[v[0]])

    return index


def query_ltc(line, index, stemmer):

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


def rsv_bm25(index, doc_count, dl, avdl):

    tmp = dict()

    # Replace number of occurrences of one word in one document by its weight
    for k in index.keys():

        # Calculate idf ( log(number of docs / number of docs where the word appears) )
        idf = math.log(doc_count / len(index[k]), 10)

        # Save idf in the first position of the list associated to that word
        index[k] = [idf] + index[k]

        # Calculate and save the weight
        # Weight = ( (k1 + 1) * Term frequency ) /
        #          ( k1 * ((1 - b) + b * document length / average document length) + Term frequency )
        for v in index[k][1:]:
            res = (2.2 * v[1]) / (1.2 * (0.25 + 0.75 * dl[v[0]]/avdl) * v[1])

            # Replace number of occurrences by weight
            v[1] = res

            # Fill tmp dictionary (key = document id ; value = sum of all (weight ** 2) for all terms in one document)
            if v[0] not in tmp:
                tmp[v[0]] = res**2
            else:
                tmp[v[0]] += res**2

    # Normalize documents weight terms
    for k in index.keys():
        for v in index[k][1:]:
            v[1] /= math.sqrt(tmp[v[0]])

    return index


def query_bm25(line, index, stemmer):

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


def create_index(data, doc_id, index):
    # Verify if the index + the data to be added is bigger than 4GB. If true, write to disk and clear the index
    if index.__sizeof__() + data.__sizeof__() > 4*1024**3:
        write_index(index)
        index.clear()

    # Add words and document id to the dictionary
    for k, v in data.items():
        # If dictionary dont contain the term, add it and create list to record documents ID
        if k not in index:
            index[k] = []
        # Add document ID to the respective key
        index[k].append([doc_id, v])


def calculate_scores(file_name, index):

    scores = dict()
    time_start = []
    time_end = []

    # Create english stemmer
    stemmer = Stemmer.Stemmer('english')

    # Get queries from file
    f = open(file_name, "r")
    queries = f.read().splitlines()
    f.close()

    # Calculate scores for each query based in ltc - 0 or bm25 - 1 and save results
    if sys.argv[3] == '0':
        for q_number, query in enumerate(queries):

            # Get start time (evaluation purposes only)
            time_start.append(timer())

            # Get query score using ltc
            score = query_ltc(query, index, stemmer)

            # Get start time (evaluation purposes only)
            time_end.append(timer())

            # Save query score
            scores[q_number] = score

    elif sys.argv[3] == '1':
        for q_number, query in enumerate(queries):

            # Get start time (evaluation purposes only)
            time_start.append(timer())

            # Get query score using bm25
            score = query_bm25(query, index, stemmer)

            # Get start time (evaluation purposes only)
            time_end.append(timer())

            # Save query score
            scores[q_number] = score

    else:
        print('invalid choice')
        sys.exit()

    return queries, scores, time_start, time_end


def write_index(index):
    # Get from directory "Indice" the documet text tha start with "indice"
    direc = [k for k in os.listdir('./Indice') if k.startswith('indice')]

    # If none set doc_id to 0. Else get doc_id from the last document added and sum 1
    if len(direc) == 0:
        doc_id = 0
    else:
        doc_id = len(direc)

    # Open document to write
    f = open("./Indice/indice" + str(doc_id) + ".txt", "w")

    # Sort dictionary by key to facilitate merge documents later
    res = {k: v for k, v in sorted(index.items(), key=lambda item:  item[0])}

    # Write dictionary to disk
    f.write(json.dumps(res))

    # Close document
    f.close()


def write_titles(titles):
    # Open document to write (append mode)
    f = open("./Indice/titles.txt", "a")

    # Write every entry from the list (title, doc_ID) to disk
    for k in titles:
        f.write(json.dumps(k))

    # Close document
    f.close()


def merge_files():
    # TODO merge the 4 Gb indexes if more than 1 exists (separated thread to increase performance)
    print()


def get_results_part1(time_start, time_end, index):

    print("\n\nIndex size (MB): ", index.__sizeof__()/1024**2)
    print("Index size (Elements): ", len(index))
    print("Run time: ", time_end - time_start)

    # Sort by number of docs where the word appear and in case of same number sorted alphabetically
    res = {k: v for k, v in sorted(index.items(), key=lambda item: (len(item[1]), item[0]), reverse=True)}
    keys = list(res.keys())

    print('\nWords that appear in more documents:\n')
    for i in range(0, 10):
        print(keys[i], " : ", len(index[keys[i]]) - 1)

    print('\nWords that appear in just 1 document sorted alphabetically:\n')
    for j in range(len(keys) - 10, len(keys)):
        print(keys[j], " : ", len(index[keys[j]]) - 1)

    process = psutil.Process(os.getpid())

    print('\nProcess mem (MB): ', process.memory_info().wset/1024**2)
    print('Process mem peak (MB): ', process.memory_info().peak_wset/1024**2)


def get_results_part2(file_name, scores, queries, time_end, time_start):

    # Get queries relevance from file
    f = open(file_name, "r")
    lines = f.read().splitlines()
    f.close()

    # Initiate dictionaries
    relevant1 = dict()
    relevant2 = dict()

    # Fill the dictionaries with the query number
    for count in range(0, len(queries)):
        relevant1[count] = dict()
        relevant2[count] = dict()

    # Add document id to the correct dictionaries accordingly with the relevance
    for line in lines:
        fields = line.split(' ')

        if fields[2] == '1':
            relevant1[int(fields[0])-1][fields[1]] = 0
        elif fields[2] == '2':
            relevant2[int(fields[0])-1][fields[1]] = 0

    # Calculate duration of each query
    times = [time_end[k] - time_start[k] for k in range(0, len(time_start))]

    # Get metrics
    pre1, rec1, f_m1, a_p1, ndcg1 = calc_metrics(10, relevant1, relevant2, scores, queries)
    pre2, rec2, f_m2, a_p2, ndcg2 = calc_metrics(20, relevant1, relevant2, scores, queries)
    pre3, rec3, f_m3, a_p3, ndcg3 = calc_metrics(50, relevant1, relevant2, scores, queries)

    print('\nQuery\t'
          'Precision\t\t\t'
          'Recall\t\t\t\t'
          'F Measure\t\t\t'
          'MAP\t\t\t\t'
          'NDCG\t\t\t\t'
          'latency')

    print('\t'
          'TOP10\tTOP20\tTOP30\t\t'
          'TOP10\tTOP20\tTOP30\t\t'
          'TOP10\tTOP20\tTOP30\t\t'
          'TOP10\tTOP20\tTOP30\t\t'
          'TOP10\tTOP20\tTOP30')

    for count, query in enumerate(queries):
        print('{:d} -\t'
              '{:3.2f} %\t{:3.2f} %\t{:3.2f} %\t\t'
              '{:3.2f} %\t{:3.2f} %\t{:3.2f} %\t\t'
              '{:3.2f} %\t{:3.2f} %\t{:3.2f} %\t\t'
              '{:3.2f} %\t{:3.2f} %\t{:3.2f} %\t\t'
              '{:3.2f} %\t{:3.2f} %\t{:3.2f} %\t\t'
              '{:3.2f} ms'
              .format(
                        count+1,
                        (pre1[count] * 100), (pre2[count] * 100), (pre3[count] * 100),
                        (rec1[count] * 100), (rec2[count] * 100), (rec3[count] * 100),
                        (f_m1[count] * 100), (f_m2[count] * 100), (f_m3[count] * 100),
                        (a_p1[count] * 100), (a_p2[count] * 100), (a_p3[count] * 100),
                        (ndcg1[count] * 100), (ndcg2[count] * 100), (ndcg3[count] * 100),
                        times[count]*1000))

    print('mean -\t'
          '{:3.2f} %\t{:3.2f} %\t{:3.2f} %\t\t'
          '{:3.2f} %\t{:3.2f} %\t{:3.2f} %\t\t'
          '{:3.2f} %\t{:3.2f} %\t{:3.2f} %\t\t'
          '{:3.2f} %\t{:3.2f} %\t{:3.2f} %\t\t'
          '{:3.2f} %\t{:3.2f} %\t{:3.2f} %\t\t'
          'median - {:3.2f} ms'
          .format(
                    (statistics.fmean(pre1) * 100), (statistics.fmean(pre2) * 100), (statistics.fmean(pre3) * 100),
                    (statistics.fmean(rec1) * 100), (statistics.fmean(rec2) * 100), (statistics.fmean(rec3) * 100),
                    (statistics.fmean(f_m1) * 100), (statistics.fmean(f_m2) * 100), (statistics.fmean(f_m3) * 100),
                    (statistics.fmean(a_p1) * 100), (statistics.fmean(a_p2) * 100), (statistics.fmean(a_p3) * 100),
                    (statistics.fmean(ndcg1) * 100), (statistics.fmean(ndcg2) * 100), (statistics.fmean(ndcg3) * 100),
                    statistics.median(times) * 1000))

    print('\nQuery throughput: {:3.2f} queries'.format(1/(sum(times)/50)))


def calc_metrics(top_num, relevant1, relevant2, scores, queries):

    pre = []
    rec = []
    f_m = []
    a_p = []
    ndcg = []

    for q_number, query in enumerate(queries):

        tp = 0
        fp = 0
        ap = 0

        # Get list with top {10, 20, 50} high scores
        top = list(scores[q_number].keys())[:top_num]

        # Calculate values (tp - documents relevant retrieved , fp -  documents non relevant retrieved)
        for doc_number in range(0, top_num):
            if top[doc_number] in relevant1[q_number] or top[doc_number] in relevant2[q_number]:
                tp += 1
                ap += tp / (tp + fp)
            else:
                fp += 1

        # Get the number of relevant documents to the query
        doc_relevant = len(relevant1[q_number]) + len(relevant2[q_number])

        # Calculate fn - documents relevant non retrieved
        fn = doc_relevant - tp

        # Get Precision for the query
        if fp != 0 or tp != 0:
            pre.append(tp / (tp + fp))
        else:
            pre.append(0)

        # Get Recall for the query
        if fn != 0 or tp != 0:
            rec.append(tp / (tp + fn))
        else:
            rec.append(0)

        # Get F measure for the query
        b = 1

        if rec[q_number] != 0 or pre[q_number] != 0:
            f_m.append(((b**2 + 1) * rec[q_number] * pre[q_number]) / (rec[q_number] + b**2 * pre[q_number]))
        else:
            f_m.append(0)

        # Get Average Precision (AP)
        if tp != 0:
            a_p.append(ap/tp)
        else:
            a_p.append(0)

        # Get Normalized Discounted Cumulative Gain (NDCG)
        rel_list = []

        for doc_number in range(0, top_num):
            if top[doc_number] in relevant1[q_number]:
                rel_list.append(1)
            elif top[doc_number] in relevant2[q_number]:
                rel_list.append(2)
            else:
                rel_list.append(0)

        i_rel_list = sorted(rel_list, reverse=True)

        dcg = rel_list[0]
        idcg = i_rel_list[0]

        for count in range(1, top_num):
            dcg += rel_list[count]/math.log(count + 1, 2)
            idcg += i_rel_list[count]/math.log(count + 1, 2)

        if idcg != 0:
            ndcg.append(dcg/idcg)
        else:
            ndcg.append(0)

    return pre, rec, f_m, a_p, ndcg


def main():

    # Tokenizer execution
    st_start = timer()
    index, titles = read_file(sys.argv[1], sys.argv[2], sys.argv[3])
    st_end = timer()

    # Calculate documents scores to the queries
    queries, scores, time_start, time_end = calculate_scores("queries.txt", index)

    # Write data to external file
    write_titles(titles)
    write_index(index)

    # Print results
    get_results_part1(st_start, st_end, index)
    get_results_part2('queries.relevance.txt', scores, queries, time_end, time_start)


if __name__ == '__main__':
    main()
