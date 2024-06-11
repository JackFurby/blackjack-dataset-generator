import pickle
import os
import json
import argparse
from utils import getCards, getActionFromHandTotal, setAce, genImage
import random


def cardsToConcepts(playerCards, dealerCards):
	pass


def getCardhands(targetNumSamples, trainRatio):

	trainNumTarget = int(targetNumSamples * trainRatio)
	testNumTarget = targetNumSamples - trainNumTarget

	trainGames = genGames(trainNumTarget)
	testGames = genGames(testNumTarget)

	return trainGames, testGames


def genGames(targetSamples):

	numSamples = 0
	games = []

	while numSamples < targetSamples:
		newSamples = genGame()

		games.append(newSamples)

		numSamples += len(newSamples)

	# balance task labels with additional samples (we do not need to worry about concepts as they are roughly balanced by default)
	# get task label count
	task_labels = [0, 0, 0, 0]  # one value for each task label
	for idx, game in enumerate(games):
		for sample in game:
			task_labels[sample["class_label"]] = task_labels[sample["class_label"]] + 1

	# get class label imbalance
	class_imbalance = []
	for i in task_labels:
		class_imbalance.append(task_labels[task_labels.index(max(task_labels))] - i)

	# while an imbalance exists: generate a new game and add samples to a list of game samples
	out_of_game_samples = []
	while sum(class_imbalance) > 0:
		new_game = genGame()
		for sample in new_game:
			if class_imbalance[sample["class_label"]] > 0:  # only add samples if it helps to remove the imbalance
				out_of_game_samples.append(sample)
				class_imbalance[sample["class_label"]] = class_imbalance[sample["class_label"]] - 1

	# the last item in games will represent samples required to balance the dataset
	games.append(out_of_game_samples)

	return games


def genGame():
	"""
	generate samples for a single game and return the game
	"""
	# get a shuffled deck of cards
	cardDesc = getCards()
	random.shuffle(cardDesc)

	rawPlayerCards = []
	rawDelearCards = []
	newSamples = []

	# add initial cards to player and dealer hands
	rawPlayerCards.append(cardDesc.pop())
	rawPlayerCards.append(cardDesc.pop())
	rawDelearCards.append(cardDesc.pop())

	# decide if ace is 11 or 1
	playerCards = setAce(rawPlayerCards)
	delearCards = setAce(rawDelearCards)

	# get value of player and delear hands
	playerTotal = sum([x[2] for x in playerCards])
	delearTotal = sum([x[2] for x in delearCards])

	softHand = True if 11 in [x[2] for x in playerCards] else False

	# set sample class (action for player to take or bust)
	if playerTotal > 21:
		classLabel = 3
	else:
		classLabel = getActionFromHandTotal(playerTotal, delearTotal, ace=softHand)

	newSamples.append({
		"class_label": classLabel,
		"player_cards": playerCards,
		"dealer_cards": delearCards
	})

	while (len(playerCards) < 7) and (playerTotal < 21):  # we are limiting player hands to 7 cards
		rawPlayerCards.append(cardDesc.pop())
		playerCards = setAce(rawPlayerCards)
		playerTotal = sum([x[2] for x in playerCards])

		softHand = True if 11 in [x[2] for x in playerCards] else False

		# set sample class (action for player to take or bust)
		if playerTotal > 21:
			classLabel = 3
		else:
			classLabel = getActionFromHandTotal(playerTotal, delearTotal, ace=softHand)

		newSamples.append({
			"class_label": classLabel,
			"player_cards": playerCards,
			"dealer_cards": delearCards
		})

	while (len(delearCards) < 7) and (delearTotal < 17):  # we are limiting dealer hands to 7 cards
		rawDelearCards.append(cardDesc.pop())
		delearCards = setAce(rawDelearCards)
		delearTotal = sum([x[2] for x in delearCards])

	# set sample class (action for player to take or bust)
	if playerTotal > 21:
		classLabel = 3
	else:
		classLabel = getActionFromHandTotal(playerTotal, delearTotal, ace=softHand)

	# only save final dealer hand
	newSamples.append({
		"class_label": classLabel,
		"player_cards": playerCards,
		"dealer_cards": delearCards
	})

	return newSamples


def createSampleAttrbutes(games, start_index=0):
	samples = {}
	sample_id = start_index
	for idx, game in enumerate(games):
		# each game has an index apart from the last one which is -1 as this is made of filler samples
		if idx == len(games) - 1:
			game_number = -1
		else:
			game_number = idx

		for idy, game_part in enumerate(game):
			# gen image
			game_part = genImage(game_part, sample_id)

			# gen concept vector
			soft_hand = True if 11 in [x[2] for x in game_part["player_cards"]] else False
			concepts = set_concept_vec(game_part["player_cards"], game_part["dealer_cards"], soft_hand)

			# put together dict for sample
			sample = {
				"img_path": game_part["img_path"],
				"class_label": game_part["class_label"],
				"concept_label": concepts,
				"player_card_points": game_part['playerCardCoords'],
				"dealer_card_points": game_part['dealerCardCoords'],
				"game_number": game_number
			}

			samples[sample_id] = sample
			sample_id = sample_id + 1
	return samples, sample_id


def set_concept_vec(player_cards, delear_cards, soft_hand):
	"""
	based on https://www.blackjackapprenticeship.com/blackjack-strategy-charts/
	"""
	player_card_values = [x[2] for x in player_cards]

	if soft_hand:
		soft = 1
		hard = 0
	else:
		soft = 0
		hard = 1

	if sum(player_card_values) >= 20:
		player_value_20 = 1
	else:
		player_value_20 = 0
	if sum(player_card_values) == 19:
		player_value_19 = 1
	else:
		player_value_19 = 0
	if sum(player_card_values) == 18:
		player_value_18 = 1
	else:
		player_value_18 = 0
	if sum(player_card_values) == 17:
		player_value_17 = 1
	else:
		player_value_17 = 0
	if sum(player_card_values) == 16:
		player_value_16 = 1
	else:
		player_value_16 = 0
	if sum(player_card_values) == 15:
		player_value_15 = 1
	else:
		player_value_15 = 0
	if sum(player_card_values) == 14:
		player_value_14 = 1
	else:
		player_value_14 = 0
	if sum(player_card_values) == 13:
		player_value_13 = 1
	else:
		player_value_13 = 0
	if sum(player_card_values) == 12:
		player_value_12 = 1
	else:
		player_value_12 = 0
	if sum(player_card_values) == 11:
		player_value_11 = 1
	else:
		player_value_11 = 0
	if sum(player_card_values) == 10:
		player_value_10 = 1
	else:
		player_value_10 = 0
	if sum(player_card_values) == 9:
		player_value_9 = 1
	else:
		player_value_9 = 0
	if sum(player_card_values) <= 8:
		player_value_8 = 1
	else:
		player_value_8 = 0

	if '2' in delear_cards[0][1]:
		dealer_card_2 = 1
	else:
		dealer_card_2 = 0
	if '3' in delear_cards[0][1]:
		dealer_card_3 = 1
	else:
		dealer_card_3 = 0
	if '4' in delear_cards[0][1]:
		dealer_card_4 = 1
	else:
		dealer_card_4 = 0
	if '5' in delear_cards[0][1]:
		dealer_card_5 = 1
	else:
		dealer_card_5 = 0
	if '6' in delear_cards[0][1]:
		dealer_card_6 = 1
	else:
		dealer_card_6 = 0
	if '7' in delear_cards[0][1]:
		dealer_card_7 = 1
	else:
		dealer_card_7 = 0
	if '8' in delear_cards[0][1]:
		dealer_card_8 = 1
	else:
		dealer_card_8 = 0
	if '9' in delear_cards[0][1]:
		dealer_card_9 = 1
	else:
		dealer_card_9 = 0
	if ('10' in delear_cards[0][1]) or ('J' in delear_cards[0][1]) or ('Q' in delear_cards[0][1]) or ('K' in delear_cards[0][1]):
		dealer_card_10 = 1
	else:
		dealer_card_10 = 0
	if 'A' in delear_cards[0][1]:
		dealer_card_a = 1
	else:
		dealer_card_a = 0
	if len(delear_cards) > 1:
		dealer_multi_cards = 1
	else:
		dealer_multi_cards = 0

	return [
		soft,
		hard,
		player_value_20,
		player_value_19,
		player_value_18,
		player_value_17,
		player_value_16,
		player_value_15,
		player_value_14,
		player_value_13,
		player_value_12,
		player_value_11,
		player_value_10,
		player_value_9,
		player_value_8,
		dealer_card_2,
		dealer_card_3,
		dealer_card_4,
		dealer_card_5,
		dealer_card_6,
		dealer_card_7,
		dealer_card_8,
		dealer_card_9,
		dealer_card_10,
		dealer_card_a,
		dealer_multi_cards
	]



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Options to build a blackjack dataset')
	parser.add_argument(
		'--img_size',
		type=int,
		default=700,
		help='Width and height of the output image'
	)
	parser.add_argument(
		'--target_num_samples',
		type=int,
		default=10000,
		help='Target number of samples in the dataset. The true number of samples may be slightly higher or lower than the set value as the dataset will only contain complete games'
	)
	parser.add_argument(
		'--train_ratio',
		type=float,
		default=0.7,
		help='Ratio of the dataset to generate (1.0 for all, 0 for none)'
	)
	parser.add_argument(
		'--save_name',
		type=str,
		help='Name of the folder containing card images'
	)
	args = parser.parse_args()

	# Generate games
	trainGames, testGames = getCardhands(args.target_num_samples, args.train_ratio)

	"""
	# Create images for games
	sampleId = 0
	for idx, game in enumerate(trainGames):
		for idy, sample in enumerate(game):
			sample = genImage(sample, sampleId, saveName=args.save_name)
			sampleId += 1

	for idx, game in enumerate(testGames):
		for idy, sample in enumerate(game):
			sample = genImage(sample, sampleId, saveName=args.save_name)
			sampleId += 1
	"""

	# Turn games into sample attributes

	train_samples, next_index = createSampleAttrbutes(trainGames)
	val_samples, next_index = createSampleAttrbutes(testGames, start_index=next_index)

	# print dataset stats

	print("\nexample samples")

	print("train:", random.choice(list(train_samples.items())))
	print("val:", random.choice(list(val_samples.items())))

	print("\nlength of train:", len(train_samples))
	print("length of val:", len(val_samples))


	global_classes = [[], []]  # hand class - [[train], [val]]
	concept_classes = [[], []]  # card classes - [[train], [val]]

	for split in [[train_samples, "train"], [val_samples, "val"]]:
		for sample_key in split[0]:
			metric_index = 0 if split[1] == "train" else 1
			# use the first sample to create buckets for counting occurances
			if len(global_classes[metric_index]) == 0:
				for i in range(len(split[0][sample_key]["concept_label"])):
					concept_classes[metric_index].append(0)
				for i in range(4):  # there are 4 task labels
					global_classes[metric_index].append(0)

			# add 1 to each occurance of global and local class
			global_classes[metric_index][split[0][sample_key]["class_label"]] += 1
			for idx, value in enumerate(split[0][sample_key]["concept_label"]):
				if value == 1:
					concept_classes[metric_index][idx] += 1

		print(f"\nCounts for {split[1]}")
		print("Concept classes:", concept_classes[metric_index])
		print("Task classes:", global_classes[metric_index])


	pickle.dump(train_samples, open("./new/train.pkl", "wb"))
	pickle.dump(val_samples, open("./new/val.pkl", "wb"))

	with open('./new/train.json', 'w', encoding='utf-8') as f:
		json.dump(train_samples, f)

	with open('./new/val.json', 'w', encoding='utf-8') as f:
		json.dump(val_samples, f)

"""
pkl / json file structure

id:
{
	img_path: string
	class_label: int (0 indexed)
	concept_label: [list of 0s and 1s]
	player_card_points: [[List of card corner coordinates]]
	dealer_card_points: [[List of card corner coordinates]]
	game_number: int (0 indexed)
}

class labels:
	0: hit
	1: stand
	2: surrender
	3: bust

"""
