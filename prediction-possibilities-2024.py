#!/usr/bin/env python

import collections
import os
import sys
import statistics

predictions = {
        #'x':           [ A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X],

        'ZJ👶':         [14,16,13, 5, 7, 3,19,17, 9, 1,12,23,21,18,11, 6, 4,22, 8, 2,24,20,15,10],
        'DI🎲':         [ 2, 8,18,17,19,16, 6, 3,11,13, 9,22,20,15, 4, 7,23, 1,24,12,10,21, 5,14],
        'YL👨‍🍳': [12,22, 2, 3,21,23,20, 6, 5,10, 4, 8,17,16, 7,13,18,14,11, 9,19,24, 1,15],
        'RW🎭':         [ 7,20, 6, 5,17,23, 2,21,19,11, 3,12, 1,16, 8, 4,24, 9,22,18,10,15,14,13],
        'BF🧞‍♀️':  [24,22,23, 9, 3,17,10,16, 2,19,18,11,13, 1, 4, 5,21, 8,14,15, 6,12,20, 7],
        'AX💃':         [23,15, 9,14,16, 5, 3,10,17,24, 6, 7, 8, 4,11, 2,20, 1,18,13,21,22,19,12],
        'LL⛈':         [ 5,24, 6,20,16,21,13, 1, 9, 8, 4,10,23,22,15,18,14, 2,12,11, 3,17, 7,19],
        'NA👺':         [13,18,20,19, 2,21,22,23,14,17,16, 5,12,15, 4, 8, 7, 9, 6, 3,11,24,10, 1],
        'IV🦄':         [ 6,18,16,20,13,24,19,15, 9,14, 5, 7,21,12,10,22,17, 1, 8, 2, 4,23,11, 3],
        'MA🥃':         [19,14, 9, 5,18,23,10,15, 8,12,24,16, 7,17,13, 4,22, 3, 2,21,20, 6,11, 1],
        'TR🐉':         [ 3, 2,10,18, 7,20,23,15,13, 6,22,17,21, 9,19,14, 8, 1,16,24,11, 4,12, 5],
        'EN🪬':         [ 8,23,17, 6,11,18, 5,12,14,13, 9, 3, 2,10,16, 4,24, 1,15,21,22,20, 7,19],
        'CJ🧲':         [16,20,22,17,10,24,13, 3, 5, 6,21, 7,18,11,12,19,15, 4, 2, 1, 9,23,14, 8],
        'SU🪨':         [13, 6,24,11,17,12,14,21, 2, 8,18,22,16,23, 9, 4, 3, 5, 1,15,10,19,20, 7],
        'AL🛼':         [ 2,12,15,14,17,13,19,11,21,10, 1,22, 3,20,18,23, 9, 4, 8,16, 5, 6, 7,24],
        'PS🛸':         [ 5,23,21,22, 6,24, 4,20,11,10, 9,18,19,17, 8, 2, 7,15, 1,14,16,13,12, 3],
        'AJ🪅':         [ 9,17,18,21, 4,20,23, 2,11,22, 6, 7,19,15,10, 8,16,14, 5, 1,12,24,13, 3],

        # MM: FVPMQCNDHGETWLUJIOKASXPR
        # 'MM':         [ 5,22,19,17,14,24,15,16, 8, 9, 6,11,21,18, 7, 2,20, 1, 4,13,10,23,12, 3],
        }

# validate predictions
def validate_predictions():
    for contestant, ordering in predictions.items():
        count_by_number = collections.Counter(ordering)
        expected = collections.Counter(range(1,25))
        if count_by_number != expected:
            print("predictions are not 1-24 for ", contestant)
            sys.exit()

validate_predictions()


known_outcomes = {
        'A': 'm', # 3 States Flip
        'B': 'm', # 3 Backflips in Breakdancing
        'C': 'n', # Spelling Bee No-B
        'D': 'm', # Only Murders In and Around Building
        'E': 'y', # Wicked Trailer 2x Gravity Defiances
        'F': 'm', # Taylor Swift Eras Tour more than any Movie
        'G': 'y', # Winnie The Pooh kills 10+
        'H': 'y', # Succession not Successful
        'I': 'y', # Amazing Race Boat Capsizes
        'J': 'y', # Groundhogs Agree
        'K': 'm', # Ukraine Wins
        'L': 'y', # Food Flies in Flugtag
        'M': 'm', # Star Wars Outlaws features Jabba or Jawas
        'N': 'y', # Buffalo Buffalo Buffalos
        'O': 'y', # WSOP Heartless Winner
        'P': 'm', # No Perfection in Beat Shazam!
        'Q': 'y', # Foreign Lanugage in Oscars Acceptance Speech
        'R': 'y', # Dragons Drop or Dragon Droppings
        'S': 'm', # Tuba in Tiny Desk
        'T': 'y', # Israel More Popular
        'U': 'y', # Vegas Sphere Glitch
        'V': 'y', # Hell Michigan Freezes
        'W': 'm', # Squid Game Winner is Odd
        'X': 'm', # 40 Cocomelon Thumbnails don't show JJ
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

print("percent of win-paths per person (score so far in parentheses)")
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
    mm_prediction = predictions.get('MM')

    if mm_prediction is None:
        print("skipping mean error analysis")
        return

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
