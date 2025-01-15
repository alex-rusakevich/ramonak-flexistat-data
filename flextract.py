import gc
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import pytz
from lxml import etree
from ramonak.packages.actions import package_path as rm_pkg_path
from ramonak.packages.actions import require

from stemdata.find_flexions import find_flexions
from stemdata.utils import timing_decorator

require("@bnkorpus/grammar_db/20230920")


def extract_stem_data(ncorp_xml_path) -> Tuple[List[str], List[str]]:
    f = etree.parse(ncorp_xml_path)
    root = f.getroot()

    print("File has been fully loaded into memory. Processing...")

    flexions_in_file = []
    unchangeable_words = []

    for paradigm in root.findall("Paradigm"):
        if "0" in paradigm.get("tag", ""):  # Unchangeable paradigm
            paradigm_lemma = paradigm.get("lemma").replace("+", "")
            unchangeable_words.append(paradigm_lemma)
            continue

        for variant in paradigm.findall("Variant"):
            processed_variant_lemma = variant.get("lemma").replace("+", "")
            variant_forms = variant.findall("Form")

            processed_forms = []

            if "-" in processed_variant_lemma or " " in processed_variant_lemma:
                continue

            if len(variant_forms) == 1:
                continue

            for form in variant_forms:
                processed_forms.append(form.text.replace("+", ""))

            all_word_forms = (processed_variant_lemma, *processed_forms)

            flexions = find_flexions(all_word_forms)
            flexions_in_file.extend(flexions)

    return flexions_in_file, unchangeable_words


def move_all_to_unchangeable(xml_file):
    f = etree.parse(xml_file)
    root = f.getroot()

    print("File has been fully loaded into memory. Getting unchangeable words...")

    unchangeable_words = []

    for paradigm in root.findall("Paradigm"):
        unchangeable_words.append(paradigm.get("lemma").replace("+", ""))

    return tuple(set(unchangeable_words))


def xml_stem_data_stats(xml_dir_path: str) -> Tuple[Tuple[str, int], Tuple[str]]:
    all_flexions = []
    unchangeable_words = []

    for xml_file in Path(xml_dir_path).glob("*.xml"):
        pos = Path(xml_file).stem[:1]
        print("Processing '{}', POS is {}".format(xml_file, pos))

        file_flexions = ()
        file_unchangeable = ()

        # region Process file
        # Move all to unchangeable: Злучнік Прыназоўнік Часціца Выклічнік
        if pos in "CIEY":
            file_unchangeable = move_all_to_unchangeable(xml_file)
        else:
            file_stem_data = extract_stem_data(xml_file)
            file_flexions = tuple(set(file_stem_data[0]))
            file_unchangeable = tuple(set(file_stem_data[1]))
        # endregion

        all_flexions.extend(file_flexions)
        unchangeable_words.extend(file_unchangeable)

        # region Write data to corresponding file
        file_flexions = filter(bool, file_flexions)
        file_flexions = sorted(file_flexions, key=len, reverse=True)

        file_unchangeable = filter(bool, file_unchangeable)
        file_unchangeable = sorted(file_unchangeable, key=len)

        xml_file_stem = Path(xml_file).stem
        folder = Path("./generated_data", xml_file_stem)
        folder.mkdir(parents=True, exist_ok=True)

        (folder / "unchangeable.txt").write_text(
            "\n".join(file_unchangeable), encoding="utf8"
        )

        (folder / "flexions.txt").write_text("\n".join(file_flexions), encoding="utf8")
        # endregion

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

    return flexions_and_count, unchangeable_words


@timing_decorator
def build_stem_data():
    flexions_and_count, unchangeable_words = xml_stem_data_stats(
        rm_pkg_path("@bnkorpus/grammar_db/20230920")
    )

    # Occurance first, length second
    flexions_and_count = sorted(flexions_and_count, key=lambda x: x[1], reverse=True)

    # flexions_total = sum(i[1] for i in flexions_and_count)
    # flexions_and_count = (
    #     filter(  # Leave only flexions, which take at least 0.01% of all flexions
    #         lambda x: round(x[1] / flexions_total, 4) > 0, flexions_and_count
    #     )
    # )

    flexions = list(i[0] for i in flexions_and_count)
    flexions = sorted(flexions, key=lambda x: len(x), reverse=True)

    print("Valuable flexions: {}".format(len(flexions)))

    Path("./generated_data").mkdir(exist_ok=True, parents=True)

    unchangeable_words = sorted(unchangeable_words)
    unchangeable_words = sorted(unchangeable_words, key=lambda x: len(x))

    with open(
        "./generated_data/all_flexions.txt", "w", encoding="utf8"
    ) as flexions_file:
        for flexion in flexions:
            flexion = flexion.strip()

            if " " in flexion or flexion == "":
                continue

            flexions_file.write(flexion + "\n")

    with open(
        "./generated_data/all_unchangeable.txt", "w", encoding="utf8"
    ) as unchangeable_words_file:
        for w in unchangeable_words:
            unchangeable_words_file.write(w + "\n")


def zip_results():
    Path("./dist/").mkdir(parents=True, exist_ok=True)

    tz = pytz.timezone("Europe/Minsk")
    minsk_now = datetime.now(tz)
    file_date_mark = f"{minsk_now:%Y%m%d_%H%M%S}"

    file_name = "./dist/STEMDATA_{}".format(file_date_mark)

    print("Packing the results into '{}'...".format(file_name), end=" ")

    shutil.make_archive(file_name, "zip", "./generated_data")

    print("OK")


def main():
    if Path("./generated_data").exists():
        shutil.rmtree("./generated_data")

    build_stem_data()
    zip_results()


if __name__ == "__main__":
    main()
