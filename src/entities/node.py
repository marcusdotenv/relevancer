from __future__ import annotations

class Node:
    def __init__(self, letter: str) -> None:
        self.letter = letter
        self.__related_nodes = {}
        self.__related_terms = []
    
    def assign_new_node(self, next_node: Node):
        letter = next_node.letter.lower()

        self.__related_nodes.update({letter: next_node})
    
    def assign_related_term(self, term: str):
        self.__related_terms.append(term)

    def get_related_terms(self, amount: int):
        return self.__related_terms[:amount]

    def is_final_node(self):
        return self.has_node_with_letter("*")

    def has_node_with_letter(self, letter: str) -> bool:
        return letter in self.__related_nodes.keys()
    
    def get_related_nodes(self) -> dict[str, Node]:
        return self.__related_nodes

    def get_next_node_by_letter(self, letter: str) -> Node:
        return self.__related_nodes.get(letter)

    def show(self, prefix=""):
        string_to_show = f"{prefix}|-- {self.letter}"

        print(string_to_show)
