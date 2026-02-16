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

def highlight_vowels(text, highlight_mask=None):
    """
    Kiemeli a magánhangzókat zölddel. 
    Ha highlight_mask meg van adva (bool lista a magánhangzókra), csak azokat emeli ki.
    """
    vowel_chars = 'aáeéiíoóöőuúüűAÁEÉIÍOÓÖŐUÚÜŰ'
    
    chars = list(text)
    vowel_idx = 0
    for i in range(len(chars)):
        if chars[i] in vowel_chars:
            should_highlight = True
            if highlight_mask is not None:
                should_highlight = highlight_mask[vowel_idx] if vowel_idx < len(highlight_mask) else False
            
            if should_highlight:
                chars[i] = f'<span style="color: green; font-weight: bold;">{chars[i]}</span>'
            vowel_idx += 1
            
    return "".join(chars)

def get_rhyme_mask(input_vowels, line_vowels, match_count, include_internal):
    """
    Visszaad egy bool maszkot a line_vowels-hez.
    """
    mask = [False] * len(line_vowels)
    
    # End rhyme (mindig számoljuk, ha elég hosszú)
    m_len = get_match_length(input_vowels, line_vowels)
    if m_len >= match_count:
        for i in range(1, m_len + 1):
            mask[-i] = True
            
    if not include_internal:
        return mask

    # Internal rhyme
    input_substrings = set()
    for i in range(len(input_vowels) - match_count + 1):
        input_substrings.add(input_vowels[i:i+match_count])
        
    for i in range(len(line_vowels) - match_count + 1):
        sub = line_vowels[i:i+match_count]
        if sub in input_substrings:
            for j in range(i, i + match_count):
                mask[j] = True
                
    return mask

def find_rhymes(input_text, filtered_lines, match_count, loose_matching, rhythm_matching, internal_rhyme=True, cross_line=False):
    input_vowels = normalize_vowels(get_vowels(input_text), loose_matching)
    input_struct = get_word_vowel_counts(input_text)
    
    if not input_vowels:
        return []
    
    suffix = input_vowels[-match_count:]
    results = []
    
    # --- Egysoros rímek ---
    seen_lines = set()
    for line in filtered_lines:
        if line in seen_lines: continue
        line_vowels_raw = get_vowels(line)
        line_vowels = normalize_vowels(line_vowels_raw, loose_matching)
        
        if rhythm_matching:
            line_struct = get_word_vowel_counts(line)
            if len(line_struct) != len(input_struct): continue
            if len(input_struct) > 1 and line_struct[1:] != input_struct[1:]: continue
            vowels_in_remaining_words = sum(input_struct[1:])
            vowels_needed_from_first_word = max(0, match_count - vowels_in_remaining_words)
            if line_struct[0] < vowels_needed_from_first_word: continue

        is_match = False
        m_len = 0
        
        if line_vowels.endswith(suffix):
            is_match = True
            m_len = get_match_length(input_vowels, line_vowels)
        elif internal_rhyme and suffix in line_vowels:
            is_match = True
            for length in range(len(input_vowels), match_count - 1, -1):
                for i in range(len(input_vowels) - length + 1):
                    sub = input_vowels[i:i+length]
                    if sub in line_vowels:
                        m_len = length
                        break
                if m_len > 0: break

        if is_match:
            mask = get_rhyme_mask(input_vowels, line_vowels, match_count, internal_rhyme)
            results.append({
                "type": "single",
                "line": line,
                "strength": m_len,
                "mask": mask
            })
            seen_lines.add(line)

    # --- Kereszt-soros rímek ---
    if cross_line:
        for i in range(len(filtered_lines) - 1):
            line1 = filtered_lines[i]
            line2 = filtered_lines[i+1]
            v1 = normalize_vowels(get_vowels(line1), loose_matching)
            v2 = normalize_vowels(get_vowels(line2), loose_matching)
            
            found_cross = False
            best_m = 0
            for split_idx in range(1, match_count):
                part1_len = split_idx
                part2_len = match_count - split_idx
                s1 = input_vowels[-match_count : -part2_len]
                s2 = input_vowels[-part2_len:]
                if v1.endswith(s1) and v2.startswith(s2):
                    found_cross = True
                    m1 = get_match_length(input_vowels[:-part2_len], v1)
                    m2 = 0
                    rem_input = input_vowels[-part2_len:]
                    for k in range(min(len(rem_input), len(v2))):
                        if rem_input[k] == v2[k]: m2 += 1
                        else: break
                    best_m = m1 + m2
                    break
            
            if found_cross:
                mask1 = [False] * len(v1)
                for k in range(1, m1 + 1): mask1[-k] = True
                mask2 = [False] * len(v2)
                for k in range(m2): mask2[k] = True
                results.append({
                    "type": "cross",
                    "line1": line1, "line2": line2,
                    "strength": best_m,
                    "mask1": mask1, "mask2": mask2
                })

    results.sort(key=lambda x: x["strength"], reverse=True)
    return results

# --- UI elrendezés ---
st.set_page_config(page_title="Magyar Rímkereső", layout="wide")
st.title("hun rhyme")

filtered_data, full_data = load_data()

st.sidebar.header("beallitas")

match_len = st.sidebar.slider(
    "Egyező magánhangzók száma", 1, 10, 4,
    help="legalább hány magánhangzónak kell egyeznie."
)

loose_match = st.sidebar.checkbox(
    "Hosszú-rövid magánhangzók párosítása", value=True,
    help="Megengedi, hogy a hasonló hangzású, de eltérő hosszúságú magánhangzók rímeljenek."
)

rhythm_match = st.sidebar.checkbox(
    "Ritmikai szűrő (Szószerkezet)", value=False,
    help="Csak azonos szószerkezetű találatok."
)

internal_rhyme = st.sidebar.checkbox(
    "Belső rímek keresése és kiemelése", value=True,
    help="Megtalálja és kiemeli a sorokon belüli rímelő részeket is."
)

cross_line = st.sidebar.checkbox(
    "Kereszt-soros rímek", value=False,
    help="Keres olyan rímeket, amik az egyik sor végén kezdődnek és a következő elején folytatódnak."
)

user_input = st.text_input("Írj be egy sort a rímek kereséséhez:", placeholder="pl. mindig egy nő meg a pénz")

if user_input:
    rhymes = find_rhymes(user_input, filtered_data, match_len, loose_match, rhythm_match, internal_rhyme, cross_line)
    
    highlighted_input = highlight_vowels(user_input)
    st.markdown(f"### Keresés: {highlighted_input}", unsafe_allow_html=True)
    st.subheader(f"{len(rhymes)} találat:")
    
    if rhymes:
        for idx, res in enumerate(rhymes):
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                if res["type"] == "single":
                    h_rhyme = highlight_vowels(res["line"], highlight_mask=res["mask"])
                    st.markdown(f"**{h_rhyme}**", unsafe_allow_html=True)
                    target_line = res["line"]
                else:
                    h1 = highlight_vowels(res["line1"], highlight_mask=res["mask1"])
                    h2 = highlight_vowels(res["line2"], highlight_mask=res["mask2"])
                    st.markdown(f"**{h1}** / **{h2}** (Kereszt-rím)", unsafe_allow_html=True)
                    target_line = res["line1"]
                
                exp = st.expander("Szövegkörnyezet")
            
            with col2:
                st.write(f"&nbsp;\n\n{res['strength']} magánhangzó")
            
            with exp:
                try:
                    occ_idx = -1
                    for i, line in enumerate(full_data):
                        if line.strip() == target_line:
                            occ_idx = i
                            break
                    if occ_idx != -1:
                        start = max(0, occ_idx - 2)
                        end = min(len(full_data), occ_idx + 4)
                        context = full_data[start:end]
                        st.markdown("---")
                        for context_line in context:
                            c_strip = context_line.strip()
                            if c_strip == target_line or (res["type"] == "cross" and c_strip == res["line2"]):
                                st.markdown(f"**-> {context_line}**")
                            else:
                                st.text(f"   {context_line}")
                except:
                    st.info("Környezet nem elérhető.")
    else:
        st.info("Nincs találat.")
else:
    st.markdown("Írj be valamit a kezdéshez!")
