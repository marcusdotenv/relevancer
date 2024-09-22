import unittest

from src.domain.models.trie import Trie



class TrieTest(unittest.TestCase):

    def test_insert_if_unique(self):
        trie = Trie("root")
        trie.insert("term")

        last_node = trie.get_root_node().get_next_node_by_letter("t")\
                                    .get_next_node_by_letter("e")\
                                    .get_next_node_by_letter("r")\
                                    .get_next_node_by_letter("m")\
        
        self.assertTrue(last_node.is_final_node())
        self.assertTrue(last_node.has_node_with_letter("*"))
        self.assertTrue(trie.search("term"))

    def test_insert_if_already_exists(self):
        trie = Trie("root")
        trie.insert("term")
        trie.insert("termm")

        last_node = trie.get_root_node().get_next_node_by_letter("t")\
                                    .get_next_node_by_letter("e")\
                                    .get_next_node_by_letter("r")\
                                    .get_next_node_by_letter("m")
        
        second_m_node = last_node.get_next_node_by_letter("m")

        self.assertTrue(last_node.has_node_with_letter("*"))
        self.assertTrue(last_node.is_final_node())
        self.assertTrue(second_m_node.has_node_with_letter("*"))
        self.assertTrue(second_m_node.is_final_node())

    def test_insert_many(self):
        trie = Trie("root")
        trie.insert_many([("term1", 0), ("term2", 0)])

        last_node = trie.get_root_node().get_next_node_by_letter("t")\
                                    .get_next_node_by_letter("e")\
                                    .get_next_node_by_letter("r")\
                                    .get_next_node_by_letter("m")\
        
        self.assertFalse(last_node.is_final_node())
        self.assertFalse(last_node.has_node_with_letter("*"))
        self.assertTrue(last_node.has_node_with_letter("1"))
        self.assertTrue(last_node.has_node_with_letter("2"))

    def test_search(self):
        trie = Trie("root")
        trie.insert("term")
        
        self.assertTrue(trie.search("term"))
        self.assertFalse(trie.search("ter"))

        trie.insert("termm")

        self.assertTrue(trie.search("term"))
        self.assertFalse(trie.search("ter"))
        self.assertTrue(trie.search("termm"))

    def test_full(self):
        trie = Trie("root")
        trie.insert("term1")
        trie.insert("term2")
        trie.insert("term3")
        trie.insert("ter")


        self.assertTrue(trie.search("term1"))
        self.assertTrue(trie.starts_with("te"))
        self.assertFalse(trie.search("te"))

    def test_find_by_prefix(self):
        trie = Trie("root")
        trie.insert("term1", 1)
        trie.insert("termm", 2)
        trie.insert("terrm", 3)
        trie.insert("ter", 4)

        related_terms = trie.find_terms_by_prefix(prefix="t", limit=10)

        self.assertEqual(len(related_terms), 4)
        self.assertEqual(related_terms, ["ter", "terrm", "termm", "term1"])

        trie.insert("term44", 100)

        new_related_terms = trie.find_terms_by_prefix(prefix="t", limit=10)
        self.assertEqual(len(new_related_terms), 5)
        self.assertEqual(new_related_terms[0], "term44")
