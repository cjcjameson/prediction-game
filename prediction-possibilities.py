#!/usr/bin/env python

predictions = {
        'tr': [13,1,11,8,7,3,16,9,5,15,4,17,12,10,6,19,14,2,18],
        'ma': [14,13,10,11,15,12,2,9,8,1,7,17,16,5,4,3,18,6,19],
        'su': [19,12,8,15,14,6,9,4,2,7,11,17,16,10,3,1,13,5,18],
        'jj': [9,13,7,6,5,4,2,11,18,3,8,19,1,16,12,10,17,14,15],
        'ps': [15,2,8,9,18,3,17,4,6,7,10,13,12,14,5,11,16,1,19],
        'jc': [13,4,18,1,2,10,9,16,15,11,12,14,17,6,8,5,19,3,7],
        'cj': [6,8,7,16,17,13,1,2,14,3,4,18,9,10,5,19,15,12,11],
        'nt': [4,3,17,1,11,7,18,2,19,6,5,9,12,8,14,16,15,13,10],
        'le': [1,8,7,6,15,16,14,17,18,2,12,19,11,9,5,4,13,3,10],
        'dj': [19,1,13,7,6,15,18,4,2,17,8,14,16,11,3,9,10,12,5],
        'mm': [19,15,8,17,9,16,14,10,7,11,6,12,5,13,3,4,18,1,2],
        'am': [7,9,11,6,16,19,10,13,14,12,8,5,18,2,17,1,4,15,3],
        }

known_outcomes = [
        'm', #A
        'n', #B
        'y', #C
        'm', #D
        'm', #E
        'm', #F
        'm', #G
        'm', #H
        'n', #1
        'm', #J
        'n', #K
        'y', #L
        'm', #M
        'm', #N
        'm', #O
        'm', #P
        'm', #Q
        'n', #R
        'y', #S
        ]

# returns a dictionary of outcome sequences and winners
def winners(outcomes):
    if 'm' not in outcomes:
        points_per_prediction = {k: points(v, outcomes) for k, v in predictions.items()}
        max_points = max(points_per_prediction.values())
        winner = []
        for predictor, persons_points in points_per_prediction.items():
            if persons_points==max_points:
                winner.append(predictor)
        if len(winner)==1:
            return {''.join(outcomes): winner[0]}
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

each_win = winners(known_outcomes)

# total possible win paths per person
for w in each_win.values():
    winner_tally[w] += 1
ordered_winner_tally = sorted(winner_tally.items(), key=lambda x: x[1], reverse=True)
print("total possible win paths per person")
print(ordered_winner_tally)

# which events are most necessary for each person to win
# people have each event, and each event has a count of wins when it was true, and when it was false

each_question_empty_tf_buckets = {
        'a': {'t': 0, 'f': 0},
        'b': {'t': 0, 'f': 0},
        'c': {'t': 0, 'f': 0},
        'd': {'t': 0, 'f': 0},
        'e': {'t': 0, 'f': 0},
        'f': {'t': 0, 'f': 0},
        'g': {'t': 0, 'f': 0},
        'h': {'t': 0, 'f': 0},
        'i': {'t': 0, 'f': 0},
        'j': {'t': 0, 'f': 0},
        'k': {'t': 0, 'f': 0},
        'l': {'t': 0, 'f': 0},
        'm': {'t': 0, 'f': 0},
        'n': {'t': 0, 'f': 0},
        'o': {'t': 0, 'f': 0},
        'p': {'t': 0, 'f': 0},
        'q': {'t': 0, 'f': 0},
        'r': {'t': 0, 'f': 0},
        's': {'t': 0, 'f': 0},
        }

each_person_with_empty_question_buckets = {k: each_question_empty_tf_buckets for k in predictions}

import json
print(json.dumps(each_person_with_empty_question_buckets, indent=4))
