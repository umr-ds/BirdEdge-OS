#!/usr/bin/env python3

import subprocess
import argparse
import sys
import io
import logging
import csv
import time

# manpage: https://docs.nvidia.com/drive/drive_os_5.1.6.1L/nvvib_docs/index.html#page/DRIVE_OS_Linux_SDK_Development_Guide/Utilities/util_tegrastats.html

# PLL@28C CPU@31C PMIC@50C GPU@29.5C AO@33C thermal@30.25C

KEYWORDS = {
    # RAM 2436/3964MB (lfb 107x4MB)
    "RAM": lambda ram: ram[1].split("/")[0],
    # SWAP 0/1982MB (cached 0MB)
    "SWAP": lambda swap: swap[1].split("/")[0],
    # IRAM 0/252kB(lfb 252kB)
    "IRAM": lambda iram: iram[1].split("/")[0],
    # CPU [93%@614,93%@614,off,off]
    "CPU": lambda cpu: [core.split("%")[0] for core in cpu[1][1:-1].split(",")],
    # EMC_FREQ 9%@1600
    "EMC_FREQ": lambda s: s[1].split("%")[0],
    # GR3D_FREQ 99%@230
    "GR3D_FREQ": lambda s: dict(zip(["UTIL", "FREQ"], s[1].split("%@"))),
    # POM_5V_IN 2799/3164
    "POM_5V_IN": lambda s: dict(zip(["CUR", "AVG"], s[1].split("/"))),
    # POM_5V_GPU 393/679
    "POM_5V_GPU": lambda s: dict(zip(["CUR", "AVG"], s[1].split("/"))),
    # POM_5V_CPU 590/554
    "POM_5V_CPU": lambda s: dict(zip(["CUR", "AVG"], s[1].split("/"))),
    # APE 25
    "APE": lambda s: s[1]
}

parser = argparse.ArgumentParser(
    prog='tegrastats',
    description='A tegrastats wrapper',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="count", default=0)
parser.add_argument("-i", "--interval", help="sample the information in <milliseconds>", default=1000)
parser.add_argument("-l", "--logfile", help="dump the output of tegrastats to <filename>", type=argparse.FileType('w'), default=sys.stdout)


def parse_tegraline(line):
    out = {"TIME": time.time()}

    logging.debug(line)

    elems = line.split()
    last_keyword_i = -1
    for i in range(len(elems)+1):
        # continue if there is no keyword
        if i < len(elems):
            if elems[i] not in KEYWORDS:
                # directly consume temperature values, as they do not contain a keyword
                if elems[i].endswith("C"):
                    keyword, temp = elems[i][:-1].split("@")
                    out[keyword] = temp

                continue

        # if there has been a keyword before, parse it
        if last_keyword_i >= 0:
            keyword = elems[last_keyword_i]
            res = KEYWORDS[keyword](elems[last_keyword_i:i])
            if isinstance(res, list):
                res = {f"{keyword}_{i}": x for i, x in enumerate(res)}
            elif isinstance(res, dict):
                res = {f"{keyword}_{k}": v for k, v in res.items()}
            else:
                res = {keyword: res}

            out.update(res)

        last_keyword_i = i

    return out


if __name__ == "__main__":
    args = parser.parse_args()

    logging_level = logging.WARNING - 10 * args.verbose
    logging.basicConfig(level=logging_level)

    cmd = ["tegrastats", "--interval", str(args.interval)]
    if args.verbose:
        cmd += ["--verbose"]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    writer = None

    for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):
        parsed = parse_tegraline(line[:-1])

        if not writer:
            writer = csv.DictWriter(args.logfile, fieldnames=parsed.keys())
            writer.writeheader()

        writer.writerow(parsed)
