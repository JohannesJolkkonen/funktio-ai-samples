import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

st.title("Evaluation Leaderboard")


def load_eval_results() -> list[dict]:
    dir_path = "eval_results"
    eval_results = os.listdir(dir_path)
    evals = []
    # Download blob content
    for file in eval_results:
        if file.endswith("csv"):
            print(f"{dir_path}/{file}")
            df = pd.read_csv(f"{dir_path}/{file}")
            evals.append(
                {
                    "id": file,
                    "results": df,
                }
            )

    return evals


def highlight_cells(val):
    if val <= 0.5:
        red = 255
        green = int(255 * (val / 0.5))
        color = f"rgb({red}, {green}, 0)"
    else:
        green = 255
        red = 255 - int(255 * ((val / 0.5) / 0.5))
        color = f"rgb({red}, {green}, 0)"

    return f"background-color: {color}"


def run_ragas_dashboard():
    evals = load_eval_results()
    for e in evals:
        st.subheader(e.get("id"))
        col1, col2, col3, col4 = st.columns(4)
        results = e.get("results")
        correctness = results["answer_correctness"].mean()
        col1.metric(
            "Records",
            f"{len(results)}",
        )
        if correctness <= 0.5:
            col2.metric(
                "🟧 Answer Correctness",
                round(results["answer_correctness"].mean(), 2),
            )
        elif correctness < 0.75:
            col2.metric(
                "🟨 Answer Correctness",
                round(results["answer_correctness"].mean(), 2),
            )
        else:
            col2.metric(
                "🟩 Answer Correctness",
                round(results["answer_correctness"].mean(), 2),
            )

        col3.metric(
            "Avg Token Consumption",
            f"{round(results['token_usage'].mean() / 1000, 2)}k",
        )
        col4.metric(
            "Avg Latency",
            f"{round(results['latencies'].mean(), 2)}s",
        )
        with st.expander("See evaluation details"):
            st.dataframe(
                results[
                    [
                        "question",
                        "answer",
                        "ground_truth",
                        "answer_correctness",
                        "latencies",
                        "token_usage",
                    ]
                ]
            )


if __name__ == "__main__":
    run_ragas_dashboard()
