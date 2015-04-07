from sumpy.preprocessor import (SentenceTokenizerMixin, WordTokenizerMixin,
    PosTaggerMixin, WordLemmatizerMixin, NamedEntityRecogMixin,
    CorpusTfidfMixin)
from sumpy.rankers import (LedeRankerMixin, TextRankMixin, LexRankMixin, 
    CentroidScoreMixin, DEMSRankerMixin)
from sumpy.document import Summary
import pandas as pd
from nltk.corpus import wordnet
import nltk

class DEMSSummarizer (SentenceTokenizerMixin, WordTokenizerMixin, 
                      PosTaggerMixin, WordLemmatizerMixin,
                      NamedEntityRecogMixin, DEMSRankerMixin):
    def __init__(self, sentence_tokenizer=None, word_tokenizer=None,
                 pos_tagger=None, word_lemmatizer=None, 
                 named_entity_recog=None):
        self._sentence_tokenizer = sentence_tokenizer
        self._word_tokenizer = word_tokenizer
        self._pos_tag = pos_tagger
        self._word_lemmatizer = word_lemmatizer
        self._named_entity_recog = named_entity_recog

    def summarize(self, docs):
        sent_tokenize = self.build_sent_tokenizer()
        word_tokenize = self.build_word_tokenizer()
        pos_tag = self.build_pos_tag()
        word_lemmatizer = self.build_word_lemmatizer()
        named_entity_recog = self.build_named_entity_recog()
        docs = [sent_tokenize(doc) for doc in docs]

        sents = []
        for doc_no, doc in enumerate(docs, 1):
            for sent_no, sent in enumerate(doc, 1):
                words = word_tokenize(sent)
                words_pos = pos_tag(words)
                lem = []
                pos = []
                for word_pos in words_pos:
                    word = word_pos[0]
                    old_pos = word_pos[1][:2]
                    morph_tag = {'NN':wordnet.NOUN,'JJ':wordnet.ADJ,
                                 'VB':wordnet.VERB,'RB':wordnet.ADV}
                    new_pos = wordnet.NOUN
                    if old_pos in morph_tag:
                        new_pos = morph_tag[old_pos]
                    word_lem = word_lemmatizer(word, new_pos)
                    pos.append(old_pos)
                    lem.append(word_lem)
                tree_ne = named_entity_recog(words_pos, binary=True)
                ne = []
                for i in range(0, len(tree_ne)):
                    if isinstance(tree_ne[i], nltk.tree.Tree):
                        ne.append(True)
                    else:
                        ne.append(False)
                sents.append({"doc": doc_no, "doc position": sent_no, 
                    "text": sent, "words": words, "pos": pos, "lem": lem,
                    "ne": ne})
        input_df = pd.DataFrame(sents, 
                                columns = ["doc", "doc position", "text",
                                            "words", "pos", "lem", "ne",
                                            "rank:demsrank", "rank:verbspec", 
                                            "rank:leadvalue",
                                            "rank:countpronoun",
                                            "rank:sentlength",
                                            "rank:location", ])
        self.demsrank(input_df)
        input_df.sort(["rank:demsrank"], inplace=True, ascending=False)
        return Summary(input_df)

class LedeSummarizer(SentenceTokenizerMixin, LedeRankerMixin):
    def __init__(self, sentence_tokenizer=None):
        self._sentence_tokenizer = sentence_tokenizer
    
    def summarize(self, docs):
        analyze = self.build_sent_tokenizer()
        docs = [analyze(doc) for doc in docs]
        
        sents = []
        for doc_no, doc in enumerate(docs, 1):
            for sent_no, sent in enumerate(doc, 1):
                sents.append({"doc": doc_no, "doc position": sent_no, 
                              "text": sent})
        input_df = pd.DataFrame(sents,
                                columns=["doc", "doc position", "text", 
                                         "rank:lede"])

        self.rank_by_lede(input_df)
        summary_df = input_df.loc[input_df["rank:lede"] == 1]
        return Summary(summary_df)
       
class TextRankSummarizer(SentenceTokenizerMixin, WordTokenizerMixin, 
                         TextRankMixin):
    def __init__(self, sentence_tokenizer=None, word_tokenizer=None):
        self._sentence_tokenizer = sentence_tokenizer
        self._word_tokenizer = word_tokenizer 

    def summarize(self, docs):
        sent_tokenize = self.build_sent_tokenizer()
        word_tokenize = self.build_word_tokenizer()
        docs = [sent_tokenize(doc) for doc in docs]
        
        sents = []
        for doc_no, doc in enumerate(docs, 1):
            for sent_no, sent in enumerate(doc, 1):
                words = word_tokenize(sent)
                sents.append({"doc": doc_no, "doc position": sent_no, 
                    "text": sent, "words": words})
        input_df = pd.DataFrame(sents,
                                columns=["doc", "doc position", "text", 
                                         "words", "rank:textrank"])

        self.textrank(input_df)
        input_df.sort(["rank:textrank"], inplace=True, ascending=False)
        return Summary(input_df)
       
class LexRankSummarizer(SentenceTokenizerMixin, WordTokenizerMixin, 
                        CorpusTfidfMixin, LexRankMixin):
    def __init__(self, sentence_tokenizer=None, word_tokenizer=None):
        self._sentence_tokenizer = sentence_tokenizer
        self._word_tokenizer = word_tokenizer 

    def summarize(self, docs):
        sent_tokenize = self.build_sent_tokenizer()
        word_tokenize = self.build_word_tokenizer()
        tfidfer = self.build_tfidf_vectorizer()
        docs = [sent_tokenize(doc) for doc in docs]
        
        sents = []
        for doc_no, doc in enumerate(docs, 1):
            for sent_no, sent in enumerate(doc, 1):
                words = word_tokenize(sent)
                sents.append({"doc": doc_no, "doc position": sent_no, 
                    "text": sent, "words": words})
        input_df = pd.DataFrame(sents,
                                columns=["doc", "doc position", "text", 
                                         "words", "rank:lexrank"])

        tfidf_mat = tfidfer(input_df[u"words"].tolist())
        self.lexrank(input_df, tfidf_mat)
        input_df.sort(["rank:lexrank"], inplace=True, ascending=False)
        return Summary(input_df)


class CentroidSummarizer(SentenceTokenizerMixin, WordTokenizerMixin,
                         CorpusTfidfMixin, CentroidScoreMixin):
    def __init__(self, sentence_tokenizer=None, word_tokenizer=None):
        self._sentence_tokenizer = sentence_tokenizer
        self._word_tokenizer = word_tokenizer
    
    def summarize(self, docs):
        sent_tokenize = self.build_sent_tokenizer()
        word_tokenize = self.build_word_tokenizer()
        tfidfer = self.build_tfidf_vectorizer()
        docs = [sent_tokenize(doc) for doc in docs]
        
        sents = []
        for doc_no, doc in enumerate(docs, 1):
            for sent_no, sent in enumerate(doc, 1):
                words = word_tokenize(sent)
                sents.append({"doc": doc_no, "doc position": sent_no, 
                    "text": sent, "words": words})
        input_df = pd.DataFrame(sents,
                                columns=["doc", "doc position", "text", 
                                         "words", "rank:centroid_score"])

        tfidf_mat = tfidfer(input_df[u"words"].tolist())
        self.centroid_score(input_df, tfidf_mat)

        input_df.sort([u"rank:centroid_score"], inplace=True, ascending=False)
        return Summary(input_df)
