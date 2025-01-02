#!/usr/bin/env python

import collections
import os
import sys
import statistics
import multiprocessing as mp
from functools import partial

# fmt: off
predictions = {
        #'x':           [ A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y],

        'SOPH🦈':         [ 5,18,24, 7, 2,23,21,16, 9,20, 3,14, 1,22, 4,19, 6,17, 8,25,10,15,11,13,12],
        'ALIZ🦎':         [20,21,22,23,17,24, 2,18, 1, 8, 6, 5,25,16,12,13, 7,15, 4,14,11,10, 3,19, 9],
        'HETH🍣':         [24,22,20,16, 7,25, 2,19, 6,13,15, 8,23,18,21, 5, 3,10,11,17,14, 1, 4, 9,12],
        'MATT🍁':         [19,21, 6,18, 5,23,24, 7,25, 8, 2, 9,22,12,17,15,20,16,14,10, 3, 1,13,11, 4],
        'DICE🎲':         [ 9,25, 4,24,19,10, 5,14,17,22, 6,11,21,15, 7, 1,23,12,18, 2, 8,20,16, 3,13],
        'ALEX👽':         [18,25,22,24,16,13,19, 9,11, 4, 3, 8, 6,20, 1, 7,12,15,14,10,23, 5,17, 2,21],
        'WINZ🪅':         [24,16,14,10, 1,19, 2,12,22,11,21, 5,25,13,20, 3, 8,23, 9,17,15, 6, 7,18, 4],
        'STEN🍸':         [23, 8,17,11,25, 4, 2, 3,15,13,22, 9,20, 5,21,14, 6,19,12,18,24, 1, 7,16,10],
        'PETE🛸':         [25,18,17, 2,24, 7,23, 8,22,13,19,16,15,12,11,14,10, 6, 5, 9,21, 1, 3,20, 4],
        'CJCJ🌚':         [ 3,17,20,23, 2, 6, 5,13,25,24, 1, 8,21,11,19,15,12,18,16,22,10, 4,14, 9, 7],
        'NICK👺':         [24,20, 6,12,11,23,10,14, 2,21, 3,22, 7,15, 4,25,16, 9, 8,17,19,13, 5,18, 1],
        'IVYY🦄':         [23,22,15, 6,13,24, 1,11,21,25, 7, 5,19,12, 4,16, 8,10, 3, 9,14, 2,18,20,17],
        'RACH🎭':         [22,21,20, 3, 2, 9, 1, 4,25,13,17,18,19,12,24,23, 5,16, 6,10, 7, 8,15,11,14],
        'LIND🍄':         [23, 7,18,15,11,25,12,21,24,22, 4,10, 5,20,19, 3, 8,14, 1, 6, 9,17, 2,16,13],
        'ELEN🪆':         [25,22,15,17, 8,14, 9,13, 7,20, 3, 4,18,12,24, 6,19,16,10,11,23, 2, 1,21, 5],
        'ALSH🛼':         [21,23,12,13,11,14, 9,10, 3, 7,19,18,15,16, 1,22, 6,20, 2, 4,17,24, 5, 8,25],
        'ZYLA🦓':         [ 6,15, 3, 9,19,18,20,17, 7, 4,12,14,10, 1,23,21,16, 5, 8,24, 2,25,13,11,22],
        'MIKE🥃':         [25, 3,22, 7,24,21,20, 9,19,13,12, 2,16,10,23, 4,18, 8, 5,14, 6,15, 1,17,11],
        'YAIR👨‍🍳':         [25,24,17, 7, 3,16, 1, 6,21,10,18, 4,22,11,23,15, 8,20, 2, 9,13,12,19,14, 5],

        # 'WISDOMOFCROWDS':         [25,24,20,12,9,22,5,10,19,16,3,6,23,13,21,15,7,18,1,11,14,4,2,17,8],
        }
# fmt: on


# validate predictions
def validate_predictions():
    for contestant, ordering in predictions.items():
        count_by_number = collections.Counter(ordering)
        expected = collections.Counter(range(1, 26))
        if count_by_number != expected:
            print("predictions are not 1-25 for ", contestant)
            sys.exit()


validate_predictions()


known_outcomes = {
    "A": "m",  # Bluesky on Bluesky past 20 million
    "B": "m",  # Super Bowl Ads: 2 licks
    "C": "m",  # Mammal wins comedy wildlife photo awards
    "D": "m",  # 50 castmembers in SNL50 special
    "E": "m",  # Ruble in Truuuble
    "F": "m",  # Good News said 4x on Futurama
    "G": "m",  # Change in 25 tallest skyscrapers
    "H": "m",  # Bitch wins national dog show
    "I": "m",  # 1234 career WNBA points for Caitlin Clark
    "J": "m",  # GTA6 sex
    "K": "m",  # 3 bodily fluids on Hot Ones
    "L": "m",  # Tuba or Harp on Tiny Desk
    "M": "m",  # Smurf said 99 times
    "N": "m",  # Odd # wins Beast Games
    "O": "m",  # Yodel Guy falls to death on Price is Right
    "P": "m",  # Luigi + Diddy released
    "Q": "m",  # Foods out-race balls in TreadmillGuy
    "R": "m",  # K-Pop Slots Top 8 Pop Spot
    "S": "m",  # Bogey Bogey Bogey Bogey Bogey Bogey
    "T": "m",  # 3 Tetris Shapes on The Floor
    "U": "m",  # Sexiest Man has died
    "V": "m",  # Senate Age down a Zendaya
    "W": "m",  # Hurricane Karen
    "X": "m",  # Zootopia celebrating predators
    "Y": "m",  # 99 silhouettes
}

question_ids = known_outcomes.keys()


# returns a dictionary of outcome sequences and winners
def winners_optimized(outcomes, start, end):
    results = {}
    for i in range(start, end):
        binary = format(i, f"0{len(outcomes)}b")
        current_outcome = "".join("y" if b == "1" else "n" for b in binary)

        points_per_prediction = {
            k: points(v, current_outcome) for k, v in predictions.items()
        }
        max_points = max(points_per_prediction.values())
        possible_winners = [
            predictor
            for predictor, points in points_per_prediction.items()
            if points == max_points
        ]

        winner = possible_winners[0] if len(possible_winners) == 1 else "tie"
        results[current_outcome] = winner

    return results


def parallel_winners(outcomes):
    num_cores = mp.cpu_count()
    total_combinations = 2 ** len(outcomes)
    chunk_size = total_combinations // num_cores

    with mp.Pool(num_cores) as pool:
        partial_winners = partial(winners_optimized, outcomes)
        ranges = [
            (i * chunk_size, min((i + 1) * chunk_size, total_combinations))
            for i in range(num_cores)
        ]
        results = pool.starmap(partial_winners, ranges)

    return {k: v for result in results for k, v in result.items()}


def points(rankings, outcomes):
    total = 0
    for ranking, outcome in zip(rankings, outcomes):
        if outcome == "y":
            total += ranking
    return total


winner_tally = {k: 0 for k in predictions}
winner_tally["tie"] = 0

if __name__ == "__main__":
    each_win = parallel_winners(list(known_outcomes.values()))
    total_possible = len(each_win)

    # Question 1: how many total possible win paths per person?
    for w in each_win.values():
        winner_tally[w] += 1
    percentage_wins = winner_tally.copy()
    for winner, tally in percentage_wins.items():
        percentage_wins[winner] = float(tally) / float(total_possible)
    ordered_winner_percentages = sorted(
        percentage_wins.items(), key=lambda x: x[1], reverse=True
    )

    # Question 1b: how many points does each person currently have?

    contestant_current_scores = {k: 0 for k in predictions}
    contestant_current_scores["tie"] = "n/a"
    for contestant, point_allocations in predictions.items():
        score = 0
        for yes_no_maybe, points_allocated in zip(
            known_outcomes.values(), point_allocations
        ):
            if yes_no_maybe == "y":
                score += points_allocated
        contestant_current_scores[contestant] = score

    print("percent of win-paths per person (score so far in parentheses)")
    for winner, p in ordered_winner_percentages:
        score = contestant_current_scores[winner]
        print(winner, ": ", "{:.1%}".format(p), "({})".format(score))

    # Question 2: which events are most necessary for each person to win?

    def new_empty_yn_bucket():
        return {"y": 0, "n": 0}

    def new_each_question_empty_yn_buckets():
        return {k: new_empty_yn_bucket() for k in question_ids}

    # people have each event, and each event has a count of wins when it was true, and when it was false
    each_person_with_question_buckets = {
        k[0]: new_each_question_empty_yn_buckets() for k in ordered_winner_percentages
    }

    for events, winner in each_win.items():
        for idx, question_id in enumerate(question_ids):
            event_outcome = events[idx]
            each_person_with_question_buckets[winner][question_id][event_outcome] += 1

    import copy

    only_people_with_win_paths = copy.deepcopy(each_person_with_question_buckets)
    for person, questions in each_person_with_question_buckets.items():
        if winner_tally[person] == 0:
            del only_people_with_win_paths[person]

    each_person_only_maybe_questions = copy.deepcopy(only_people_with_win_paths)
    for person, questions in only_people_with_win_paths.items():
        for question in questions:
            if known_outcomes[question] != "m":
                del each_person_only_maybe_questions[person][question]

    each_person_question_percentage = copy.deepcopy(each_person_only_maybe_questions)
    for person, questions in each_person_only_maybe_questions.items():
        for question in questions:
            raw_percentage = questions[question]["y"] / (
                questions[question]["y"] + questions[question]["n"]
            )
            each_person_question_percentage[person][question] = raw_percentage

    for person, questions in each_person_question_percentage.items():
        print(
            "Contestant "
            + person
            + " has "
            + str(winner_tally[person])
            + " ways to win, and needs the following to happen (high percentages) or not (low percentages)"
        )

        ordered_qs_by_need_percent = sorted(
            questions.items(), key=lambda x: x[1], reverse=True
        )

        if os.environ.get("FULL_GUTS"):
            print(questions)

            # unpack the tuple
        print("\t{}: {:.1%}".format(*ordered_qs_by_need_percent[0]))
        print("\t{}: {:.1%}".format(*ordered_qs_by_need_percent[-1]))

    # Question 3: for each maybe-question, what happens?
    print("Question 3: for each maybe-question, what happens?")

    maybe_question_need_by_person = {}

    for question, outcome in known_outcomes.items():
        if outcome == "m":
            maybe_question_need_by_person[question] = {}

    for person, questions in each_person_question_percentage.items():
        for question, percentage in questions.items():
            maybe_question_need_by_person[question][person] = percentage

    for question, person_percentages in maybe_question_need_by_person.items():
        print(
            "Question "
            + question
            + " coming TRUE will help (high percentages) or hurt (low percentages) these people"
        )

        ordered_people_by_need_percent = sorted(
            person_percentages.items(), key=lambda x: x[1], reverse=True
        )

        for person_need_percent in ordered_people_by_need_percent:
            print("\t{}: {:.1%}".format(*person_need_percent))

    # Question 4: who wins, organized by how many "yes" outcomes
    print("Question 4: who wins, organized by how many more 'yes' outcomes")

    maybes_count = sum(1 for outcome in known_outcomes.values() if outcome == "m")
    yesses_already_count = sum(
        1 for outcome in known_outcomes.values() if outcome == "y"
    )

    # def new_tally_by_guesser():
    #    return {"tie": 0}

    how_many_more_yes_buckets = {k: {} for k in range(maybes_count + 1)}

    for outcome, winner in each_win.items():
        how_many_more_yes = outcome.count("y") - yesses_already_count
        if not winner in how_many_more_yes_buckets[how_many_more_yes]:
            how_many_more_yes_buckets[how_many_more_yes][winner] = 1
        else:
            how_many_more_yes_buckets[how_many_more_yes][winner] += 1

    for how_many_more_yes_bucket, person_counts in how_many_more_yes_buckets.items():
        print(
            "If there are "
            + str(how_many_more_yes_bucket)
            + " more yesses, then these people have win-paths:"
        )

        ordered_people_by_count = sorted(
            person_counts.items(), key=lambda x: x[1], reverse=True
        )

        for person_count in ordered_people_by_count:
            print("\t{}: {}".format(*person_count))

    # do people have more win-paths because they're just guessing differently than the wisdom of the crowds?
    # Or does someone have reasonable guesses, and also a clear opportunity?
    def mean_difference_analysis():

        questions_values = {}

        for index, question in enumerate(question_ids):
            this_question_values = []
            for prediction_list in predictions.values():
                this_question_values.append(prediction_list[index])

            questions_values[question] = this_question_values

        questions_means = {
            q: statistics.mean(values) for (q, values) in questions_values.items()
        }
        questions_means_sorted = dict(
            sorted(questions_means.items(), key=lambda item: item[1], reverse=True)
        )
        questions_means_sorted_rounded = {
            q: round(mean, 1) for (q, mean) in questions_means_sorted.items()
        }
        print()
        print("mean question ranking")
        print(questions_means_sorted_rounded)

        questions_medians = {
            q: statistics.median(values) for (q, values) in questions_values.items()
        }
        questions_medians_sorted = dict(
            sorted(questions_medians.items(), key=lambda item: item[1], reverse=True)
        )
        print()
        print("median question ranking")
        print(questions_medians_sorted)

        # what would the mean prediction order be? mostly driven by the mean, with some influence from median
        mm_prediction = predictions.get("MM")

        if mm_prediction is None:
            print("skipping mean error analysis")
            return

        mean_absolute_error_by_person = {}
        for person, prediction in predictions.items():
            absolute_errors = []
            for p1, p2 in zip(prediction, mm_prediction):
                absolute_errors.append(abs(p1 - p2))
            mean_absolute_error_by_person[person] = round(
                statistics.mean(absolute_errors), 2
            )

        mae_sorted = dict(
            sorted(
                mean_absolute_error_by_person.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )
        print()
        print("mean absolute error from the collective mean prediction")
        print(mae_sorted)

    mean_difference_analysis()
