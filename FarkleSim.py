# FARKLE IMPLEMENTATION/SIMULATOR
# Farkle is a traditional dice game played with 6 dice. 
# It is superficially similar to Yahtzee, but with a lot more player agency and interesting probabalistic considerations!
# Players roll dice, select "scoring combinations" to "keep", and roll remaining dice until they either roll no scoring combos (they "FARKLE"),
# resulting in 0 points for the turn, or choose to stop and add their "kept" score from the turn to their game total. If they have "kept" scoring combos
# on all 6 dice, they may continue their turn by rolling a fresh set of all 6 dice (and retain the turn score they've already rolled). The first player
# to reach 10,000 points wins the game!

import pandas as pd
from random import randint
import ahocorasick
from itertools import combinations

print('Welcome to Farkle!')

# big dictionary of all possible scoring combos. tuple of dice values: score of combo e.g. (1,1): 200, (5,): 50
# jk - making it a dataframe from a csv, to improve readability and allow for n_dice (to filter results for rolls), and more info later if needed
scoring_combos_df = pd.read_csv('farkle_scoring.csv')
# columns: dice_rolls, score, n_dice_used
# unfortunately dice_rolls is imported as a string, not tuple :(
# convert to normal str format
scoring_combos_df['dice_rolls_str'] = scoring_combos_df['dice_rolls'].apply(lambda s: ''.join(s[1:-1].split(',')))
# print(type(scoring_combos_df.iat[5, 2]))
# print(scoring_combos_df.head())

# big (biggest?) challenge of this will be the algorithm to identify the scoring combos that have been rolled
# use Aho-Corasick algorithm/automaton to find the "needles" of scoring combinations in the "haystack" of a dice roll
scoring_finder = ahocorasick.Automaton()
# add all scoring combos, converted to strings, as "needles"/"words" to automaton
for score_str in scoring_combos_df.dice_rolls_str:
	# print(type(score_tup), score_tup)
	# (no longer necessary) score_str = ''.join(score_tup[1:-1].split(',')) # converting from 'tuple-like' string to normal string of dice vals
	# print(type(score_str), score_str)
	scoring_finder.add_word(score_str, score_str) # associate the actual combo of dice as "value" in automaton
scoring_finder.make_automaton()
# now scoring_finder is a complete Aho-Corasick automaton containing all scoring combinations. Searching along a dice roll will return all the scoring
# combos present in the roll. Crucially, this depends on the dice being in ascending order, and the structure of the scoring combos in Farkle. 


# game scoreboard. probably put everything in a game wrapper class if/when I want to run it
# dict player_name: game_score
# game_scores = {}

# roll n dice, return list of rolled values
def roll(n):
	return [randint(1,6) for _ in range(n)]

# print(roll(6),roll(3),roll(1))

def is_sublist(input_list, test_superset):
	# input_list is a list of strs, test that all of them combined are still within (str) test_superset i.e. to avoid duplicates
	# "111","111" in "1111" = False, but "11","11" in "1111" = True
	# useful test case: 1,1111,5 from 111156 -> False
	# the input list will still be sorted! can leverage this
	# N.B.: again depends on structure of Farkle scoring combos. only exception to it coming in sorted is "123456", trying to combine "1","5","123456"
	# This case is accounted for by the length of the combo being longer than the input dice
	# use pointers -> i in input, j in test. if i<j return False, if they match increase both, and if i>j, increase j. if you get to the end of i return T
	# account for len input>test case first to save time anyway
	input_str = ''.join(input_list)
	# print(input_str, test_superset)
	if len(input_str) > len(test_superset):
		return False
	i = 0
	j = 0
	while i<len(input_str):
		# print(i,j)
		if j>=len(test_superset): # no match found, there is an elt in input not in superset -> False
			return False
		elif int(input_str[i])<int(test_superset[j]): # there is an elt in input not in superset -> False
			return False
		elif int(input_str[i])>int(test_superset[j]): # there is an elt in superset not in input -> increase superset pointer to try again
			j+=1
		else: # match, increment both pointers
			i+=1
			j+=1
	# when it gets here, it has gone through entire input_str and found matches in test_superset -> True
	return True



def get_scoring_combos(dice_list): # algorithm to return list of (dice,), score pairs (as a dict? list? df? not sure)
	'''
	# first, limit scoring combos to those that can be made by the number of dice that were rolled
	n_dice_rolled = len(dice_list)
	possible_combos = scoring_combos_df.query('n_dice_used <= @n_dice_rolled') # <- this is now unnecessary using Aho-Corasick, which automatically
	# takes into account the length of the "haystack" i.e. the dice roll
	# print(possible_combos)
	'''
	# sort dice list and convert to a string to be passed to automaton
	dice_str = ''.join(str(d) for d in sorted(dice_list))
	# search for scoring combos in dice_str (do we want these returned as strings, tuples? strings by default)
	initial_scoring_combos_dice_list = [combo[1] for combo in scoring_finder.iter(dice_str)]
	initial_scoring_combos_score_dict = {combo: scoring_combos_df.loc[scoring_combos_df['dice_rolls_str']==combo, 'score'].iloc[0] for combo in initial_scoring_combos_dice_list}
	
	# print(initial_scoring_combos_score_dict)
	# dict of scoring combos and their associated scores. for easy lookup and combining scores
	# print(initial_scoring_combos_dice_list)
	# returns list of strings representing possible scoring_combo from the rolled dice
	# have to have this list to account for duplicates i.e. 2 "1"s

	# combine combos to complete possibilities i.e. "1","1" -> "11", also return as a list of ints instead? type manipulation is an annoying part
	# also should remove duplicates i.e. if "5,5,5", should have "5","55","555", not "5","5","5","555"
	combined_combos_dict = dict()
	for r in range(1, len(initial_scoring_combos_dice_list)+1):
		for c in combinations(initial_scoring_combos_dice_list, r):
			# print(c)
			combined_score = sum(initial_scoring_combos_score_dict[k] for k in c)
			if c not in combined_combos_dict and is_sublist(c, dice_str): # and (combined combo is still in dice_str):
				combined_combos_dict[c] = combined_score

	scoring_combos = sorted([(k,v) for k,v in combined_combos_dict.items()], key=lambda x: x[1])

	return scoring_combos

	# algo we want is essentially a (sorted?) subset finder (EXCEPT vvv)
	# make sure we allow the algo to return repeated combos/combos of combos i.e. if the roll is "1,1,5,2,3,2" we want it to return (1,1,5) as an option,
	# and (1,1), and (1,5) etc. even though they are not themselves in possible_combos
	# idea: Aho-Corasick BUT with ability to "skip" dice i.e. pull out (1,5) from (1,2,2,3,4,5) or (2,4,6) from (2,2,3,4,4,6) <- BUT the latter will never
	# be necessary due to structure of the scoring combos. Aho-Corasick will work as long as we combine combos e.g. (1,), (5,) -> (1,5) afterwards.
	# this can be done decently easily since the numbers will be small (max length of "haystack" is 6). so just sort dice_list and then run Aho-Corasick on it
	# Aho-Corasick (and pyahocorasick) runs on strings in particular, so will have to convert tuples/list to strings as we build

# print(get_scoring_combos([1,1,1,1,5,6]))
# print(get_scoring_combos([2,4,5,5,1,5]))
'''
for _ in range(10):
	r = roll(4)
	print(r)
	get_scoring_combos(r)
'''

# first attempt at a player's turn - could be a fun extension to implement a turn iteratively as well!
'''
def take_turn_iter(player):
	turn_score = 0 # initialize new score for the turn
	kept_dice = [] # initialize list of dice that have been kept as scoring combos. length determines the next roll of the remaining dice, and if it gets
				   # to length 6 turn can continue with new 6 dice

	# all turns start with rolling 6 dice
	rolled = roll(6)

	# find out scoring combos from 'rolled' list <-- heaviest lift
	scoring_combos = [] # result of algo

	if len(scoring_combos) == 0: # farkle! turn is over
		turn_score = 0
		return turn_score 

	# else:
	# 	select scoring combo to keep
	# 	add these values to kept_dice <- now len 1-6
	# 	add scoring value to turn_score

	# IF player wants to stop, keep_rolling = False:
	# 	return turn_score
	# IF player wants to continue, keep_rolling = True:
	# 	if len(kept_dice) == 6:
	# 		reset kept_dice
	#		roll(6)
	# 	else:
	#		roll(6-len(kept_dice))
	# should probably make this recursive <- but how to 'escape' recursion in case of a farkle <- can just make 'take_turn' itself recursive
'''

# running a game scaffolding
	# collect/list player names
	# initialize game_scores dict for players
	# game_end = False
	# while not game_end:
	#	for p in players:
	#		player_turn(p)
	# (now game_end is true)
	# winner = a player now. intialize game class w/ a null winner
	# print("{} wins!".format(winner))

class FarkleGame:
	def __init__(self, players, target_score=10000):
		# Start a new game with the player names listed in players
		self.players = players
		self.game_end = False
		self.game_scores = {k: 0 for k in players}
		self.target_score = target_score
		self.winner = None

		while not self.game_end:
			for p in self.players:
				self.player_turn(p) # everyone gets the same number of turns
		print("{} wins!".format(self.winner))

	def player_turn(self, player):
		# wrapper for a player's turn
		print("{}'s turn:".format(player))
		turn_score = self.take_turn_recur()
		self.game_scores[player] += turn_score
		print("Total score for {} is {}.".format(player, self.game_scores[player]))
		if self.game_scores[player] >= self.target_score:
			self.game_end = True
			self.winner = player # area for improvement -> don't automatically win, but give everyone else one more turn and then look at max in game_scores
		return

	def take_turn_recur(self, turn_score=0, n_dice=6, kept_dice=""):
		new_turn_score = turn_score
		new_kept_dice = kept_dice

		# roll the dice (all turns start with 6 dice)
		rolled = roll(n_dice)
		print("You rolled: {}".format(rolled)) # area for improvement -> all print statements could be updated with visuals for better human readability

		# find out scoring combos from 'rolled'
		scoring_combos = get_scoring_combos(rolled) # returns list of (("dice",), score) tuples

		if len(scoring_combos) == 0: # Farkle! Turn is over
			print("FARKLE! Oh no, your turn is over! You scored 0.")
			new_turn_score = 0
			return new_turn_score

		else: # there are possible scoring combos
			print("Select one of the scoring combos from your roll:\n")
			# print scoring combos
			print("Index\t(Dice to Keep, Score)")
			print("_____________________________\n")
			for x,y in enumerate(scoring_combos):
				print("{}\t{}\n".format(x,y))

			# get user input to select a scoring combo
			while True:
				try:
					chosen_combo_index = int(input("Choose the index corresponding to the scoring combo you wish to keep: "))
					break
				except:
					print("I'm sorry, I don't understand. Please try again.")
			chosen_combo = scoring_combos[chosen_combo_index] # dice, score pair
			new_turn_score += chosen_combo[1]

			# consider (extremely unlikely) edge case to prevent infinite recursion
			if new_turn_score > 10000:
				print("Wow! You've won the whole game in a single turn! You scored {}".format(new_turn_score))
				return new_turn_score

			for s in chosen_combo[0]:
				new_kept_dice+=s
			new_n_dice = 6-len(new_kept_dice)
			if new_n_dice == 0: # all dice used, reset to a clean slate of 6 dice
				new_n_dice = 6
				new_kept_dice = ""
			print("Turn score is {}. Do you want to keep rolling with {} dice?".format(new_turn_score, new_n_dice))
			while True:
				keep_rolling = input("Keep rolling? Y/N: ").lower() # get user input to continue
				if keep_rolling == "n" or keep_rolling == "no":
					print("You scored {}.".format(new_turn_score))
					return new_turn_score
				elif keep_rolling == "y" or keep_rolling == "yes":
					return self.take_turn_recur(new_turn_score, new_n_dice, new_kept_dice)
				elif keep_rolling == "quit" or keep_rolling == "exit": # failsafe to get out of program if user does not want to play entire game
					raise SystemExit
				else:
					print("I'm sorry, I don't understand. Please try again.")
					continue


	# take_turn_recur()



# FarkleGame(["Jake"], 5000)