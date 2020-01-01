#!/usr/bin/env python

predictions = {
        #'x': [ a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t],
        'am': [ 1,10, 9,15, 8, 5,17,11, 4, 7,12, 6,16,19,20,14,18, 3, 2,13],
        'jc': [ 7,20, 1,16,18,14,17,15,12, 4,11, 5, 3,13,10, 6,19, 9, 2, 8],
        'jj': [ 8,15,16, 2,14,11, 4, 5,18,13, 7,10, 3,19,17, 6,20,12, 3, 9],
        'su': [ 9,20, 6,19,15,10, 8,14,18, 4,11,12, 7,17, 2, 5, 1,16, 3,13],
        'ek': [10,18,17,12,11,13,15,19, 1, 1, 9, 8, 7,20,16, 5, 6, 4, 3, 2], # L twice...!
        'le': [18,19, 4, 7,20,12,13,11, 8,15, 6, 5, 3,16,17, 9,10, 1, 2,14],
        'cj': [10,15, 6,16,13,14,20,19,12,18,17,11, 5, 3, 4, 7, 9, 8, 1, 2],
        }

known_outcomes = {
        'a': 'm', # Arizona Turns Blue on Election Night
        'b': 'm', # Joey Chestnut Eats 71+ Hot Dogs on July 4th
        'c': 'm', # Pat Sajak Announces Retirement
        'd': 'm', # Loki Appears in the Avengers Video Game
        'e': 'm', # Japan Wins at Least 44 Medals at the Olympics
        'f': 'm', # Miss Universe is from the Western Hemisphere
        'g': 'm', # 7th Straight Year a Different Team Wins the World Series
        'h': 'm', # Joe Biden is not the Democratic Presidential Nominee
        'i': 'm', # Mulan FInishes the Year 8th Place or Worse
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
