import csv
import os
import json

class indexer:

    def __init__(self, token):
        self._tokenizer = token
        self._index = dict()
        self._titles = []
        self._lenths = dict()

    def create_index(self, doc_name, option):
        # Read csv file data
        with open("./Files/Data/" + doc_name) as csv_file:
            rows = csv.DictReader(csv_file)
            for ID, row in enumerate(rows):

                # Check if the documents have data
                if row['abstract'] != '':

                    # Append title and id to the list.
                    self._titles.append((row['title'], row['cord_uid']))

                    # Chose simple tokenizer - 0 or custom - any other.
                    # Collect all tokens and the number of times that they appear on the document.
                    if option == '0':
                        tokens = self._tokenizer.simple_tokenizer(row['abstract'])
                    else:
                        tokens = self._tokenizer.custom_tokenizer(row['abstract'])

                    # Calculate documents length
                    self._lenths[row['cord_uid']] = sum(tokens.values())

                    # Append data to the index ( key = word ; value = [[doc_id, count], [doc_id, count], ...] )
                    for k, v in tokens.items():
                        # If dictionary dont contain the term, add it and create list to record documents ID
                        if k not in self._index:
                            self._index[k] = []
                        # Add document ID to the respective key
                        self._index[k].append([row['cord_uid'], v])

    def write_index(self):
        # Get from directory "Indice" the documet text tha start with "indice"
        direc = [k for k in os.listdir('./Files/Index') if k.startswith('index_')]

        # If none set doc_id to 0. Else get doc_id from the last document added and sum 1
        if len(direc) == 0:
            doc_id = 0
        else:
            doc_id = len(direc)

        # Open document to write
        f = open("./Files/Index/index_" + str(doc_id) + ".txt", "w")

        # Sort dictionary by key to facilitate merge documents later
        res = {k: v for k, v in sorted(self._index.items(), key=lambda item:  item[0])}

        # Write dictionary to disk
        f.write(json.dumps(res))

        # Close document
        f.close()

    def write_titles(self):
        # Get from directory "Indice" the documet text tha start with "indice"
        direc = [k for k in os.listdir('./Files/Index') if k.startswith('titles_')]

        # If none set doc_id to 0. Else get doc_id from the last document added and sum 1
        if len(direc) == 0:
            doc_id = 0
        else:
            doc_id = len(direc)

        # Open document to write
        f = open("./Files/Index/titles_" + str(doc_id) + ".txt", "w")

        # Write every entry from the list (title, doc_ID) to disk
        f.write(json.dumps(self._titles))

        # Close document
        f.close()

    def write_lenghts(self):
        # Get from directory "Indice" the documet text tha start with "indice"
        direc = [k for k in os.listdir('./Files/Index') if k.startswith('lenghts_')]

        # If none set doc_id to 0. Else get doc_id from the last document added and sum 1
        if len(direc) == 0:
            doc_id = 0
        else:
            doc_id = len(direc)

        # Open document to write
        f = open("./Files/Index/lenghts_" + str(doc_id) + ".txt", "w")

        # Write every entry from the list (title, doc_ID) to disk
        f.write(json.dumps(self._lenths))

        # Close document
        f.close()

    def get_index(self):
        return self._index
    
    def get_titles(self):
        return self._titles

    def get_tokenizer(self):
        return self._tokenizer

    def get_lenths(self):
        return self._lenths

    def set_index(self, value):
        self._index = value

    def set_titles(self, value):
        self._titles = value
    
    def set_tokenizer(self, value):
        self._tokenizer = value

    def set_lenths(self,value):
        self._lenths = value