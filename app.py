import streamlit as st
import pandas as pd
from functools import partial
import random

@st.cache_data
def load_data():
    return pd.read_csv('data/master.csv')

def reveal_answer():
    st.session_state.show_answer = True

def mark_performance(word, result):
    st.session_state.performance.append((word, result))
    
    # If wrong, add this card back to the review queue
    if result == "wrong":
        current_card = st.session_state.words.iloc[st.session_state.index]
        # Insert the card at a random position later in the deck (between current position + 3 and end of deck)
        if len(st.session_state.words) > st.session_state.index + 3:
            insert_position = random.randint(st.session_state.index + 3, len(st.session_state.words) - 1)
            # Create a copy of the card
            card_to_reinsert = current_card.copy()
            # Add the card back to the deck at the random position
            st.session_state.words = pd.concat([
                st.session_state.words.iloc[:insert_position],
                pd.DataFrame([card_to_reinsert]),
                st.session_state.words.iloc[insert_position:]
            ]).reset_index(drop=True)
        else:
            # If we're near the end, just append to the end
            st.session_state.words = pd.concat([
                st.session_state.words,
                pd.DataFrame([current_card])
            ]).reset_index(drop=True)
    
    st.session_state.index += 1
    st.session_state.show_answer = False

def main():
    st.title("In Bocca al Lupo 🐺🇮🇹")
    st.markdown("---")
    st.markdown(
        "<style> .main { padding: 20px; text-align: center; } </style>",
        unsafe_allow_html=True
    )

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

    # ── Load & shuffle once ──
    data = load_data()
    if 'words' not in st.session_state:
        st.session_state.words = data.sample(frac=1).reset_index(drop=True)

    # ── Initialize other state ──
    st.session_state.setdefault('index', 0)
    st.session_state.setdefault('show_answer', False)
    st.session_state.setdefault('performance', [])

    words = st.session_state.words
    idx = st.session_state.index

    # ── End of deck ──
    if idx >= len(words):
        st.success("🎉 You've gone through all the cards!")
        perf_df = pd.DataFrame(
            st.session_state.performance,
            columns=[direction.split(" → ")[0], "Result"]
        )
        # Calculate and display statistics
        total_cards = len(perf_df)
        correct_cards = len(perf_df[perf_df["Result"] == "right"])
        accuracy = correct_cards / total_cards * 100 if total_cards > 0 else 0
        
        st.markdown(f"**Final Score: {correct_cards}/{total_cards} ({accuracy:.1f}%)**")
        st.table(perf_df)
        
        if st.button("Start New Session"):
            st.session_state.words = data.sample(frac=1).reset_index(drop=True)
            st.session_state.index = 0
            st.session_state.performance = []
            st.session_state.show_answer = False
            st.experimental_rerun()
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
        st.button(
            "🔍 Mostra la risposta",
            key="show",
            on_click=reveal_answer,
            help=f"Clicca per mostrare la risposta"
        )

    # ── Feedback step ──
    else:
        st.markdown(
            f"<div style='font-size:20px; color:#555;'>{back_col}:</div>"
            f"<div style='font-size:28px; font-weight:bold; color:green; margin:10px 0;'>{back_value}</div>",
            unsafe_allow_html=True
        )

        # center the two feedback buttons
        blank1, middle, blank2 = st.columns([1, 2, 1])
        with middle:
            c1, c2 = st.columns(2, gap="small")
            with c1:
                st.button(
                    "✅ Corretto",
                    key="right",
                    use_container_width=True,
                    on_click=partial(mark_performance, front_value, "right"),
                    help="Crepi il lupo 🐺"
                )
            with c2:
                st.button(
                    "❌ Sbagliato",
                    key="wrong",
                    use_container_width=True,
                    help="Il lupo ti ha mangiato 🐺",
                    on_click=partial(mark_performance, front_value, "wrong")
                )

    st.markdown("---")

if __name__ == "__main__":
    main()