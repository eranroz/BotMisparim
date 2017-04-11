# Bot Misparim (Shtei Shekel)
[Bot Misparim](https://he.wikipedia.org/wiki/%D7%95%D7%99%D7%A7%D7%99%D7%A4%D7%93%D7%99%D7%94:%D7%AA%D7%97%D7%96%D7%95%D7%A7%D7%94/%D7%A9%D7%AA%D7%99_%D7%A9%D7%A7%D7%9C) is a script developed for Hebrew Wikipedia for catching common grammar mistakes related to numbers.

In Hebrew one very common mistake is using the wrong gender (שני ילדות; שתי ילדים).

It isn't easy task to parse a sentence and understand to what word the number in the sentence is related to - this bot
does it based on simple regex heuristics<sup>*</sup> rules.
The bot uses hspell project for analyzing words and classify their gender.

<sup>*</sup> You are welcome to challenge this approach with more advanced NLP/ML approaches
(CFG/PCFGs, LSTM/RLU etc) for catching more grammar errors.
 
# Requirements
* pywikibot - python framework to access wikipedia
* HspellPy - a python wrapper for hspell

# Usage
> python misparim.py -xml:XML_DUMP

You can get dump from http://dumps.wikimedia.org/

Advances usage:
> python misparim.py -xml:XML_DUMP -fix

Semi-automatic bot for fixing the suspected errors. (use with CAUTION)

# Possible fails
The bot is heavily based on heuristics so don't always trust it!

Here are some possible mistakes:
* שבע may be 
  * זקן ושבע ימים
  * שבע מרורים
* בני תשע + (males)




