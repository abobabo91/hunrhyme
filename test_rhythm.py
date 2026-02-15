import re

def get_vowels(text):
    vowels = re.sub(r'[^aáeéiíoóöőuúüűAÁEÉIÍOÓÖŐUÚÜŰ]', '', text)
    return vowels.lower()

def get_word_vowel_counts(text):
    words = text.split()
    counts = []
    for word in words:
        v = get_vowels(word)
        if v:
            counts.append(len(v))
    return counts

def check_rhythm(input_struct, line_struct, match_count):
    if len(line_struct) != len(input_struct):
        return False
    
    # Utolsó N-1 szó ellenőrzése
    if len(input_struct) > 1:
        if line_struct[1:] != input_struct[1:]:
            return False
    
    vowels_in_remaining_words = sum(input_struct[1:])
    vowels_needed_from_first_word = max(0, match_count - vowels_in_remaining_words)
    
    if line_struct[0] < vowels_needed_from_first_word:
        return False
    
    return True

# Teszt esetek a felhasználó példája alapján: 3+2+1, match_count=4
input_s = [3, 2, 1]
match_c = 4

test_cases = [
    ([1, 2, 1], True),   # Felhasználó példája: 1+2+1 jó
    ([2, 2, 1], True),   # 2+2+1 is jó (több van az első szóban mint kell)
    ([3, 2, 1], True),   # Pontos egyezés is jó
    ([0, 2, 1], False),  # Első szóban 0 szótag (nem is lehetséges a get_word_vowel_counts-al, de elvben False)
    ([1, 1, 1], False),  # Második szó nem egyezik
    ([3, 2, 2], False),  # Utolsó szó nem egyezik
]

for struct, expected in test_cases:
    res = check_rhythm(input_s, struct, match_c)
    print(f"Input: {input_s}, Line: {struct}, Match: {match_c} -> Result: {res}, Expected: {expected}")
    assert res == expected

print("Minden teszt sikeres!")
