import unittest

from src.domain.models.trie import Trie
from src.infrastructure.adapters.impl.serializer.proto.protobuff_serializer import ProtobuffSerializer


class TrieTest(unittest.TestCase):
    
    def test_insert_if_unique(self):
        trie = Trie("root")
        trie.insert("term1", 1)
        trie.insert("term2", 10)

        serializer = ProtobuffSerializer()
        serialized_trie = serializer.serialize(trie=trie)
        deserialized_trie = serializer.deserialize(serialized_bytes=serialized_trie)

        terms = deserialized_trie.find_terms_by_prefix("te", 10)

        self.assertEqual(len(terms), 2)
        self.assertEqual(terms[0], "term2")

        term2_last_node = deserialized_trie.get_root_node().get_next_node_by_letter("t")\
                                    .get_next_node_by_letter("e")\
                                    .get_next_node_by_letter("r")\
                                    .get_next_node_by_letter("m")\
                                    .get_next_node_by_letter("2")

        self.assertEqual(term2_last_node.letter, "2")
        self.assertEqual(term2_last_node.frequency, 10)
        