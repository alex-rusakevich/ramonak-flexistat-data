import zipfile
from datetime import datetime
from pathlib import Path

import pytz


def zip_results():
    Path("./dist/").mkdir(parents=True, exist_ok=True)

    tz = pytz.timezone("Europe/Minsk")
    minsk_now = datetime.now(tz)
    file_date_mark = f"{minsk_now:%Y%m%d}"

    with zipfile.ZipFile(
        "./dist/STEMDATA_{}.zip".format(file_date_mark),
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as zip_ref:
        zip_ref.write("build/flexions.txt", arcname="flexions.txt")
        zip_ref.write("build/unchangeable_words.txt", arcname="unchangeable_words.txt")


if __name__ == "__main__":
    zip_results()
