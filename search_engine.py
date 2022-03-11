import math
import statistics
from timeit import default_timer as timer
from tokenizer import *
from indexer import *
from ranking_algorithms import *
from searching_algorithms import *
import psutil
import os


def load_file(file_name):

    try:
        file = open("./Files/" + file_name + ".txt", "r")
        data = json.load(file)
    except IOError:
        print("The file can't be opened.")
    finally:
        file.close()

    return data


def get_results_part1(time_start, time_end, index):

    print("\n\nIndex size (MB): ", index.__sizeof__()/1024**2)
    print("Index size (Elements): ", len(index))
    print("Run time: ", time_end - time_start)

    # Sort by number of docs where the word appear and in case of same number sorted alphabetically
    res = {k: v for k, v in sorted(index.items(), key=lambda item: (len(item[1]), item[0]), reverse=True)}
    keys = list(res.keys())

    print('\nWords that appear in more documents:\n')
    for i in range(0, 10):
        print(keys[i], " : ", len(index[keys[i]]))

    print('\nWords that appear in just 1 document sorted alphabetically:\n')
    for j in range(len(keys) - 10, len(keys)):
        print(keys[j], " : ", len(index[keys[j]]))

    process = psutil.Process(os.getpid())

    print('\nProcess mem (MB): ', process.memory_info().rss/1024**2)

def get_results_part2(file_name, scores, queries, time_end, time_start):

    # Get queries relevance from file
    f = open("./Files/Data/" + file_name, "r")
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


if __name__ == '__main__':

    # Set the variables base value
    choice = 0
    language = 'english'
    stop_words = load_file('Properties/' + 'stop_words')
    symbols = load_file('Properties/' + 'symbols')
    rules = load_file('Properties/' + 'rules')
    indexer_0 = None
    search = None

    while choice != '11':

        print("\nMenu: ")
        print("1 - Change the language.")
        print("2 - Change the stop words for the custom tockenizer.")
        print("3 - Change the symbols for the simple tokenizer.")
        print("4 - Change the rules for the custom tokenizer.")
        print("5 - Create the index.")
        print("6 - Write index to file.")
        print("7 - Load index from file.")
        print("8 - Calculate rankings and search queries.")
        print("9 - Calculate results from part 1.")
        print("10 - Calculate results from part 2.")

        print("11 - Exit.\n")

        print('Choice:')
        choice = input()

        if choice == '1':

            print('Language:')
            language = input()

        elif choice == '2':

            print('Stop words file name:')
            stop_words = load_file('Properties/' + input())

        elif choice == '3':

            print('Symbols file name:')
            symbols = load_file('Properties/' + input())

        elif choice == '4':

            print('Rules file name:')
            rules = load_file('Properties/' + input())

        elif choice == '5':

            a = tokenizer(language, stop_words, symbols, rules)
            indexer_0 = indexer(a)

            print('Enter the source file name:')
            file_name = input()

            print('Chose the number of the tokenizer (0 - simple or 1 - custom):')
            number = input()

            st_start = timer()
            indexer_0.create_index(file_name, number)
            st_end = timer()

        elif choice == '6':

            if indexer_0 != None:
                indexer_0.write_index()
                indexer_0.write_titles()
                indexer_0.write_lenghts()

        elif choice == '7':

            tokenizer_0 = tokenizer(language, stop_words, symbols, rules)
            indexer_0 = indexer(tokenizer_0)

            print('Index file name:')
            indexer_0.set_index(load_file('Index/' + input()))
            
            print('Titles file name:')
            indexer_0.set_titles(load_file('Index/' + input()))

            print('Lenghts file name:')
            indexer_0.set_lenths(load_file('Index/' + input()))

        elif choice == '8':

            print('Chose the number of the algorithm (0 - lnc_ltc or 1 - bm25):')
            number1 = input()

            rank = rank_alg(indexer_0.get_index(), indexer_0.get_lenths())
            search = search_alg(language)

            if number1 == '0':

                rank.doc_lnc()
                search.calc_scores(rank.get_index(), '0')

            elif number1 == '1':

                rank.rsv_bm25()
                search.calc_scores(rank.get_index(), '1')

            else:

                print('Invalid choice!')

        elif choice == '9':

            if indexer_0 != None:
                get_results_part1(st_start, st_end, indexer_0.get_index())

        elif choice == '10':
            
            if search != None:
                get_results_part2('queries.relevance.txt', search.get_scores(), search.get_queries(), search.get_time_end(), search.get_time_start())



