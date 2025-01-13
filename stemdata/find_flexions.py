from typing import List, Tuple

from stemdata.utils import commonprefix


def find_flexions(words: Tuple[str]) -> Tuple[str]:
    flexions = []
    form_variants = {}

    # region Round 1. Clashing
    for word in words:
        for word_comp in words:
            if word == word_comp:
                continue

            words_common_prefix: str = commonprefix((word, word_comp))

            if form_variants.get(words_common_prefix):
                form_variants[words_common_prefix] += [word, word_comp]
            else:
                form_variants[words_common_prefix] = [word, word_comp]
    # endregion

    # region Round 2. Remove redundant common prefixes
    ignored_prefixes: List[str] = []

    for common_prefix in form_variants.keys():
        for ref_common_prefix in form_variants.keys():
            if common_prefix == ref_common_prefix:
                continue

            if (
                ref_common_prefix.startswith(common_prefix)
                and common_prefix not in ignored_prefixes
            ):
                ignored_prefixes.append(common_prefix)

    for ignored_prefix in ignored_prefixes:
        del form_variants[ignored_prefix]
    # endregion

    # region Round 3. Unification
    # for common_prefix in form_variants.keys():
    #     form_variants[common_prefix] = tuple(set(form_variants[common_prefix]))
    # endregion

    # region Round 3. Flexions
    for common_prefix, words in form_variants.items():
        for word in words:
            flexions.append(word[len(common_prefix) :])
    # endregion

    return list(set(flexions))
