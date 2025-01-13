import itertools


def commonprefix(words):
    def all_same(x):
        return all(x[0] == y for y in x)

    char_tuples = zip(*words)
    prefix_tuples = itertools.takewhile(all_same, char_tuples)
    return "".join(x[0] for x in prefix_tuples)
