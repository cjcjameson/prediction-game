#!/usr/bin/env python

import collections
import os
import sys
import statistics

predictions = {
        #'x':          [ a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v],
        'JP😻':        [ 2,11, 5,17,13,21,18,22,12, 4,14,15, 9, 1, 6, 8,20,16,10,19, 3, 7],
        'JN⛵':        [11,15, 2,22,10,14, 3,21, 1, 9, 8,20, 5,12,19,18,13,17, 6,16, 7, 4],
        'PS☠️':         [ 5,10,18, 4, 6, 7,11,20,19, 2,22,16, 1,17,12, 8, 9,14, 3,21,13,15],
        'LL🦔':        [ 5,15,19,17,16,20, 7,18,13, 4,22, 9, 3,11,14, 8, 6,21, 1,10, 2,12],
        'JC🤷🏾‍♀️': [ 1, 5, 9,10,17,16, 4,22, 2,12,13,20,11,14,15,18,19, 8, 6,21, 7, 3],
        'MA🥃':        [ 7,16,17,22,20, 8, 5,21,12,14,19, 6,10, 1,11,18,13,15, 3, 9, 4, 2],
        'TR🐉':        [17, 1, 2,16, 3, 4,15, 5, 6, 7, 8,22, 9,10,18,11,19,12,13,20,21,14],
        'EK💩':        [ 5, 8,22, 7, 4,20,14,18,16, 3,12,10, 1,13,15, 9,21,19,17, 6,11, 2],
        'BF🍕':        [ 9,18,11,19,17,16, 8, 5, 1, 2,13, 6, 3,20,14,15, 7,21,22,12, 4,10],
        'SU🍸':        [16, 6,15,12,22, 9,10,20, 8, 3,21, 5,13, 7,17,18,19,14, 2,11, 4, 1],
        'DJ💜':        [21,16, 4,22,19, 2,20,15, 5, 6,13,12, 8, 9,17,14,10,18, 1, 3, 7,11],
        'CJ😎':        [ 6,18, 4, 8,20,14,10,16,12,15,22,13,21, 1,19, 7, 3,17, 5,11, 2, 9],
        'JJ🥌':        [ 6, 8,16,11,20,18,10,12, 4,21,14, 5,22,13,17,19, 7, 1, 2, 9,15, 3],
        'HR🦎':        [17,20,18, 1,19,22, 2, 8,21, 6, 7,14,15,16, 4,13, 5,12, 9, 3,11,10],
        'JL🐡':        [21,11, 3,15,12,18, 5,19,17, 7,22,13, 4, 8,20,16, 6,14, 2, 9, 1,10],
        'NA🧙🏽‍♂️': [11,15,19,20, 6,14,12,13, 8, 9,16, 1,17,21,22, 4, 3,18, 5, 7,10, 2],
        # 'MM':          [ 5,14,13,18,20,16, 7,22, 8, 2,17,12, 6,11,21,15, 9,19, 1,10, 3, 4],
        }

# validate predictions
def validate_predictions():
    for contestant, ordering in predictions.items():
        count_by_number = collections.Counter(ordering)
        expected = collections.Counter(range(1,23))
        if count_by_number != expected:
            print("predictions are not 1-22 for ", contestant)
            sys.exit()

validate_predictions()


known_outcomes = {
        'a': 'm', # Zero Instruments on Rolling Stone Covers
        'b': 'n', # A Big Brother Wins Big Brother
        'c': 'n', # Knuckles Punches Tails
        'd': 'y', # Multiple Women Win Nobel Prizes
        'e': 'y', # Word fo the Day Worth 22+ Scrabble Points
        'f': 'm', # 40 Wins for NFL Birds
        'g': 'm', # Kumquats in a Chopped Mystery Basket
        'h': 'y', # All 6 "Squad" Members Re-Elected
        'i': 'm', # LiMu Emu Pecks Someone or a Soccer Ball
        'j': 'y', # 6 Curling Stone Hits in a Single Throw
        'k': 'y', # NASA's "DART" Gets a "Bullseye"
        'l': 'n', # Game of the Year Title Contains a number
        'm': 'y', # Figure Skater Rotates 9000 degrees
        'n': 'n', # Mid-Air Death in Both Tom Cruise Sequels
        'o': 'y', # Symmetrical Flag Country Wins Eurovision
        'p': 'y', # Doja Cat Raps About Her... "Other" Cat
        'q': 'y', # Met Gala Outfit has a Giant Flower
        'r': 'm', # Homer Does a Dozen D'Oh!s
        's': 'm', # Ball Nails Goalie  in the Face at World Cup
        't': 'n', # A Bitch Wins the National Dog Show
        'u': 'y', # Hole-in-1 on "Hole" Hole on Holey Moley
        'v': 'm', # Zach King Loses a Child... in a Magic Video
}

question_ids=known_outcomes.keys()


# returns a dictionary of outcome sequences and winners
def winners(outcomes):
    if 'm' not in outcomes:
        points_per_prediction = {k: points(v, outcomes) for k, v in predictions.items()}
        max_points = max(points_per_prediction.values())
        possible_winners = []
        for predictor, persons_points in points_per_prediction.items():
            if persons_points==max_points:
                possible_winners.append(predictor)
        if len(possible_winners)==1:
            return {''.join(outcomes): possible_winners[0]}
        else:
            return {''.join(outcomes): 'tie'}
    else:
        first_maybe = outcomes.index('m')
        its_a_yes = list(outcomes)
        its_a_yes[first_maybe]='y'
        yes_outcomes = winners(its_a_yes)

        its_a_no = list(outcomes)
        its_a_no[first_maybe]='n'
        no_outcomes = winners(its_a_no)

        return {**yes_outcomes, **no_outcomes}

def points(rankings, outcomes):
    total = 0
    for ranking, outcome in zip(rankings, outcomes):
        if outcome == 'y':
            total += ranking
    return total

winner_tally = {k:0 for k in predictions}
winner_tally['tie']=0

each_win = winners(list(known_outcomes.values()))
total_possible = len(each_win)

# Question 1: how many total possible win paths per person?
for w in each_win.values():
    winner_tally[w] += 1
percentage_wins = winner_tally.copy()
for winner, tally in percentage_wins.items():
    percentage_wins[winner] = float(tally)/float(total_possible)
ordered_winner_percentages = sorted(percentage_wins.items(), key=lambda x: x[1], reverse=True)

print("percent of win-paths per person")
for winner, p in ordered_winner_percentages:
    print(winner, ": ", '{:.1%}'.format(p))

# Question 2: which events are most necessary for each person to win?

def new_empty_yn_bucket():
    return {'y': 0, 'n': 0}
def new_each_question_empty_yn_buckets():
    return {k: new_empty_yn_bucket() for k in question_ids}
# people have each event, and each event has a count of wins when it was true, and when it was false
each_person_with_question_buckets = {k[0]: new_each_question_empty_yn_buckets() for k in ordered_winner_percentages}

for events, winner in each_win.items():
    for idx, question_id in enumerate(question_ids):
        event_outcome = events[idx]
        each_person_with_question_buckets[winner][question_id][event_outcome]+=1

import copy
only_people_with_win_paths = copy.deepcopy(each_person_with_question_buckets)
for person, questions in each_person_with_question_buckets.items():
    if winner_tally[person] == 0:
        del only_people_with_win_paths[person]

each_person_only_maybe_questions = copy.deepcopy(only_people_with_win_paths)
for person, questions in only_people_with_win_paths.items():
    for question in questions:
        if known_outcomes[question] != 'm':
            del each_person_only_maybe_questions[person][question]

each_person_question_percentage = copy.deepcopy(each_person_only_maybe_questions)
for person, questions in each_person_only_maybe_questions.items():
    for question in questions:
        raw_percentage = questions[question]['y'] / (questions[question]['y'] + questions[question]['n'])
        each_person_question_percentage[person][question] = raw_percentage

for person, questions in each_person_question_percentage.items():
    print("Contestant " + person + " has " + str(winner_tally[person]) + " ways to win, and needs the following to happen (high percentages) or not (low percentages)")

    ordered_qs_by_need_percent = sorted(questions.items(), key=lambda x: x[1], reverse=True)

    if os.environ.get('FULL_GUTS'):
        print(questions)

                                # unpack the tuple
    print('\t{}: {:.1%}'.format(*ordered_qs_by_need_percent[0]))
    print('\t{}: {:.1%}'.format(*ordered_qs_by_need_percent[-1]))

# Question 3: for each maybe-question, what happens?
print("Question 3: for each maybe-question, what happens?")

maybe_question_need_by_person = {}

for question, outcome in known_outcomes.items():
    if outcome == 'm':
        maybe_question_need_by_person[question] = {}

for person, questions in each_person_question_percentage.items():
    for question, percentage in questions.items():
        maybe_question_need_by_person[question][person] = percentage

for question, person_percentages in maybe_question_need_by_person.items():
    print("Question " + question + " coming TRUE will help (high percentages) or hurt (low percentages) these people")

    ordered_people_by_need_percent = sorted(person_percentages.items(), key=lambda x: x[1], reverse=True)

    for person_need_percent in ordered_people_by_need_percent:
        print('\t{}: {:.1%}'.format(*person_need_percent))

# Question 4: who wins, organized by how many "yes" outcomes
print("Question 4: who wins, organized by how many more 'yes' outcomes")

maybes_count = sum(1 for outcome in known_outcomes.values() if outcome == "m")
yesses_already_count = sum(1 for outcome in known_outcomes.values() if outcome == "y")

# def new_tally_by_guesser():
#    return {"tie": 0}

how_many_more_yes_buckets = {k:{} for k in range(maybes_count+1)}

for outcome, winner in each_win.items():
    how_many_more_yes = outcome.count("y") - yesses_already_count
    if not winner in how_many_more_yes_buckets[how_many_more_yes]:
        how_many_more_yes_buckets[how_many_more_yes][winner] = 1
    else:
        how_many_more_yes_buckets[how_many_more_yes][winner] += 1

for how_many_more_yes_bucket, person_counts in how_many_more_yes_buckets.items():
    print("If there are " + str(how_many_more_yes_bucket) + " more yesses, then these people have win-paths:")

    ordered_people_by_count = sorted(person_counts.items(), key=lambda x: x[1], reverse=True)

    for person_count in ordered_people_by_count:
        print('\t{}: {}'.format(*person_count))


# do people have more win-paths because they're just guessing differently than the wisdom of the crowds?
# Or does someone have reasonable guesses, and also a clear opportunity?
def mean_difference_analysis():

    questions_values = {}

    for index, question in enumerate(question_ids):
        this_question_values = []
        for prediction_list in predictions.values():
            this_question_values.append(prediction_list[index])

        questions_values[question] = this_question_values

    questions_means = {q:statistics.mean(values) for (q,values) in questions_values.items()}
    questions_means_sorted = dict(sorted(questions_means.items(), key=lambda item: item[1], reverse=True))
    questions_means_sorted_rounded = {q:round(mean,1) for (q,mean) in questions_means_sorted.items()}
    print()
    print("mean question ranking")
    print(questions_means_sorted_rounded)

    questions_medians = {q:statistics.median(values) for (q,values) in questions_values.items()}
    questions_medians_sorted = dict(sorted(questions_medians.items(), key=lambda item: item[1], reverse=True))
    print()
    print("median question ranking")
    print(questions_medians_sorted)

    # what would the mean prediction order be? mostly driven by the mean, with some influence from median
    mm_prediction = [21,19, 3, 1, 4,17,13,18,20,16,11,15, 6,14, 5,10, 9, 7, 2,12, 8]

    mean_absolute_error_by_person = {}
    for person, prediction in predictions.items():
        absolute_errors = []
        for p1, p2 in zip(prediction, mm_prediction):
            absolute_errors.append(abs(p1-p2))
        mean_absolute_error_by_person[person] = round(statistics.mean(absolute_errors),2)

    mae_sorted = dict(sorted(mean_absolute_error_by_person.items(), key=lambda item: item[1], reverse=True))
    print()
    print("mean absolute error from the collective mean prediction")
    print(mae_sorted)

mean_difference_analysis()
