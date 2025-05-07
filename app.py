import streamlit as st
import pandas as pd
from functools import partial
import random
import plotly.express as px

@st.cache_data
def load_data():
    return pd.read_csv('data/master.csv')

def reveal_answer():
    st.session_state.show_answer = True

def mark_performance(word, translation, result):
    key = f"{word} → {translation}"
    stats = st.session_state.performance.get(key, {"right": 0, "wrong": 0})
    stats[result] += 1
    st.session_state.performance[key] = stats

    # If wrong, re-insert the card later
    if result == "wrong":
        current_card = st.session_state.words.iloc[st.session_state.index]
        if len(st.session_state.words) > st.session_state.index + 3:
            insert_position = random.randint(st.session_state.index + 3, len(st.session_state.words) - 1)
            card_to_reinsert = current_card.copy()
            st.session_state.words = pd.concat([
                st.session_state.words.iloc[:insert_position],
                pd.DataFrame([card_to_reinsert]),
                st.session_state.words.iloc[insert_position:]
            ]).reset_index(drop=True)
        else:
            st.session_state.words = pd.concat([
                st.session_state.words,
                pd.DataFrame([current_card])
            ]).reset_index(drop=True)

    st.session_state.index += 1
    st.session_state.show_answer = False

def main():
    st.title("In Bocca al Lupo 🐺🇮🇹")
    theme = st.radio("Theme:", ["Light", "Dark"], horizontal=True)
    st.session_state.setdefault("theme", theme)
    if theme == "Dark":
        dark_style = """
        <style>
        /* === GLOBAL DARK THEME === */
        html, body, .stApp {
            background-color: #1e1e1e !important;
            color: #f1f1f1 !important;
        }

        /* Radio labels, markdown, text, etc. */
        label, div[role="radiogroup"] > *, .markdown-text-container, .stMarkdown, h1, h2, h3, h4, h5, h6, p, span {
            color: #f1f1f1 !important;
        }

        /* Secondary/dimmed text */
        .css-1d391kg, .css-qrbaxs, .css-1v3fvcr, .css-1cpxqw2 {
            color: #ccc !important;
        }

        /* Buttons */
        button {
            background-color: #333 !important;
            color: #f1f1f1 !important;
            border: 1px solid #555 !important;
        }

        /* Progress bar fill */
        .stProgress > div > div > div > div {
            background-color: #aaa !important;
        }

        /* Word labels and answer */
        .word-label {
            color: #ccc !important;
        }
        .answer {
            color: #00ff88 !important;
            font-weight: bold;
        }

        /* === CUSTOM TOOLTIP === */
        .tooltip {
            position: relative;
            display: inline-block;
            cursor: pointer;
        }

        .tooltip .tooltiptext {
            visibility: hidden;
            width: max-content;
            background-color: #333;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 6px 10px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.85rem;
            white-space: nowrap;
        }

        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }

        /* Optional: Styled buttons inside tooltip wrappers */
        .flash-btn {
            padding: 8px 18px;
            font-size: 16px;
            border: none;
            background-color: #444;
            color: #fff;
            border-radius: 8px;
        }
        </style>
        """
        st.markdown(dark_style, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        "<style> .main { padding: 20px; text-align: center; } </style>",
        unsafe_allow_html=True
    )

    # Load data
    data = load_data()

    # Add a slider to select the number of words for the session
    max_words = len(data)
    num_words = st.slider(
        "Select number of words to study:",
        min_value=1,
        max_value=max_words,
        value=min(10, max_words)  # Default to 10 or max_words if less than 10
    )
    
    # Shuffle and select the number of words based on the slider
    if 'words' not in st.session_state or 'initial_sample' not in st.session_state or st.session_state.initial_sample != num_words:
        st.session_state.words = data.sample(n=num_words).reset_index(drop=True)
        st.session_state.index = 0  # Reset index for new session
        st.session_state.performance = {}  # Reset performance for new session
        st.session_state.initial_sample = num_words  # Track the initial sample size

    # ── Choose language pair ──
    language_pair = st.radio(
        "Select language pair:",
        options=["Italiano ↔ Tedesco", "Italiano ↔ Inglese"],
        key="language_pair_selector",
        index=0  # default to Italiano ↔ Tedesco
    )
    # store in state once so it survives reruns
    st.session_state.setdefault("language_pair", language_pair)
    # but if user changes it, overwrite
    if language_pair != st.session_state.language_pair:
        st.session_state.language_pair = language_pair
        # reset deck when language pair changes
        st.session_state.index = 0
        st.session_state.show_answer = False
        st.session_state.performance = [] 

    # ── Choose direction based on language pair ──
    if st.session_state.language_pair == "Italiano ↔ Tedesco":
        direction_options = ["Italiano → Tedesco", "Tedesco → Italiano"]
    else:
        direction_options = ["Italiano → Inglese", "Inglese → Italiano"]

    direction = st.radio(
        "Flashcard direction:",
        options=direction_options,
        key="direction_selector",
        index=0  # default to first option
    )
    # store in state once so it survives reruns
    st.session_state.setdefault("direction", direction)
    # but if user changes it, overwrite
    if direction != st.session_state.direction:
        st.session_state.direction = direction
        # reset deck when direction changes
        st.session_state.index = 0
        st.session_state.show_answer = False
        st.session_state.performance = []

    # ── Initialize other state ──
    st.session_state.setdefault('index', 0)
    st.session_state.setdefault('show_answer', False)

    words = st.session_state.words
    idx = st.session_state.index

    # ── End of deck ──
    if idx >= len(words):
        st.success("🎉 You've gone through all the cards!")

        # Create performance DataFrame from the dictionary
        perf_data = [
            {"Word": k, "Right": v["right"], "Wrong": v["wrong"]}
            for k, v in st.session_state.performance.items()
        ]
        perf_df = pd.DataFrame(perf_data).sort_values(by=["Wrong", "Right"], ascending=[False, True])

        # Compute overall stats
        total_right = sum(v["right"] for v in st.session_state.performance.values())
        total_wrong = sum(v["wrong"] for v in st.session_state.performance.values())
        total_attempts = total_right + total_wrong
        accuracy = total_right / total_attempts * 100 if total_attempts > 0 else 0

        st.markdown(f"**Final Score: {total_right}/{total_attempts} ({accuracy:.1f}%)**")
        st.markdown("### 📈 Word Performance")
        st.table(perf_df)


        if st.button("Start New Session"):
            st.session_state.words = data.sample(frac=1).reset_index(drop=True)
            st.session_state.index = 0
            st.session_state.performance = {}
            st.session_state.show_answer = False
            # Trigger a rerun by modifying a session state variable
            st.session_state['rerun'] = not st.session_state.get('rerun', False)
        return

    # ── Pick current card ──
    card = words.iloc[idx]
    if "Italiano → Tedesco" in direction or "Italiano → Inglese" in direction:
        front_col = "Italiano"
        back_col = "Tedesco" if "Tedesco" in direction else "Inglese"
        front_value = card['italian']
        back_value = card['german'] if "Tedesco" in direction else card['english']
    else:
        front_col = "Tedesco" if "Tedesco" in direction else "Inglese"
        back_col = "Italiano"
        front_value = card['german'] if "Tedesco" in direction else card['english']
        back_value = card['italian']

    # ── Display progress ──
    total_cards = len(words)
    st.progress(idx / total_cards)
    st.markdown(f"Card {idx + 1} of {total_cards}")

    # ── Show the prompt (front) ──
    st.markdown(
        f"<div style='font-size:20px; color:#555;'>{front_col}:</div>"
        f"<div style='font-size:28px; font-weight:bold; margin:10px 0;'>{front_value}</div>",
        unsafe_allow_html=True
    )

    # ── Show‐answer step ──
    if not st.session_state.show_answer:
        mostra_help = None if theme == "Dark" else "Clicca per mostrare la risposta"
        st.button(
            "🔍 Mostra la risposta",
            key="show",
            on_click=reveal_answer,
            help=mostra_help
        )

    # ── Feedback step ──
    else:
        st.markdown(
            f"<div style='font-size:20px; color:#555;'>{back_col}:</div>"
            f"<div style='font-size:28px; font-weight:bold; color:green; margin:10px 0;'>{back_value}</div>",
            unsafe_allow_html=True
        )
        # Disable tooltips in dark mode
        right_help = None if theme == "Dark" else "Crepi il lupo 🐺"
        wrong_help = None if theme == "Dark" else "Il lupo ti ha mangiato 🐺"
        # center the two feedback buttons
        blank1, middle, blank2 = st.columns([1, 2, 1])
        with middle:
            c1, c2 = st.columns(2, gap="small")
            with c1:
                st.button(
                    "✅ Corretto",
                    key="right",
                    use_container_width=True,
                    on_click=partial(mark_performance, front_value, back_value, "right"),
                    help=right_help
                )
            with c2:
                st.button(
                    "❌ Sbagliato",
                    key="wrong",
                    use_container_width=True,
                    on_click=partial(mark_performance, front_value, back_value, "wrong"),
                    help=wrong_help
                )

    st.markdown("---")

if __name__ == "__main__":
    main()