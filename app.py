import streamlit as st
import re

# --- Adatok betöltése ---
@st.cache_data
def load_data():
    try:
        with open('full_filtered.txt', 'r', encoding='utf8') as f:
            filtered_lines = [line.strip() for line in f if line.strip()]
        
        with open('full.txt', 'r', encoding='utf8') as f:
            full_lines = [line.strip() for line in f]
    except FileNotFoundError:
        st.error("Hiányzó adatfájlok! Ellenőrizd a 'full_filtered.txt' és 'full.txt' fájlokat.")
        return [], []
    
    return filtered_lines, full_lines

# --- Rím logika ---
def get_vowels(text):
    """Kinyeri az összes magyar magánhangzót a szövegből."""
    vowels = re.sub(r'[^aáeéiíoóöőuúüűAÁEÉIÍOÓÖŐUÚÜŰ]', '', text)
    return vowels.lower()

def get_word_vowel_counts(text):
    """Visszaadja a szavak magánhangzó-számát egy listában (pl. [2, 2])."""
    words = text.split()
    counts = []
    for word in words:
        v = get_vowels(word)
        if v:
            counts.append(len(v))
    return counts

def normalize_vowels(vowels, loose_matching):
    """
    Normalizálja a magyar magánhangzókat.
    a != á és e != é mindig.
    Ha loose_matching=True, akkor o/ó, ö/ő, u/ú, ü/ű, i/í egynek számít.
    """
    cleaning_map = {'õ': 'ö', 'ô': 'ö', 'û': 'ü'}
    for alt, standard in cleaning_map.items():
        vowels = vowels.replace(alt, standard)

    if not loose_matching:
        return vowels
    
    mapping = {'ó': 'o', 'ő': 'ö', 'ú': 'u', 'ű': 'ü', 'í': 'i'}
    for long, short in mapping.items():
        vowels = vowels.replace(long, short)
    return vowels

def get_match_length(v1, v2):
    """Kiszámolja, hány magánhangzó egyezik a két sor végén."""
    match = 0
    for i in range(1, min(len(v1), len(v2)) + 1):
        if v1[-i] == v2[-i]:
            match += 1
        else:
            break
    return match

def highlight_vowels(text, count_from_end=None):
    """Kiemeli a magánhangzókat zölddel. Ha count_from_end meg van adva, csak az utolsó N magánhangzót."""
    vowel_chars = 'aáeéiíoóöőuúüűAÁEÉIÍOÓÖŐUÚÜŰ'
    
    if count_from_end is None:
        # Összes magánhangzó kiemelése
        return re.sub(f'([{vowel_chars}])', r'<span style="color: green; font-weight: bold;">\1</span>', text)
    
    # Csak az utolsó N magánhangzó kiemelése (hátulról visszafelé haladva)
    chars = list(text)
    vowels_found = 0
    for i in range(len(chars) - 1, -1, -1):
        if chars[i] in vowel_chars:
            chars[i] = f'<span style="color: green; font-weight: bold;">{chars[i]}</span>'
            vowels_found += 1
            if vowels_found >= count_from_end:
                break
    return "".join(chars)

def find_rhymes(input_text, filtered_lines, match_count, loose_matching, rhythm_matching):
    input_vowels = normalize_vowels(get_vowels(input_text), loose_matching)
    input_struct = get_word_vowel_counts(input_text)
    
    if not input_vowels:
        return []
    
    suffix = input_vowels[-match_count:]
    
    results = []
    seen_lines = set()
    for line in filtered_lines:
        if line in seen_lines:
            continue
            
        line_vowels = normalize_vowels(get_vowels(line), loose_matching)
        
        # Ritmikai szűrés: a szavak magánhangzó-eloszlásának egyeznie kell
        if rhythm_matching:
            line_struct = get_word_vowel_counts(line)
            # Ha a rím több szót érint, a többi szónak egyeznie kell hátulról.
            # Az első szó szótagszáma lehet eltérő.
            if len(line_struct) != len(input_struct):
                continue
            
            # Utolsó N-1 szó ellenőrzése
            if len(input_struct) > 1:
                if line_struct[1:] != input_struct[1:]:
                    continue
            
            # Az első szó ellenőrzése:
            # Kiszámoljuk, hány szótag esik a rímből az első szóra a bemenetben.
            input_total_vowels = sum(input_struct)
            vowels_in_remaining_words = sum(input_struct[1:])
            vowels_needed_from_first_word = max(0, match_count - vowels_in_remaining_words)
            
            if line_struct[0] < vowels_needed_from_first_word:
                continue

        if line_vowels.endswith(suffix):
            m_len = get_match_length(input_vowels, line_vowels)
            results.append((line, m_len))
            seen_lines.add(line)
    
    results.sort(key=lambda x: x[1], reverse=True)
    return results

# --- UI elrendezés ---
st.set_page_config(page_title="Magyar Rímkereső", layout="wide")
st.title("hun rhyme")

filtered_data, full_data = load_data()

# Oldalsáv beállítások
st.sidebar.header("beallitas")

match_len = st.sidebar.slider(
    "Egyező magánhangzók száma", 1, 10, 4,
    help="legalább hány magánhangzónak kell egyeznie a sorok végén."
)

loose_match = st.sidebar.checkbox(
    "Hosszú-rövid magánhangzók párosítása", value=True,
    help="Megengedi, hogy a hasonló hangzású, de eltérő hosszúságú magánhangzók rímeljenek (o-ó, ö-ő, u-ú, ü-ű, i-í). Az 'a-á' és 'e-é' továbbra is különbözik! Ha ki van kapcsolva akkor 'oszlopok' (o-o-o) nem rímel a 'folyosó' (o-o-ó) szóra."
)

rhythm_match = st.sidebar.checkbox(
    "Ritmikai szűrő (Szószerkezet)", value=False,
    help="Ha be van kapcsolva, akkor csak olyan találatokat mutat, ahol a szavak belső magánhangzó-eloszlása azonos. pl: 'sárga rózsa' (2+2 magánhangzó) rímel a 'drága lóra' (2+2) sorra, de nem rímel az 'fáradt volt ma' (2+1+1) szóra."
)

# Keresési bemenet
user_input = st.text_input("Írj be egy sort a rímek kereséséhez:", placeholder="pl. mindig egy nő meg a pénz")

if user_input:
    rhymes = find_rhymes(user_input, filtered_data, match_len, loose_match, rhythm_match)
    
    # Keresési kulcsszó megjelenítése kiemelve
    highlighted_input = highlight_vowels(user_input)
    st.markdown(f"### Keresés: {highlighted_input}", unsafe_allow_html=True)
    
    st.subheader(f"{len(rhymes)} találat (erősség szerint rendezve):")
    
    if rhymes:
        for idx, (rhyme, m_strength) in enumerate(rhymes):
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                # Kiemelt rím megjelenítése
                highlighted_rhyme = highlight_vowels(rhyme, count_from_end=m_strength)
                st.markdown(f"**{highlighted_rhyme}**", unsafe_allow_html=True)
                exp = st.expander("Szövegkörnyezet")
            with col2:
                st.write(f"&nbsp;\n\n{m_strength} magánhangzó")
            
            with exp:
                try:
                    occ_idx = -1
                    for i, line in enumerate(full_data):
                        if line.strip() == rhyme:
                            occ_idx = i
                            break
                    
                    if occ_idx != -1:
                        start = max(0, occ_idx - 2)
                        end = min(len(full_data), occ_idx + 3)
                        context = [l for l in full_data[start:end] if l.strip()]
                        
                        st.markdown("---")
                        for context_line in context:
                            if context_line.strip() == rhyme:
                                st.markdown(f"**-> {context_line}**")
                            else:
                                st.text(f"   {context_line}")
                    else:
                        st.info("A szövegkörnyezet nem található.")
                except Exception as e:
                    st.error(f"Hiba: {e}")
    else:
        st.info("Nincs találat. Próbáld módosítani a beállításokat!")
else:
    st.markdown("""
    ### Hogyan használd?
    1. **Írj be egy szót vagy sort** a fenti mezőbe.
    2. Állítsd be a **rímerősséget** (legalább hány magánhangzó egyezzen a végén).
    3. Használd a **Ritmikai szűrőt**, ha azt szeretnéd, hogy a találatok szószerkezete is megegyezzen.
    """)
