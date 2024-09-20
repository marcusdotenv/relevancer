
from src.domain.models.node import Node
from src.domain.models.trie import Trie
from src.infrastructure.adapters.contracts.serializer_contract import SerializerContract
from src.infrastructure.adapters.impl.serializer.proto import trie_pb2

class ProtobuffSerializer(SerializerContract):

    def __serialize_node(self, node: Node) -> trie_pb2.Node:

        pb_node = trie_pb2.Node(
            letter=node.letter
        )

        for letter, related_node in node.get_related_nodes().items():
            pb_node.related_nodes[letter].CopyFrom(self.__serialize_node(related_node))

        return pb_node

    def serialize(self, trie: Trie) -> bytes:
        pb_trie = trie_pb2.Trie()

        pb_trie.root.CopyFrom(self.__serialize_node(trie.get_root_node()))
        return pb_trie.SerializeToString()

    def __deserialize_node(self, pb_node: trie_pb2.Node) -> Node:

        node = Node(pb_node.letter)

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
