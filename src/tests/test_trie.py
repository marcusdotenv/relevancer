import unittest

from src.entities.trie import Trie

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

    def test_insert_if_already_exists(self):
        trie = Trie("root")
        trie.insert("term")
        trie.insert("termm")

       # trie.print_all_nodes_from_root()

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
        trie.insert_many(["term1", "term2"])

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

        #trie.print_all_nodes_from_root()

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

    def test_assign_search_terms(self):
        trie = Trie("root")
        trie.insert("mar")
        trie.insert("marcus")
        trie.insert("matheus")
        trie.insert("macarrão")
        trie.insert("marreta")

        first_letter = trie.get_root_node().get_next_node_by_letter("m")
        self.assertEqual(["mar", "marcus", "matheus"], first_letter.get_related_terms(3))


        letter_r = first_letter.get_next_node_by_letter("a")\
                               .get_next_node_by_letter("r")
        
        self.assertEqual(["mar", "marcus"], letter_r.get_related_terms(2))
        self.assertEqual(["mar", "marcus", "marreta"], letter_r.get_related_terms(3))

    def test_find_most_relevant(self):
        trie = Trie("root")
        trie.insert("term1")
        trie.insert("term2")

        most_relevants = trie.find_most_relevant("ter", 3)

        self.assertTrue("term1" in most_relevants)
        self.assertTrue("term2" in most_relevants)

        trie.insert("terminal")
        trie.insert("terminante")

        new_relevants = trie.find_most_relevant("termi", 10)
        self.assertTrue("terminal" in new_relevants)
        self.assertTrue("terminante" in new_relevants)
        self.assertFalse("term1" in new_relevants)
        self.assertFalse("term2" in new_relevants)
    
    def test_bug_on_relevance(self):
        trie = Trie("root")
        trie.insert("Azerbaijao")
        trie.insert("azia")
        trie.insert("azimo")
        trie.insert("azias")

        trie.insert("azimos")
        trie.insert("azimute")
        trie.insert("azimutes")
        trie.insert("azotada")
        trie.insert("asteca")

        
        self.assertTrue("asteca" in trie.find_most_relevant("ast", 10))
        self.assertTrue(len(trie.find_most_relevant("ast", 10)) == 1)