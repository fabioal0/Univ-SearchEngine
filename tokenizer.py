import re
import json
import Stemmer 

class tokenizer:

    def __init__(self, language, stop_words, symbols, rules):
        self._rules = '|'.join('(?P<%s>%s)' % (exp[0],exp[1]) for exp in rules)
        self._stemmer = Stemmer.Stemmer(language)
        self._stop_words = stop_words
        self._symbols = symbols

    def simple_tokenizer(self, text):

        tokens = dict()

        # Set symbols to replace in the text (digits + symbols inside symbols variable)
        regex = re.compile(r"\d|" + "|".join(map(re.escape, self._symbols)))

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
                if k in tokens:
                    tokens[k] += 1
                else:
                    tokens[k] = 1

        return tokens

    def custom_tokenizer(self, data):

        result = dict()
        words = dict()
        others = dict()

        # Lower case text
        text = re.sub(r'[A-Z]+', lambda pat: pat.group(0).lower(), data)

        # Separate words from other expressions based on the rules defined in token_specification variable
        for mo in re.finditer(self._rules, text):
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

        # Remove stop words
        words = {k: v for k, v in words.items() if k not in self._stop_words}

        # Fill result dictionary (key = word ; value = number of occurrences in this document)
        for k, v in words.items():

            # Stemming resulting words
            tmp = self._stemmer.stemWord(k)

            # Filter stop words
            if tmp not in self._stop_words:

                # Join counts from same word after stemming
                if tmp in result:
                    result[tmp] += v
                else:
                    result[tmp] = v

        # Merge stemmed words with expressions that dont need stemming (digits, emails and websites)
        result.update(others)

        return result

    def get_stop_words(self):
        return self._stop_words
    
    def get_symbols(self):
        return self._symbols

    def get_rules(self):
        return self._rules

    def set_stop_words(self, data):
        self._stop_words = data

    def set_symbols(self, data):
        self._symbols = data
    
    def set_rules(self, data):
        self._rules ='|'.join('(?P<%s>%s)' % (exp[0],exp[1]) for exp in data)
