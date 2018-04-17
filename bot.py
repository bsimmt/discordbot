import discord
from discord.ext import commands
import asyncio
import random
import markovify
import os
import youtube_dl

ADMINS = []
with open(os.getcwd() + "/admins.txt", "r") as file:
	for line in file:
		ADMINS.append(line.strip())

TRUSTED = []
with open(os.getcwd() + "/trusted.txt", "r") as file:
	for line in file:
		TRUSTED.append(line.strip())

CONFIG = {}
with open(os.getcwd() + "/config.txt", "r") as file:
	for line in file:
		option = line.split(":")
		CONFIG[option[0].strip()] = option[1].strip()

VOICE = ""
PLAYER = ""

bot = commands.Bot(CONFIG["command_char"])

def trusted_check(cxt):
	if cxt.message.author.id in TRUSTED or \
		cxt.message.author.id in ADMINS:
		return True
	else:
		return False

def admin_check(cxt):
	if cxt.message.author.id in ADMINS:
		return True
	else:
		return False

def markov_text(cxt, arg):
	markov_read = open(os.getcwd() + "/markov/markov_" + \
		cxt.message.server.id + ".txt", "r", errors="ignore")
	text = markov_read.read()
	markov_read.close()
	text_model = markovify.NewlineText(text)
	markov_text = text_model.make_sentence(tries=int(CONFIG["max_tries"]), \
		max_overlap_ratio=float(CONFIG["overlap_ratio"]))
	return markov_text

def log_markov(message):
	content = str(message.content)
	try:
		markov_log = open(os.getcwd() + "/markov/markov_" + \
			message.server.id + ".txt", "a+")
		if content.endswith("\n"):
			markov_log.write(content)
		else:
			markov_log.write(content + "\n")
		markov_log.close()
	except UnicodeEncodeError:
		pass

def get_soundlist():
	sounds = os.listdir(os.getcwd() + "/sound")
	sounds = [os.path.join("sound", f) for f in sounds]
	sounds.sort(key=os.path.getmtime)
	sounds.reverse()
	sound_list = []
	for sound in sounds:
		sound = sound.split("/")[1]
		sound_list.append(sound[:len(sound)-4])
	return sound_list

@bot.command(pass_context=True, description= \
	"play a sound in voice, get sound list with " + \
	CONFIG["command_char"] + "listsounds")
async def play(cxt, sound: str=""):
	global VOICE
	global PLAYER
	if PLAYER == "" or not PLAYER.is_playing():
		if sound in get_soundlist():
			PLAYER = VOICE.create_ffmpeg_player(os.getcwd() + "/sound/" + \
				sound + ".mp3")
		else:
			PLAYER = VOICE.create_ffmpeg_player(os.getcwd() + "/sound/" + \
				"error.mp3")
			await bot.send_message(cxt.message.channel, \
			"```\nError: sound does not exist\n```")
		PLAYER.volume = 1
		PLAYER.start()

@bot.command(pass_context=True, description= \
	"play a youtube video in voice")
async def youtube(cxt, link: str=""):
	global VOICE
	global PLAYER
	try:
		if PLAYER == "" or not PLAYER.is_playing():
			PLAYER = await VOICE.create_ytdl_player(link.split("&")[0])
	except youtube_dl.utils.DownloadError:
		PLAYER = VOICE.create_ffmpeg_player(os.getcwd() + "/sound/" + \
				"error.mp3")
		await bot.send_message(cxt.message.channel, \
			"```\nError: improper link\n```")
	PLAYER.volume = 1
	PLAYER.start()

@bot.command(description= \
	"stop playing sounds")
async def stop():
	global PLAYER
	PLAYER.stop()

@bot.command(pass_context=True, description= \
	"join voice chat")
async def join(cxt):
	global VOICE
	global PLAYER
	try:
		VOICE = await bot.join_voice_channel(cxt.message.author.voice_channel)
	except discord.errors.InvalidArgument:
		await bot.send_message(cxt.message.channel, \
			"```haskell\nNot in a voice channel (if you are, rejoin" +\
			"the channel)\n```")

@bot.command(description= \
	"leave voice chat")
async def leave():
	global VOICE
	await VOICE.disconnect()

@bot.command(pass_context=True, description= \
	"list all sounds playable in voice chat")
async def listsounds(cxt):
	soundlist_txt = "This list is sorted by last added:\n```"
	sound_list = get_soundlist()
	for sound in sound_list:
		soundlist_txt += "\n" + sound
	soundlist_txt += "\n```"
	await bot.send_message(cxt.message.channel, soundlist_txt)

@bot.command(pass_context=True, description= \
	"markovifies the server chatlog")
async def markov(cxt, arg: str=""):
	tts = False
	if arg == "tts":
		tts = trusted_check(cxt)
	reply = markov_text(cxt, arg)
	await bot.send_message(cxt.message.channel, reply, tts = tts)

@bot.command(pass_context=True, description= \
	"(admin) change currently playing game")
async def game(cxt, game: str=""):
	if cxt.message.author.id in ADMINS:
		if (game != ""):
			await bot.change_presence(game=discord.Game(name=game))
		else:
			await bot.change_presence(game=discord.Game(name=None))

@bot.event
async def on_ready():
	print("Logged in as")
	with open(os.getcwd() + "/ascii.txt", "r") as file:
		for line in file:
			print(line)
	print()

@bot.event
async def on_message(message):
	if not message.content.startswith(bot.command_prefix):
		if not message.author.id == bot.user.id:
			if message.content != "None":
				log_markov(message)
	else:
		await bot.send_typing(message.channel)

	await bot.process_commands(message)

bot.run("token")