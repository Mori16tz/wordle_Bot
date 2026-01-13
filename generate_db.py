from database import Languages, add_word, delete_word, get_all_words, get_word

list = get_all_words(Languages.DE)
for word in list:
    for charac in word:
        if not "a" <= charac <= "z":
            print(word)
