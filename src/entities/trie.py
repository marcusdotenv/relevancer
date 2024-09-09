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
            node.assign_related_term(term)


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
            next_node.assign_related_term(search_term)

        next_node.assign_new_node(Node("*"))
    
    def find_most_relevant(self, search_term: str, amount: int) -> list[str]:
        node_to_search = self.__root
        for letter in search_term:
            if not node_to_search.has_node_with_letter(letter):
                return [] # d~uvida nessa regra aqui
            
            node_to_search = node_to_search.get_next_node_by_letter(letter)

        return node_to_search.get_related_terms(amount)

    def starts_with(self, search_term: str) -> bool:
        node_to_search = self.__root

        for letter in search_term:
            if not node_to_search.has_node_with_letter(letter):
                return False
            
            node_to_search = node_to_search.get_next_node_by_letter(letter)

            return True