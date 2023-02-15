#!/usr/bin/env python

import collections
import os
import sys
import statistics

predictions = {
        #'x':   [ A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W],

        'RN🎲': [12, 5,14,11,23, 7,15,10,21,20, 2, 4,16, 9, 6,22,18,19,17, 8,13, 3, 1],
        'IR🐙': [ 4,17,12,23, 1,10, 8,16, 9,15,11,22,18, 7,21,20, 2,13,19, 3,14, 6, 5],
        'AX🪅': [ 8,16,15, 7,14,21,12,17, 5, 6, 4,18, 2,22,20, 1, 9,10,19,11,13,23, 3],
        'KB🦁': [ 9, 8, 1,21,20,16, 2,17,11,10, 3,15, 4,19,23, 7, 6, 5,14,18,22,13,12],
        'EF🧇': [13,15,12, 9,20,10,11, 3,22,23,21,17, 7,16,19,18, 1, 5, 6, 4, 2, 8,14],
        'NT🐅': [23,20,19,15,12, 5,22,18,11,14,13, 7,16,21,17,10, 2, 8, 4, 9, 3, 1, 6],
        'EN🪬': [12,22,11,10,18, 9, 8,23,19, 7,13, 3,17, 4,14,16, 1,20, 2,21, 6, 5,15],
        'BF🥗': [17,23,22,18,16, 9,11, 5, 6,12, 3,19, 2,13, 8,10, 1,15, 7, 4,21,14,20],
        'PS🛸': [ 7, 3,14,15,20,21,23,10, 5,18, 8,17,11,12,16, 6, 1,19, 4,22,13, 9, 2],
        'NA🧿': [ 7, 8, 9,22,13,11, 3,12, 5,16,21,19,10, 1,20,18, 2, 4, 6,23,17,15,14],
        'TR🐉': [12,14, 4,17,15,11, 3,16, 9,22,10,13,19, 1,23,18, 5, 2, 7,21, 6,20, 8],
        'CJ🧲': [13,18,17, 3, 1,20, 6, 8,15,19,10, 4, 9, 2,23,11, 7, 5,22,16,14,21,12],
        'LL🐛': [ 3, 1, 2, 7,12, 4,22, 9,13,18,14, 5,16,10,23,19, 6, 8,21,17,15,11,20],
        'DJ💜': [17, 4, 5, 6,18, 1, 7,22,19,15, 9, 8,16,14,10,13,11, 3, 2,21,12,23,20],
        'JL🐡': [ 9,17, 7,21,18, 2,12,16,14, 4,15,10,19, 8, 6, 5,23,22,13,11, 3, 1,20],
        'MA🥃': [ 9, 1, 2, 6,18,15,23,19,13,20,12,17,10, 7,16,14, 3,11, 4, 5,22,21, 8],
        'AL🤫': [15,23, 7,22,16,12,10,18, 4, 6,17, 5, 9,14,19,11, 1,13,21, 3, 2,20, 8],
        'JJ💎': [15, 7,17, 3, 6,22,12, 8,10,20, 9,14, 5,16,18,19, 1, 2,11,13,21,23, 4],
        'HR🦎': [ 1,14,16,17,15, 3, 6,11,10,12, 2, 7, 9, 8, 4,13, 5,18,23,20,22,21,19],
        'SU🥇': [ 4, 2,18,10, 1,15,16, 7,12,23,11, 6, 5, 9,21,22, 3,14,20,17, 8,19,13],

        # 'MM': tbd
        }

# validate predictions
def validate_predictions():
    for contestant, ordering in predictions.items():
        count_by_number = collections.Counter(ordering)
        expected = collections.Counter(range(1,24))
        if count_by_number != expected:
            print("predictions are not 1-23 for ", contestant)
            sys.exit()

validate_predictions()


known_outcomes = {
        'A': 'm', # Survivor Player Loses 12 Challenges or Their Pants
        'B': 'm', # Germany Watches More Porn Than Italy
        'C': 'm', # Joe Rogan 20-Straight Womanless Episodes
        'D': 'm', # Kumquat or Insect in a Chopped Mystery Basket
        'E': 'y', # Grammy or Grampy Sings at the Grammys
        'F': 'm', # Elemental Name for Elemental "Production Baby"
        'G': 'm', # DudePerfect Trickshot: 30+ Meters or Seconds
        'H': 'm', # Late Politician Arrives on TIME (Magazine Cover)
        'I': 'm', # Game of the Year Title Contains # or . or ' or : or -
        'J': 'm', # Bob's "Burger of the Day" is a Song Title Pun
        'K': 'm', # Team Ruff Wins Puppy Bowl XIX
        'L': 'y', # Accidental Swim in Weekly Top r/holdmycosmo Vid
        'M': 'm', # Blue School Wins College Bowl
        'N': 'm', # Presenter/Performer/Nominee at Tonys is a Tony
        'O': 'm', # 69º at 4:20pm in Nice
        'P': 'm', # Wimbledon Woman Winner Wasn't Wed
        'Q': 'm', # Only Murders Outside the Building
        'R': 'm', # New Cat or Dog Macy's Thanksgiving Balloon
        'S': 'm', # ORAL is the Answer... in 10 NYT Crosswords
        'T': 'm', # Allstate's Mayhem Laughs at his Victim
        'U': 'm', # Florida is the Worst (in a Major League Sports Division)
        'V': 'm', # More People in Space Than This Game
        'W': 'm', # Winnie the Pooh Out-Murders Cocaine Bear
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

# Question 1b: how many points does each person currently have?

contestant_current_scores = {k:0 for k in predictions}
contestant_current_scores['tie'] = "n/a"
for contestant, point_allocations in predictions.items():
    score = 0
    for yes_no_maybe, points_allocated in zip(known_outcomes.values(),point_allocations):
        if yes_no_maybe == "y":
            score += points_allocated
    contestant_current_scores[contestant] = score

print("percent of win-paths per person")
for winner, p in ordered_winner_percentages:
    score = contestant_current_scores[winner]
    print(winner, ": ", '{:.1%}'.format(p),'({})'.format(score))

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
