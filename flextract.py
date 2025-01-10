import gc
import zipfile
from collections import Counter
from datetime import datetime
from os.path import commonprefix
from pathlib import Path
from typing import List, Tuple

import pytz
from lxml import etree
from ramonak.packages.actions import package_path as rm_pkg_path
from ramonak.packages.actions import require

require("@bnkorpus/grammar_db/20230920")


def find_flexions(words) -> List[str]:
    common_prefix = commonprefix(words)
    flexions = []

    if common_prefix == "":
        return flexions

    for word in words:
        if word == common_prefix:
            continue

        if len(common_prefix) - len(word) == 1:
            continue

        flexions.append(word[len(common_prefix) :])

    return flexions


def extract_stem_data(ncorp_xml_path) -> Tuple[List[str], List[str]]:
    f = etree.parse(ncorp_xml_path)
    root = f.getroot()

    print("File has been loaded in lxml")

    flexions_in_file = []
    unchangeable_words = []

    for variant in root.findall("Paradigm/Variant"):
        processed_variant_lemma = variant.get("lemma").replace("+", "")
        variant_forms = variant.findall("Form")

        processed_forms = []

        if "-" in processed_variant_lemma or " " in processed_variant_lemma:
            continue

        if (
            len(variant_forms) == 1
            and variant_forms[0].text.replace("+", "") == processed_variant_lemma
        ):
            unchangeable_words.append(processed_variant_lemma)
            continue

        for form in variant.findall("Form"):
            processed_forms.append(form.text.replace("+", ""))

        flexions = find_flexions((processed_variant_lemma, *processed_forms))
        flexions_in_file.extend(flexions)

    return flexions_in_file, unchangeable_words


def xml_stem_data_stats(xml_dir_path: str) -> Tuple[Tuple[str, int], Tuple[str]]:
    all_flexions = []
    unchangeable_words = []

    for xml_file in Path(xml_dir_path).glob("*.xml"):
        print("Processing", xml_file)
        file_stem_data = extract_stem_data(xml_file)

        all_flexions.extend(file_stem_data[0])
        unchangeable_words.extend(file_stem_data[1])
        gc.collect()

    print(
        "All flexions: {}, all unchangeable words: {}. Counting total stats...".format(
            len(all_flexions), len(unchangeable_words)
        )
    )

    flexions_and_count = Counter(all_flexions).items()
    unchangeable_words = tuple(set(unchangeable_words))

    print(
        "Unique flexions: {}, unique unchangeable words: {}. Sorting...".format(
            len(flexions_and_count), len(unchangeable_words)
        )
    )

    flexions_and_count = sorted(flexions_and_count, key=lambda x: x[1], reverse=True)

    return flexions_and_count, unchangeable_words


def build_stem_data():
    flexions_and_count, unchangeable_words = xml_stem_data_stats(
        rm_pkg_path("@bnkorpus/grammar_db/20230920")
    )

    max_count = flexions_and_count[0][1]

    # region Filter out every flexion with less than a percent
    flexions = filter(lambda x: (round(x[1] / max_count, 2) > 0), flexions_and_count)
    flexions = list(i[0] for i in flexions)
    # endregion

    # region Filter out flexions which end with other flexions
    for i, orig_flexion in enumerate(flexions):
        if orig_flexion is None:
            continue

        for k, flexion in enumerate(flexions[i:]):
            k += i

            if flexion is None:
                continue
            if orig_flexion == flexion:
                continue
            elif flexion.endswith(orig_flexion):
                flexions[k] = None

    flexions = tuple(filter(lambda x: x is not None, flexions))
    # endregion

    print("Valuable flexions: {}".format(len(flexions)))

    Path("./build").mkdir(exist_ok=True, parents=True)

    unchangeable_words = sorted(unchangeable_words)
    unchangeable_words = sorted(unchangeable_words, key=lambda x: len(x))

    with open("./build/flexions.txt", "w", encoding="utf8") as flexions_file:
        for flexion in flexions:
            flexions_file.write(flexion + "\n")

    with open(
        "./build/unchangeable_words.txt", "w", encoding="utf8"
    ) as unchangeable_words_file:
        for w in unchangeable_words:
            unchangeable_words_file.write(w + "\n")


def zip_results():
    Path("./dist/").mkdir(parents=True, exist_ok=True)

    tz = pytz.timezone("Europe/Minsk")
    minsk_now = datetime.now(tz)
    file_date_mark = f"{minsk_now:%Y%m%d_%H%M%S}"

    file_name = "./dist/STEMDATA_{}.zip".format(file_date_mark)

    print("Packing the results into '{}'...".format(file_name), end=" ")

    with zipfile.ZipFile(
        file_name,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as zip_ref:
        zip_ref.write("build/flexions.txt", arcname="flexions.txt")
        zip_ref.write("build/unchangeable_words.txt", arcname="unchangeable_words.txt")

    print("OK")


def main():
    build_stem_data()
    zip_results()


if __name__ == "__main__":
    main()
