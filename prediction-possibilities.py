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

known_outcomes = {
        'a': 'm', # New Supreme Court vacancy
        'b': 'n', # Only solo artists achieve Billboard #1s
        'c': 'y', # Daenerys Targaryen dies
        'd': 'y', # 3+ women debating at the 1st Democratic Presidential debate
        'e': 'm', # Aladdin finishes the year 7th place or worse
        'f': 'm', # Seattle's NHL Team is named and it's not an animal
        'g': 'm', # Donald Trump is no longer President
        'h': 'n', # Buzz Lightyear gets married
        'i': 'n', # King Kong is nominated for Best Musical and loses
        'j': 'm', # Mel Brooks dies
        'k': 'n', # A cat or dog team wins the March Madness Tournament
        'l': 'y', # 4+ of the original 6 Avengers survive Endgame
        'm': 'm', # 1-day stock plummet record for a single company is broken
        'n': 'm', # Tom Brady is not the Patriots starting QB at the end of 2019
        'o': 'm', # Pennywise the Clown is a playable character in Mortal Kombat 11
        'p': 'm', # 5+ self-driving car fatalities
        'q': 'm', # Miley Cyrus confirms pregnancy
        'r': 'n', # Episode 9 will be the 1st Star Wars subtitle only 1 or 2 words long
        's': 'y', # The UK is still part of the EU on March 30th
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
for w in each_win.values():
    winner_tally[w] += 1
ordered_winner_tally = sorted(winner_tally.items(), key=lambda x: x[1], reverse=True)
print("total possible win paths per person")
print(ordered_winner_tally)

# Question 2: which events are most necessary for each person to win?

question_ids=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's']
def new_empty_yn_bucket():
    return {'y': 0, 'n': 0}
def new_each_question_empty_yn_buckets():
    return {k: new_empty_yn_bucket() for k in question_ids}
# people have each event, and each event has a count of wins when it was true, and when it was false
each_person_with_question_buckets = {k[0]: new_each_question_empty_yn_buckets() for k in ordered_winner_tally}

for events, winner in each_win.items():
    for idx, question_id in enumerate(question_ids):
        event_outcome = events[idx]
        each_person_with_question_buckets[winner][question_id][event_outcome]+=1

import copy
only_people_with_win_paths = copy.deepcopy(each_person_with_question_buckets)
for person, questions in each_person_with_question_buckets.items():
    if winner_tally[person] is 0:
        del only_people_with_win_paths[person]

each_person_only_maybe_questions = copy.deepcopy(only_people_with_win_paths)
for person, questions in only_people_with_win_paths.items():
    for question in questions:
        if known_outcomes[question] is not 'm':
            del each_person_only_maybe_questions[person][question]

each_person_question_percentage = copy.deepcopy(each_person_only_maybe_questions)
for person, questions in each_person_only_maybe_questions.items():
    for question in questions:
        raw_percentage = questions[question]['y'] / (questions[question]['y'] + questions[question]['n'])
        each_person_question_percentage[person][question] = '{:.1%}'.format(raw_percentage)

for person, questions in each_person_question_percentage.items():
    print("Contestant " + person + " has " + str(winner_tally[person]) + " ways to win, and needs the following to happen (high percentages) or not (low percentages)")
    print(questions)
