#!/usr/bin/env python

import collections
import os
import sys
import statistics

predictions = {
        #'x': [ a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u],
        'AA': [ 4,16,10,18, 5,21,12, 6,19,11,20,15, 3,17,14, 7,13, 1, 9, 2, 8],
        'NT': [ 8, 9, 6,14, 7,17,19, 1,15,12,11,16, 2,21, 4,10,18, 5,20,13, 3],
        'MA': [19, 1, 5, 2, 4,17,21,15,14,13,20,16,11, 6, 8, 3, 9,10, 7,18,12],
        'PJ': [20,21,11, 4,15,18,19, 9,17,13, 5,16,12, 8, 2, 3, 6,10,14, 1, 7],
        'JL': [21,11, 1,10, 4,13, 2,15,19,17, 3,16, 8, 5, 6, 9,12,14, 7,20,18],
        'NA': [19,18,12,11,10, 8, 1,16,17, 7, 4,14, 6,13, 5,20,15, 9, 2, 3,21],
        'EK': [14,20, 7,12, 1,15,21,17,16,13,11, 6,10, 5, 8, 2,19,18, 4, 3, 9],
        'SU': [13,14, 5, 2,11,15,12,19,18,17, 7,16, 9,20, 1,10, 3, 6, 8,21, 4],
        'BF': [14,20,19, 4, 1, 5, 6,13,17,18, 2, 7, 8,16,12,11,21,10, 9,15, 3],
        'LE': [14, 2,12, 1,11, 5,21,15,16,20,10,13,17,18, 3, 7, 6, 8, 9, 4,19],
        'PG': [20,21,10,11,12, 5, 9,13,16,18, 8,14, 3,15,19,17, 4, 1, 2, 6, 7],
        'DJ': [21, 2, 1, 7,15,17, 8,16, 6,14,20,13, 5,10,11,19, 9,12, 4, 3,18],
        'TR': [20,16,17, 5,13,21, 2,19,15,14,12, 7, 1, 8,10,18, 6, 4, 3, 9,11],
        'JC': [10,11, 9, 3, 2,20,16,12,13,17,19,15, 8, 6,14,18, 7, 4, 1,21, 5],
        'CJ': [13,16, 1,10, 8,19,11, 2,17, 6,20, 5,15,14, 9,18, 7,12, 4,21, 3],
        'HR': [17,20, 9, 8, 4, 5, 3,15,10,11,21,16, 6, 1, 7, 2,14,18,19,12,13],
        'AL': [19, 4, 3, 2, 8, 7,15,20,13, 6, 5,17, 9,16,10,11,12,18, 1,14,21],
        'JJ': [20,17, 1, 5,11,10,13,18,16,14, 7, 8,15,21, 2,19, 4, 9, 6,12, 3],
        # 'MM': [21,19, 3, 1, 4,17,13,18,20,16,11,15, 6,14, 5,10, 9, 7, 2,12, 8],
        }

# validate predictions
def validate_predictions():
    for contestant, ordering in predictions.items():
        count_by_number = collections.Counter(ordering)
        expected = collections.Counter(range(1,22))
        if count_by_number != expected:
            print("predictions are not 1-21 for ", contestant)
            sys.exit()

validate_predictions()


known_outcomes = {
        'a': 'y', # Democrats gain one or both Senate seats (GA January)
        'b': 'm', # Winds of Winder STILL unpublished
        'c': 'm', # NHL Kings win more than NBA Kings
        'd': 'y', # "Dugong" is a Jeopardy! answer or clue
        'e': 'm', # Trump is detained, flees country, or dies
        'f': 'n', # Smash Bros. character in Olympic Ceremony
        'g': 'n', # New 007 saves old 007's life
        'h': 'y', # "Lil" Artist has a Top 10 Billboard hit
        'i': 'y', # Miss Universe isn't from Africa or Europe
        'j': 'n', # LeBron is Tune Squad all-time point leader
        'k': 'y', # < 2000 daily global COVID-19 deaths
        'l': 'y', # OnlyFans joke on Last Week Tonight
        'm': 'm', # 2 different Battlebots champions
        'n': 'm', # Americone Dream outsells Chunky Monkey
        'o': 'm', # LiMu emu pecks someone
        'p': 'y', # Axis Powers countries win 111+ medals
        'q': 'y', # Someone loses a limb... in an SNL Sketch
        'r': 'y', # Ninja Warrior's stage 3 beaten
        's': 'n', # Sexiest Man Alive is a repeat winner
        't': 'y', # NASA reaches (Bruno) Mars ('s Twitter following)
        'u': 'm', # Google Doodle of poodles or noodles
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
