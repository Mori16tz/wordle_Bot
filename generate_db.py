from database import Languages, add_word

wordlist = []
with open("valid_words.txt", encoding="utf8") as f:
    for line in f:
        wordlist.append(line.strip())

with open("possible_guesses.txt", encoding="utf8") as f:
    for line in f:
        add_word(line.strip(), Languages.EN, line.strip() in wordlist)
