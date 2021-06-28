#! /usr/bin/python3

# Linux CLI workout assistant

import math
from columnar import columnar
import json
import os
from posixpath import expanduser
import subprocess
import argparse
from pathlib import Path
from colored import fg, attr
import logging

FORMAT = f"%(filename)s: {attr('bold')}%(levelname)s {fg(3)+attr('bold')}%(message)s{attr('reset')} line: %(lineno)s, %(relativeCreated)dms"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

logging.disable(logging.WARNING)

data_path = os.path.join(Path.home(), ".local/share/trening.json")


class Trening(object):

    def __init__(self) -> None:
        self.data_path = data_path
        self.load_conf()

    def load_conf(self) -> None:
        with open(self.data_path) as f:
            self.config = json.load(f)

    def determine_exercise(self) -> None:
        index = self.config["exercise_order"].index(
            self.config["last_exercise"])
        if index + 1 < len(self.config["exercise_order"]):
            self.current_exercise = self.config["exercise_order"][index + 1]
            self.current_cycle = self.config["last_cycle"]
        else:
            index = self.config["cycle_order"].index(self.config["last_cycle"])
            if index + 1 < len(self.config["cycle_order"]):
                self.current_cycle = self.config["cycle_order"][index + 1]
            else:
                self.current_cycle = self.config["cycle_order"][0]

            self.current_exercise = self.config["exercise_order"][0]

        self.cycle_rms = self.config[self.current_cycle + "_RMs"]
        self.one_rm = self.config["exercises"][self.current_exercise]["1RM"]
        self.maximum = self.config["exercises"][self.current_exercise]["max"]
        self.record = self.config["exercises"][self.current_exercise]["record"]
        self.calculate_set_weights()

    def calculate_set_weights(self) -> None:
        self.weights = []
        for rm in self.cycle_rms:
            if self.current_exercise == "chin-up":
                weight = self.config["percents"][rm] * \
                    self.one_rm - self.config["my_weight"]
                if weight < 0:
                    weight = 0
            else:
                weight = self.config["percents"][rm] * self.one_rm

            weight = weight // self.config["weight_inc"] * \
                self.config["weight_inc"]
            self.weights.append(weight)

    def print_exercise(self) -> None:
        self.determine_exercise()
        os.system("clear")

        for w in self.weights[0:-1]:
            if self.current_cycle == 'neural':
                print(f"\t\t{w:>5}\tx {self.cycle_rms[-1]}")
            else:
                reps = self.cycle_rms[-1] - self.config["metabolic_rep_dec"]
                print(f"\t\t{w:>5}\tx {reps}")

        if self.current_cycle == 'neural':
            exercise = fg(1) + attr(1) + \
                self.current_exercise.title() + ":" + attr("reset")
            print(f"\n  {exercise:<10}\t{self.weights[-1]:>5}\tx max")
        else:
            exercise = fg(2) + attr(1) + \
                self.current_exercise.title() + ":" + attr("reset")
            reps = self.cycle_rms[-1] - self.config["metabolic_rep_dec"]
            print(f"\n  {exercise:<10}\t{self.weights[-1]:>5}\tx {reps}")

    def calculate_new_1rm(self) -> None:
        if self.current_cycle == "neural":
            while True:
                reps = input(
                    f"\n  {attr('bold')}Puta podigao: {attr('reset')}")
                if reps.isdigit() and 0 <= int(reps) < 10:
                    break

            weight = self.config["exercises"][self.current_exercise]["1RM"]
            ratio = self.config["percents"][self.cycle_rms[-1]
                                            ] / self.config["percents"][int(reps)]
            self.new_1rm = round(weight * ratio, 2)
        else:
            input("\n")
            self.new_1rm = self.one_rm

    def update_config(self) -> None:
        self.calculate_new_1rm()
        self.config["last_exercise"] = self.current_exercise
        self.config["last_cycle"] = self.current_cycle

        self.config["exercises"][self.current_exercise]["1RM"] = min(
            self.new_1rm, self.maximum)
        self.config["exercises"][self.current_exercise]["record"] = max(
            self.record, self.new_1rm)

        with open(self.data_path, "w") as f:
            json.dump(self.config, f, indent=4)
        p = subprocess.Popen(["energy", "-e", "trening", "25"])
        p.wait()

    def print_stats(self) -> None:
        self.exercises = self.config["exercises"]
        logging.debug(f"All: {self.exercises}")
        headers = []
        data = []
        _ = []
        for i in self.exercises:
            logging.debug(f"{i} - {self.exercises[i]}")
            headers.append(i.capitalize())
            if self.exercises[i]["1RM"] == self.exercises[i]["max"]:
                _.append(
                    f"{attr('bold')+fg(2)}{round(self.exercises[i]['1RM'])}{attr('reset')}")
            else:
                _.append(math.floor(self.exercises[i]["1RM"]))
        data.append(_)
        table = columnar(data, headers, min_column_width=10, justify="c")
        print(table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--stats", action="store_true",
                        help="display workout statistics")
    args = parser.parse_args()
    trening = Trening()
    if args.stats:
        trening.print_stats()
    else:
        trening.print_exercise()
        trening.update_config()
