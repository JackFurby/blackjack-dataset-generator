import numpy as np
import copy
from PIL import Image
import random
import os

import matplotlib.pyplot as plt
from matplotlib.patches import Circle


def getCards():
	# [index, class string, value / values]
	return [
		[0, "2C", 2],
		[1, "2D", 2],
		[2, "2H", 2],
		[3, "2S", 2],
		[4, "3C", 3],
		[5, "3D", 3],
		[6, "3H", 3],
		[7, "3S", 3],
		[8, "4C", 4],
		[9, "4D", 4],
		[10, "4H", 4],
		[11, "4S", 4],
		[12, "5C", 5],
		[13, "5D", 5],
		[14, "5H", 5],
		[15, "5S", 5],
		[16, "6C", 6],
		[17, "6D", 6],
		[18, "6H", 6],
		[19, "6S", 6],
		[20, "7C", 7],
		[21, "7D", 7],
		[22, "7H", 7],
		[23, "7S", 7],
		[24, "8C", 8],
		[25, "8D", 8],
		[26, "8H", 8],
		[27, "8S", 8],
		[28, "9C", 8],
		[29, "9D", 9],
		[30, "9H", 9],
		[31, "9S", 9],
		[32, "10C", 10],
		[33, "10D", 10],
		[34, "10H", 10],
		[35, "10S", 10],
		[36, "JC", 10],
		[37, "JD", 10],
		[38, "JH", 10],
		[39, "JS", 10],
		[40, "QC", 10],
		[41, "QD", 10],
		[42, "QH", 10],
		[43, "QS", 10],
		[44, "KC", 10],
		[45, "KD", 10],
		[46, "KH", 10],
		[47, "KS", 10],
		[48, "AC", [1, 11]],
		[49, "AD", [1, 11]],
		[50, "AH", [1, 11]],
		[51, "AS", [1, 11]]
	]


def getActions():
	# [index, class string]
	return [
		[0, "hit"],
		[1, "stand"],
		[2, "surrender"]
	]


def getActionFromHandTotal(playersCardsTotal, delearsCardsTotal, ace):
	"""
	ace (bool): True if ace in in card hand and its value is set to 11
	"""

	# soft hand
	if ace:
		if playersCardsTotal <= 17:
			return 0
		else:
			if (playersCardsTotal == 18) and (delearsCardsTotal in [9, 10]):
				return 0
			else:
				return 1
	# hard hand
	else:
		if playersCardsTotal <= 11:
			return 0
		elif (playersCardsTotal == 12) and (delearsCardsTotal in [1, 2, 3]):
			return 0
		elif (playersCardsTotal in [12, 13, 14, 15]) and (delearsCardsTotal in [7, 8, 9, 10, 11]):
			return 0
		elif (playersCardsTotal == 16) and (delearsCardsTotal in [7, 8, 9]):
			return 0
		elif (playersCardsTotal == 16) and (delearsCardsTotal in [10, 11]):
			return 2
		else:
			return 1


def setAce(cards):
	""" Set the value of ace to either 1 or 11
	This will follow the policy of setting ace to 11 if it does not set the hand total over 21, otherwise ace will be set to 1
	"""
	returnCards = []  # cards to return with ace set to either 1 or 11
	aceCards = []  # temp list for ace cards

	# seperate ace from other cards
	for card in cards:
		if "A" in card[1]:
			aceCards.append(copy.deepcopy(card))  # copy card values
		else:
			returnCards.append(copy.deepcopy(card))  # copy card values

	# return cards if no ace is included
	if len(aceCards) == 0:
		return returnCards
	# get sum of non ace card values
	else:
		# hand only contains ace cards
		if len(returnCards) == 0:
			sumOtherCards = 0
		# hand has non ace cards
		else:
			sumOtherCards = sum([x[2] for x in returnCards])

	# Only one ace in hand
	if len(aceCards) == 1:
		if sumOtherCards + 11 > 21:  # ace == 11 is a bust (hand value over 21)
			aceCards[0][2] = 1
		else:  # ace == 11 is not a bust (hand value under or equal to 21)
			aceCards[0][2] = 11
		returnCards.append(aceCards[0])
	# More than 1 ace in hand
	else:
		# set all ace values to 1
		aceValues = []
		for ace in aceCards:
			aceValues.append(1)
		# All ace cards set to 1 is a bust
		if sumOtherCards + sum(aceValues) > 21:
			for ace in aceCards:
				ace[2] = 1
				returnCards.append(ace)
		# set ace cards to 11 (one at a time) until a bust is met or all cards are a 11
		else:
			for idx, ace in enumerate(aceValues):
				aceValues[idx] = 11
				if sumOtherCards + sum(aceValues) > 21:
					aceValues[idx] = 1
					aceCards[idx][2] = 1
					returnCards.append(aceCards[idx])
				else:
					aceCards[idx][2] = 11
					returnCards.append(aceCards[idx])

	# reorder returnCards to match the order of cards
	# TO DO
	returnCardsSorted = []
	for card in cards:
		for idx, finalCard in enumerate(returnCards):
			if card[0] == finalCard[0]:
				returnCardsSorted.append(finalCard)

	return returnCardsSorted


def resizeCards(img, newHeight):
	width, height = img.size
	ratio = width / height
	newWidth = int(ratio * newHeight)
	scale = ((newWidth/width), (newHeight/height))
	return img.resize((newWidth, newHeight)), scale


def transformPoints(cardCoords, scale, translate):
	new_card_coords = []
	for idx, card in enumerate(cardCoords):
		coords = card[0]
		card_string = card[1]
		for idy, point in enumerate(coords):

			#resize
			point = (int(point[0] * scale[0]), int(point[1] * scale[1]))

			# location
			point = (point[0] + translate[0], point[1] + translate[1])

			# update point
			coords[idy] = point
		new_card_coords.append((coords, card_string))

	return new_card_coords


def genImage(sample, sampleId, saveName="new", returnImg=False):
	img = Image.new('RGBA', (1024, 1024), color=(0, 145, 48, 0))  # backgound is green

	playerCardImg, playerCardCoords = place_cards(sample["player_cards"])
	dealerCardImg, dealerCardCoords = place_cards(sample["dealer_cards"])

	newHeight = 185
	playerCardImg, playCardScale = resizeCards(playerCardImg, newHeight)
	dealerCardImg, dealerCardScale = resizeCards(dealerCardImg, newHeight)

	img.paste(playerCardImg, (50, (1024 - 50 - newHeight)), playerCardImg)
	img.paste(dealerCardImg, (50, 50), dealerCardImg)

	img = img.convert('RGB')  # remove alpha channel

	# apply transformation to card coordinates
	playerCardCoords = transformPoints(playerCardCoords, playCardScale, (50, (1024 - 50 - newHeight)))
	dealerCardCoords = transformPoints(dealerCardCoords, dealerCardScale, (50, 50))

	# save image
	save_path = f"{saveName}/imgs"
	if not os.path.exists(save_path):
		os.makedirs(save_path)
	img.save(f"{save_path}/{sampleId}.png", format="png")

	if returnImg:
		return {
			'class_label': sample['class_label'],
			'sampleId': sampleId,
			'playerCardCoords': playerCardCoords,
			'dealerCardCoords': dealerCardCoords,
			'img_path': f"imgs/{sampleId}.png",
			'player_cards': sample["player_cards"],
			'dealer_cards': sample["dealer_cards"]
		}, img
	else:
		return {
			'class_label': sample['class_label'],
			'sampleId': sampleId,
			'playerCardCoords': playerCardCoords,
			'dealerCardCoords': dealerCardCoords,
			'img_path': f"imgs/{sampleId}.png",
			'player_cards': sample["player_cards"],
			'dealer_cards': sample["dealer_cards"]
		}


def place_cards(cards):
	"""
	return a image of given cards placed next to each other
	"""

	card_imgs = []
	card_rotated = []  # record whether a card has been rotated or not
	for card in cards:
		rotate = random.choice([0, 180])
		if rotate == 0:
			card_rotated.append(False)
		else:
			card_rotated.append(True)
		card_imgs.append(Image.open(f"./card_decks/deck_1/{card[1]}.png", 'r').rotate(rotate, Image.NEAREST, expand=1))

	img = Image.new('RGBA', ((card_imgs[0].width * len(card_imgs) + (len(card_imgs) * 50)), card_imgs[0].height), (255, 0, 0, 0))

	card_coords = []
	x_pos = 0
	for idx, card in enumerate(card_imgs):
		# list order: card top left, card top right, card bottom left, card bottom right
		if card_rotated[idx]:
			card_coords.append(([
				(x_pos + card.width, card.height),
				(x_pos, card.height),
				(x_pos + card.width, 0),
				(x_pos, 0)
			], cards[idx][1]))
		else:
			card_coords.append(([
				(x_pos, 0),
				(x_pos + card.width, 0),
				(x_pos, card.height),
				(x_pos + card.width, card.height)
			], cards[idx][1]))
		img.paste(card, (x_pos, 0))
		x_pos = x_pos + card.width + 50

	return img, card_coords


if __name__ == "__main__":

	delearTotals = [x for x in range(1, 12)]
	playerTotalsHard = [x for x in range(5, 18)]
	playerTotalsSoft = [x for x in range(13, 21)]

	print(delearTotals)
	print(playerTotalsHard)
	print(playerTotalsSoft)

	yHard = np.empty((len(playerTotalsHard), len(delearTotals)))
	ySoft = np.empty((len(playerTotalsSoft), len(delearTotals)))

	for idx, playerValue in enumerate(playerTotalsHard):
		for idy, delearValue in enumerate(delearTotals):
			yHard[idx, idy] = getActionFromHandTotal(playerValue, delearValue, ace=False)

	for idx, playerValue in enumerate(playerTotalsSoft):
		for idy, delearValue in enumerate(delearTotals):
			ySoft[idx, idy] = getActionFromHandTotal(playerValue, delearValue, ace=True)

	print("Hard")
	print(yHard)
	print("Soft")
	print(ySoft)
	# hand classes based on https://wizardofodds.com/games/blackjack/strategy/1-deck/

	#--------------------------
	# ace card value set tests
	# note: card order should not change                                     <<<<<<<<<<<<<<<<<<<<<<<<<<<<<< TO DO
	#--------------------------


	# no ace, cards should not change
	hand = [
		[3, "2S", 2],
		[7, "3S", 3],
		[44, "KC", 10]
	]
	print("in:", hand)
	print("out:", setAce(hand))

	# one ace, should be set to 11
	hand = [
		[3, "2S", 2],
		[7, "3S", 3],
		[51, "AS", [1, 11]]
	]
	print("in:", hand)
	print("out:", setAce(hand))

	# one ace, should be set to 1
	hand = [
		[3, "2S", 2],
		[7, "3S", 3],
		[51, "AS", [1, 11]],
		[47, "KS", 10]
	]
	print("in:", hand)
	print("out:", setAce(hand))

	# two aces, both should be set to 1
	hand = [
		[3, "2S", 2],
		[7, "3S", 3],
		[51, "AS", [1, 11]],
		[50, "AH", [1, 11]],
		[47, "KS", 10]
	]
	print("in:", hand)
	print("out:", setAce(hand))

	# two aces, one should be set to 1, one to 11
	print("final")
	hand = [
		[3, "2S", 2],
		[7, "3S", 3],
		[51, "AS", [1, 11]],
		[50, "AH", [1, 11]]
	]
	print("in:", hand)
	print("out:", setAce(hand))

	hand = [
		[3, "2S", 2],
		[7, "3S", 3],
		[51, "AS", 11],
		[50, "AH", 1]
	]
	img, card_coords = place_cards(hand)
	img.show()
	print(card_coords)

	sample = {
		'class_label': 1,
		'player_cards': [[27, '8S', 8], [30, '9H', 9]],
		'dealer_cards': [[10, '4H', 4]]
	}
	sample, img = genImage(sample, 0, returnImg=True)
	print(sample)
	img.show()

	sample = {
		'class_label': 3,
		'player_cards': [[27, '8S', 8], [30, '9H', 9], [7, '3S', 3], [6, '3H', 3]],
		'dealer_cards': [[10, '4H', 4], [23, '7S', 7], [21, '7D', 7]]
	}
	sample, img = genImage(sample, 1, returnImg=True)
	print(sample)
	img.show()

	sample = {
		'class_label': 3,
		'player_cards': [[27, '8S', 8], [27, '8S', 8], [27, '8S', 8], [27, '8S', 8], [27, '8S', 8], [27, '8S', 8], [27, '8S', 8]],
		'dealer_cards': [[10, '4H', 4], [10, '4H', 4], [10, '4H', 4], [10, '4H', 4], [10, '4H', 4], [10, '4H', 4], [10, '4H', 4]]
	}
	sample, img = genImage(sample, 2, returnImg=True)
	print(sample)
	img.show()

	# show image preview with coordinates
	fig, ax = plt.subplots(1)
	ax.imshow(np.asarray(img))
	for card in sample["dealerCardCoords"]:
		for point_no in range(len(card[0])):
			if point_no == 0:
				ax.add_patch(Circle((card[0][point_no][0], card[0][point_no][1]), 10, color='red'))  # top left
			elif point_no == 1: # top right
				ax.add_patch(Circle((card[0][point_no][0], card[0][point_no][1]), 10, color='green'))  # top left
			elif point_no == 2: # bottom left
				ax.add_patch(Circle((card[0][point_no][0], card[0][point_no][1]), 10, color='orange'))  # top left
			else:
				ax.add_patch(Circle((card[0][point_no][0], card[0][point_no][1]), 10, color='blue'))  # bottom right

	for card in sample["playerCardCoords"]:
		for point_no in range(len(card[0])):
			if point_no == 0:
				ax.add_patch(Circle((card[0][point_no][0], card[0][point_no][1]), 10, color='red'))  # top left
			elif point_no == 1: # top right
				ax.add_patch(Circle((card[0][point_no][0], card[0][point_no][1]), 10, color='green'))  # top left
			elif point_no == 2: # bottom left
				ax.add_patch(Circle((card[0][point_no][0], card[0][point_no][1]), 10, color='orange'))  # top left
			else:
				ax.add_patch(Circle((card[0][point_no][0], card[0][point_no][1]), 10, color='blue'))  # bottom right
	plt.show()    # Default is a blocking call
