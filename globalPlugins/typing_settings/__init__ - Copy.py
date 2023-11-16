from .sound_lib import output
from .sound_lib.stream import FileStream
import globalPluginHandler
import config
import os
import glob
import wx
import addonHandler
import api
from random import randint
from globalCommands import SCRCAT_CONFIG
from ui import message
from scriptHandler import script
from gui import SettingsPanel, NVDASettingsDialog, guiHelper
from controlTypes import STATE_READONLY, STATE_EDITABLE
from .unidecode import unidecode
bass_output=output.Output()
chans=[]

#Internal
def get_freq(char, group, groups):
	pitch=(((group-(group%2))-0)/(groups-0))*(110-100)+100
	return pitch*1.3 if group%2!=0 and (char.isnumeric() or char.isalpha()) else (90 if not (char.isnumeric() or char.isalpha()) else pitch)

def get_key_pan(char):
	char=unidecode(char)
	keylist=[['z','x','c','v','b','n','m',',','.','/'], ['Z','X','C','V','B','N','M','<','>','?'], ['a','s','d','f','g','h','j','k','l',';','\''], ['A','S','D','F','G','H','J','K','L',':','"'], ['q','w','e','r','t','y','u','i','o','p','[',']'], ['Q','W','E','R','T','Y','U','I','O','P','{','}'], ['`','1','2','3','4','5','6','7','8','9','0','-','='], ['~','!','@','#','$','%','^','&','*','(',')','_','+']]
	groups=len(keylist)
	for group in range(groups):
		keys=len(keylist[group])
		for key in range(keys):
			if keylist[group][key]==char:
				return [((key-0)/((keys-1)-0))*(0.5--0.5)+-0.5, get_freq(char, group, groups-1)]
	return [0, 90]

def play_sound_bass(filename,volume=-1, pan=0.0, pitch=100):
	global chans
	chans.append(FileStream(file=filename, autofree=True))
	last=len(chans)-1
	chans[last].volume=(config.conf["typing_settings"]["volume"]/100 if volume==-1 else volume/100)
	chans[last].pan=pan
	chans[last].frequency=(pitch/100)*44100
	chans[last].play(True)
	while len(chans)>10: chans.remove(chans[0])
	return chans[len(chans)-1]

def confinit():
	confspec = {
		"typingsnd": "boolean(default=true)",
		"typing_sound": f"string(default={get_sounds_folders()[0]})",
		"speak_characters": "integer(default=2)",
		"speak_words": "integer(default=2)",
		"speak_on_protected":"boolean(default=True)",
		"volume": "integer(default=100)"}
	config.confspec["typing_settings"] = confspec

addonHandler.initTranslation()
effects_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "effects")
controls = (8, 52, 82)
typingProtected = api.isTypingProtected

def get_sounds_folders():
		return os.listdir(effects_dir)

def get_sounds(name):
	return [os.path.basename(sound) for sound in glob.glob(f"{effects_dir}/{name}/*.wav")]

def RestoreTypingProtected():
	api.isTypingProtected = typingProtected

def IsTypingProtected():
	if config.conf["typing_settings"]["speak_on_protected"]:
		return False
	focus = api.getFocusObject()
	if focus.isProtected:
		return True

confinit()
class TypingSettingsPanel(SettingsPanel):
	title = _("typing settings")
	def makeSettings(self, settingsSizer):
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		self.tlable = sHelper.addItem(wx.StaticText(self, label=_("typing sound:"), name="ts"))
		self.typingSound = sHelper.addItem(wx.Choice(self, name="ts"))
		sounds = get_sounds_folders()
		self.typingSound.Set(sounds)
		self.typingSound.SetStringSelection(config.conf["typing_settings"]["typing_sound"])
		self.slable = sHelper.addItem(wx.StaticText(self, label=_("sounds"), name="ts"))
		self.sounds = sHelper.addItem(wx.Choice(self, name="ts"))
		sHelper.addItem(wx.StaticText(self, label=_("speek characters")))
		self.speakCharacters = sHelper.addItem(wx.Choice(self, choices=[_("off"), _("anywhere"), _("in edit boxes only")]))
		sHelper.addItem(wx.StaticText(self, label=_("speak words")))
		self.speakWords = sHelper.addItem(wx.Choice(self, choices=[_("off"), _("anywhere"), _("in edit boxes only")]))
		self.playTypingSounds = sHelper.addItem(wx.CheckBox(self, label=_("play sounds while typing")))
		self.playTypingSounds.SetValue(config.conf["typing_settings"]["typingsnd"])
		self.speakPasswords = sHelper.addItem(wx.CheckBox(self, label=_("speak passwords")))
		self.speakPasswords.SetValue(config.conf["typing_settings"]["speak_on_protected"])
		self.volumeSliderLabel = sHelper.addItem(wx.StaticText(self, label=_("Volume")))
		self.volumeSlider = sHelper.addItem(wx.Slider(self))
		self.volumeSlider.SetValue(config.conf["typing_settings"]["volume"])
		try:
			self.speakCharacters.SetSelection(config.conf["typing_settings"]["speak_characters"])
		except:
			self.speakCharacters.SetSelection(0)
		try:
			self.speakWords.SetSelection(config.conf["typing_settings"]["speak_words"])
		except:
			self.speakWords.SetSelection(0)
		self.OnChangeTypingSounds(None)
		self.onChange(None)
		self.playTypingSounds.Bind(wx.EVT_CHECKBOX, self.OnChangeTypingSounds)
		self.typingSound.Bind(wx.EVT_CHOICE, self.onChange)
		self.sounds.Bind(wx.EVT_CHOICE, self.onPlay)
		self.volumeSlider.Bind(wx.EVT_SLIDER, self.onPlay)

	def postInit(self):
		self.typingSound.SetFocus()

	def OnChangeTypingSounds(self, evt):
		for obj in self.GetChildren():
			if obj.Name == "ts": obj.Hide() if not self.playTypingSounds.GetValue() else obj.Show()

	def onChange(self, event):
		sounds = get_sounds(self.typingSound.GetStringSelection())
		self.sounds.Set(sounds)
		try:
			self.sounds.SetSelection(0)
		except: pass

	def onPlay(self, event):
		play_sound_bass(f"{effects_dir}/{self.typingSound.GetStringSelection()}/{self.sounds.GetStringSelection()}",volume=self.volumeSlider.GetValue())

	def onSave(self):
		config.conf["typing_settings"]["typing_sound"] = self.typingSound.GetStringSelection()
		config.conf["typing_settings"]["speak_characters"] = self.speakCharacters.GetSelection()
		config.conf["typing_settings"]["speak_words"] = self.speakWords.GetSelection()
		config.conf["typing_settings"]["speak_on_protected"] = self.speakPasswords.GetValue()
		config.conf["typing_settings"]["typingsnd"] = self.playTypingSounds.GetValue()
		config.conf["typing_settings"]["volume"] = self.volumeSlider.GetValue()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		NVDASettingsDialog.categoryClasses.append(TypingSettingsPanel)

	def IsEditable(self, object):
		return True
		return (object.role in controls or STATE_EDITABLE in object.states) and not STATE_READONLY in object.states

	def event_gainFocus(self, object, nextHandler):
		if config.conf["typing_settings"]["speak_characters"] ==2:
			config.conf["keyboard"]["speakTypedCharacters"] = self.IsEditable(object)
		if config.conf["typing_settings"]["speak_words"] == 2:
			config.conf["keyboard"]["speakTypedWords"] = self.IsEditable(object)
		api.isTypingProtected = IsTypingProtected
		nextHandler()

	def event_typedCharacter(self, obj, nextHandler, ch):
		if self.IsEditable(obj) and config.conf["typing_settings"]["typingsnd"]:
			if ch ==" ":
				play_sound_bass(os.path.join(effects_dir, config.conf['typing_settings']['typing_sound'], "space.wav"))
			elif ch == "\b":
				play_sound_bass(os.path.join(effects_dir, config.conf['typing_settings']['typing_sound'], "delete.wav"))
			else:
				count = self.SoundsCount(config.conf["typing_settings"]["typing_sound"])
				panpitch=get_key_pan(ch)
				play_sound_bass(os.path.join(effects_dir, config.conf['typing_settings']['typing_sound'], "typing.wav" if count<=0 else f"typing_{randint(1, count)}.wav"), -1, panpitch[0], panpitch[1])
		nextHandler()

	def SoundsCount(self, name):
		path = f"{effects_dir}/{name}"
		files = len([file for file in os.listdir(path) if file.startswith("typing_")])
		return files


	@script(
		description = _("Enable and disable typing sounds"),
		category=_("typing settings"),
		gestures=["kb:nvda+shift+k"])
	def script_toggle_typing_sounds(self, gesture):
		current = config.conf["typing_settings"]["typingsnd"]
		if current:
			config.conf["typing_settings"]["typingsnd"] = False
			message(_("typing sounds off"))
		else:
			config.conf["typing_settings"]["typingsnd"] = True
			message(_("typing sounds on"))

	@script(
		description = _("Enable or disable speak passwords"),
		category = _("typing settings"),
		gestures = ["kb:nvda+shift+p"])
	def script_toggle_speak_passwords(self, gesture):
		if config.conf["typing_settings"]["speak_on_protected"]:
			config.conf["typing_settings"]["speak_on_protected"] = False
			message(_("speak passwords off"))
		else:
			config.conf["typing_settings"]["speak_on_protected"] = True
			message(_("speak passwords on"))

	@script(
		description = _("Switches between the available speak characters  modes."),
		category = _("typing settings"),
gestures=["kb:nvda+2"])
	def script_speak_characters(self, gesture):
		current = config.conf["typing_settings"]["speak_characters"]
		if current >=2:
			current = 0
			config.conf["keyboard"]["speakTypedCharacters"] = False
			message(_("speak typed characters off"))
		else:
			current +=1
			if current == 1:
				config.conf["keyboard"]["speakTypedCharacters"] = True
				message(_("speak typed characters anywhere"))
			elif current == 2:
				message(_("speak typed characters in edit boxes only"))
		config.conf["typing_settings"]["speak_characters"] = current

	@script(
		description = _("Switches between the available speak words  modes."),
		category = _("typing settings"),
gestures=["kb:nvda+3"])
	def script_speak_words(self, gesture):
		current = config.conf["typing_settings"]["speak_words"]
		if current >=2:
			current = 0
			config.conf["keyboard"]["speakTypedWords"] = False
			message(_("speak typed words off"))
		else:
			current +=1
			if current == 1:
				config.conf["keyboard"]["speakTypedWords"] = True
				message(_("speak typed words anywhere"))
			elif current == 2:
				message(_("speak typed words in edit boxes only"))
		config.conf["typing_settings"]["speak_words"] = current

	def terminate(self):
		RestoreTypingProtected()
		NVDASettingsDialog.categoryClasses.remove(TypingSettingsPanel)