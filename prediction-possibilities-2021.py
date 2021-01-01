#!/usr/bin/env python

import collections
import os
import sys

predictions = {
        #'x': [ a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u],
        'le': [18,21, 4, 7,20,12,13,11, 8,15, 6, 5, 3,16,17, 9,10, 1, 2,14,19],
        'nt': [ 6, 8, 1,17,11,19, 4,16,18,10, 2, 3, 5,13,14, 9, 7,12,15,20,21],
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
        'a': 'm', # Arizona Turns Blue on Election Night
        'b': 'm', # Joey Chestnut Eats 71+ Hot Dogs on July 4th
        'c': 'm', # Pat Sajak Announces Retirement
        'd': 'm', # Loki Appears in the Avengers Video Game
        'e': 'm', # Japan Wins at Least 44 Medals at the Olympics
        'f': 'm', # Miss Universe is from the Western Hemisphere
        'g': 'm', # 7th Straight Year a Different Team Wins the World Series
        'h': 'm', # Joe Biden is not the Democratic Presidential Nominee
        'i': 'm', # Mulan Finishes the Year 8th Place or Worse
        'j': 'm', # Seattle NHL Name is Sockeyes, Emeralds, or Kraken
        'k': 'm', # Female-Named Atlantic Hurricane is Deadliest
        'l': 'm', # No One Beats American Ninja Warrior's Stage 3
        'm': 'm', # A Country's National Flag is Changed
        'n': 'm', # New 007 Saves Old 007's Life
        'o': 'm', # "Hentai" searched more than "Lesbian" on Pornhub
        'p': 'm', # Pixar Voice Actor is a Masked Singer
        'q': 'm', # Instagram's Instagram Passes 400 Million Followers
        'r': 'm', # BostonDynamics Robots Do a Group Dance
        's': 'm', # Cardi B or Billie Eilish DIES... in a music video
        't': 'm', # "Baby Yoda" Sneezes
	'u': 'm', # 2021! Work-In-Progress
}

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

# Question 1: how many total possible win paths per person?
total_possible = len(each_win)
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

question_ids=known_outcomes.keys()
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
