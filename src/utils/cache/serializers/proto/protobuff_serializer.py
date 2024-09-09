from typing import Any
from src.utils.cache.serializers.proto import trie_pb2  
from src.entities.trie import Trie, Node
from src.utils.cache.serializers.serializer_contract import SerializerContract

class ProtobuffSerializer(SerializerContract):

    def __serialize_node(self, node: Node) -> trie_pb2.Node:

        pb_node = trie_pb2.Node(
            letter=node.letter,
            related_terms=node.get_related_terms()
        )

        for letter, related_node in node.get_related_nodes().items():
            pb_node.related_nodes[letter].CopyFrom(self.__serialize_node(related_node))

        return pb_node

    def serialize(self, trie: Trie) -> bytes:
        pb_trie = trie_pb2.Trie()

        pb_trie.root.CopyFrom(self.__serialize_node(trie.get_nodes()))
        return pb_trie.SerializeToString()

    def __deserialize_node(self, pb_node: trie_pb2.Node) -> Node:

        node = Node(pb_node.letter)
        node._Node__related_terms.extend(pb_node.related_terms)  

        for letter, pb_related_node in pb_node.related_nodes.items():
            node._Node__related_nodes[letter] = self.__deserialize_node(pb_related_node)

        return node

    def deserialize(self, serialized_bytes: bytes) -> Trie:
        pb_trie = trie_pb2.Trie()
        pb_trie.ParseFromString(serialized_bytes)
        
        trie = Trie(pb_trie.root.letter)

        root_node = self.__deserialize_node(pb_trie.root)
        trie._Trie__root = root_node 

        return trie
