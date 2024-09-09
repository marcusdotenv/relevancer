from src.entities.node import Node

class Trie:
    def __init__(self, partition_name: str) -> None:
        self.__root = Node(partition_name)

    def __print_all_nodes(self, node: Node, prefix="", is_last=True):

        node.show(prefix=prefix)

        children = list(node.get_related_nodes().values())

        for i, next_node in enumerate(children):
            is_last_child = (i == len(children) -1)
            new_prefix = prefix + ("    " if is_last else "|   ")
            self.__print_all_nodes(next_node, new_prefix, is_last_child)
    
    def print_all_nodes_from_root(self):
        self.__print_all_nodes(self.__root)
    
    def __term_to_nodes(self, term: str) -> Node:
        nodes = list(map(lambda it: Node(it), term))

        final_word_node = Node("*")
        nodes.append(final_word_node)

        for i in range(len(nodes) - 1):
            node = nodes[i]
            node.assign_new_node(nodes[i + 1])


        return nodes[0]

    def get_root_node(self) -> Node:
        return self.__root
    
    def insert_many(self, terms: list[str]):
        for term in terms:
            self.insert(term)

    def insert(self, search_term: str):
        lower_search_term = search_term.lower()
        accumulated_nodes = self.__term_to_nodes(lower_search_term)

        self.__assign_already_existing_path(lower_search_term) if self.__root.has_node_with_letter(lower_search_term[0]) else self.__root.assign_new_node(accumulated_nodes)

    def search(self, search_term: str) -> bool:
        node_to_search = self.__root

        for idx, letter in enumerate(search_term):
            if not node_to_search.has_node_with_letter(letter):
                return False
            
            node_to_search = node_to_search.get_next_node_by_letter(letter)

            if idx == len(search_term) -1:

                return node_to_search.is_final_node()
        
        return False
    
    def __assign_already_existing_path(self, search_term: str):
        next_node = self.__root

        for letter in search_term:
            if not next_node.has_node_with_letter(letter):
                next_node.assign_new_node(Node(letter))
            next_node = next_node.get_next_node_by_letter(letter)

        next_node.assign_new_node(Node("*"))

    def starts_with(self, search_term: str) -> bool:
        node_to_search = self.__root

        for letter in search_term:
            if not node_to_search.has_node_with_letter(letter):
                return False
            
            node_to_search = node_to_search.get_next_node_by_letter(letter)

            return True

    def __find_last_prefix_node(self, search_term: str) -> Node | None:
        node_to_search = self.__root

        for letter in search_term:
            if not node_to_search.has_node_with_letter(letter):
                return None
            
            node_to_search = node_to_search.get_next_node_by_letter(letter)
        
        return node_to_search

    def __collect_words_from_node_lazy(self, node: Node, prefix: str):
        if node.is_final_node():
            yield prefix

        for letter, next_node in node.get_related_nodes().items():
            if letter != "*":  
                yield from self.__collect_words_from_node_lazy(next_node, prefix + letter)

    def find_words_by_prefix(self, prefix: str, limit: int) -> list[str]:
        last_node = self.__find_last_prefix_node(search_term=prefix)
        if not last_node:
            return []
        
        word_generator = self.__collect_words_from_node_lazy(node=last_node, prefix=prefix)

        words = []
        for _ in range(limit):
            try:
                words.append(next(word_generator))
            except StopIteration:
                break 

        return words