import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import re
import openai

# Application title with colored text
st.markdown(
    """
# RFM by <span style="color:dodgerblue">Keboola</span>
""",
    unsafe_allow_html=True,
)


# Function to assign categories based on R and F scores using regex
def assign_category(r, f):
    rfm_score = f"{r}{f}"
    categories = {
        "5[4-5]": "01. Champions",
        "[3-4][4-5]": "02. Loyal Customers",
        "[4-5][2-3]": "03. Potential Loyalists",
        "51": "04. Recent Customers",
        "41": "05. Promising",
        "33": "06. Need Attention",
        "3[1-2]": "07. About to Sleep",
        "[1-2][5]": "08. Can't Lose",
        "[1-2][3-4]": "09. At Risk",
        "2[1-2]": "10. Hibernating",
        "1[1-2]": "11. Lost"
    }
    for pattern, category in categories.items():
        if re.match(pattern, rfm_score):
            return category
    return "Uncategorized"


# Define category_order
category_order = [
    "01. Champions",
    "02. Loyal Customers",
    "03. Potential Loyalists",
    "04. Recent Customers",
    "05. Promising",
    "06. Need Attention",
    "07. About to Sleep",
    "08. Can't Lose",
    "09. At Risk",
    "10. Hibernating",
    "11. Lost",
]


# Function to recalculate RFM values based on parameters
def recalculate_rfm(rfm_df, recency_thresholds, frequency_thresholds, monetary_thresholds):
    rfm_df["R_rank"] = rfm_df["Recency"].apply(
        lambda x: next((5 - i for i, t in enumerate(recency_thresholds) if x <= t), 1)
    )

    def calculate_f_rank(frequency):
        for i, threshold in enumerate(frequency_thresholds, start=1):
            if frequency <= threshold:
                return 6 - i
        return 1

    rfm_df["F_rank"] = rfm_df["Frequency"].apply(calculate_f_rank)

    rfm_df["M_rank"] = rfm_df["AOS"].apply(
        lambda x: next((5 - i for i, t in enumerate(monetary_thresholds) if x >= t), 1)
    )

    rfm_df["RFM_Score"] = rfm_df["R_rank"].astype(str) + rfm_df["F_rank"].astype(str)

    rfm_df["Category"] = rfm_df.apply(
        lambda x: assign_category(x["R_rank"], x["F_rank"]), axis=1
    )

    return rfm_df


def main():
    st.markdown("<h1>RFM by <span style='color:dodgerblue'>Keboola</span></h1>", unsafe_allow_html=True)

    # Load and preprocess data
    csv_path = "rfm-data.csv"
    try:
        df = pd.read_csv(csv_path)
        df["date"] = pd.to_datetime(df["date"])

        start_date = st.sidebar.date_input("Start date", df["date"].min().date())
        end_date = st.sidebar.date_input("End date", df["date"].max().date())
        filtered_df = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]

        max_date = filtered_df["date"].max() + timedelta(days=1)
        rfm_df = (
            filtered_df.groupby("id").agg(
                Recency=("date", lambda x: (max_date - x.max()).days),
                Frequency=("date", lambda x: max((x.max() - x.min()).days / len(x), 1)),
                Monetary=("value", "sum")
            ).reset_index()
        )

        rfm_df["AOS"] = rfm_df.apply(lambda x: x["Monetary"] / x["Frequency"] if x["Frequency"] != 0 else 0, axis=1)

        # Initial RFM calculation
        recency_thresholds = [3, 10, 25, 66]
        frequency_thresholds = [13.6, 24.5, 38.8, 66.6]
        monetary_thresholds = [6841, 3079, 1573, 672]
        rfm_df = recalculate_rfm(rfm_df, recency_thresholds, frequency_thresholds, monetary_thresholds)

        # Streamlit UI Elements and Plots
        st.sidebar.markdown("### RFM Parameters")
        col1, col2, col3, col4 = st.sidebar.columns(4)
        with col1:
            r5 = int(st.text_input("R5", 3))
        with col2:
            r4 = int(st.text_input("R4", 10))
        with col3:
            r3 = int(st.text_input("R3", 25))
        with col4:
            r2 = int(st.text_input("R2", 66))

        st.sidebar.markdown("")
        with col1:
            f5 = float(st.text_input("F5", 13.6))
        with col2:
            f4 = float(st.text_input("F4", 24.5))
        with col3:
            f3 = float(st.text_input("F3", 38.8))
        with col4:
            f2 = float(st.text_input("F2", 66.6))

        st.sidebar.markdown("")
        with col1:
            m5 = float(st.text_input("M5", 6841))
        with col2:
            m4 = float(st.text_input("M4", 3079))
        with col3:
            m3 = float(st.text_input("M3", 1573))
        with col4:
            m2 = float(st.text_input("M2", 672))

        if "rfm_df" in locals():
            # Recalculate ranks based on updated parameters
            rfm_df = recalculate_rfm(rfm_df, [r5, r4, r3, r2], [f5, f4, f3, f2], [m5, m4, m3, m2])
            st.success("RFM segmentation updated!")

        st.markdown("### Number of Customers in Each Category")
        category_counts = (
            rfm_df["Category"].value_counts().reindex(category_order).reset_index()
        )
        category_counts.columns = ["Category", "Number of Customers"]
        st.dataframe(category_counts)

        st.markdown("### RFM Data")
        st.dataframe(rfm_df.head())

        fig = px.scatter_3d(
            rfm_df,
            x="Recency",
            y="Frequency",
            z="Monetary",
            color="Category",
            title="3D Scatter Plot of Recency, Frequency, and Monetary",
            height=800,
            category_orders={"Category": category_order},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig.update_traces(marker=dict(size=5))
        st.plotly_chart(fig)

        st.markdown("### Pareto Chart")
        filtered_category_df_sorted = rfm_df.sort_values("Monetary", ascending=False)
        aggregated_df = (
            filtered_category_df_sorted.groupby("Category").agg({"Monetary": "sum"}).reset_index()
        )
        total_revenue = aggregated_df["Monetary"].sum()
        aggregated_df["Percentage of Total Revenue"] = 100 * aggregated_df["Monetary"] / total_revenue

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=aggregated_df["Category"],
                y=aggregated_df["Monetary"],
                name="Monetary",
                marker_color=px.colors.qualitative.Pastel[:11],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=aggregated_df["Category"],
                y=aggregated_df["Percentage of Total Revenue"],
                name="Percentage of Total Revenue",
                yaxis="y2",
                mode="lines+markers",
                marker=dict(color="red", size=8, symbol="circle"),
            )
        )
        fig.update_layout(
            title="Pareto Chart",
            xaxis_title="Category",
            yaxis=dict(title="Monetary", side="left"),
            yaxis2=dict(
                title="Percentage of Total Revenue",
                side="right",
                overlaying="y",
                range=[0, 110],
            ),
            legend=dict(
                x=0.1,
                y=1.1,
                bgcolor="rgba(255,255,255,0)",
                bordercolor="rgba(255,255,255,0)",
            ),
        )
        st.plotly_chart(fig)

        st.markdown("### Heatmap of Recency and Frequency (Average Order Size)")
        heatmap_data = rfm_df.pivot_table(
            index="R_rank", columns="F_rank", values="AOS", aggfunc="mean"
        ).fillna(0)
        fig = px.imshow(
            heatmap_data,
            title="Heatmap of Recency and Frequency (Average Order Size)",
            color_continuous_scale="Blues",
            labels={"color": "Average Order Size"},
        )
        fig.update_layout(xaxis_title="Frequency", yaxis_title="Recency")
        st.plotly_chart(fig)

        st.markdown("## Recommended Strategy")
        def get_recommendation():
            openai.api_key = st.secrets["OPENAI_TOKEN"]
            filtered_data_str = rfm_df.to_csv(index=False)
            prompt = (
                f"Based on the RFM analysis, provide a detailed and comprehensive description of the customers across all 11 segments. "
                f"The data includes customer information categorized by RFM segments. Analyze all segments together, highlighting the differences and similarities among them. Group segments with similar patterns and provide a combined analysis. Follow this detailed structure:\n\n"
                f"1. Segment Overview:\n"
                f"    a. Provide an overall description of the groups of segments with similar patterns.\n"
                f"    b. Include the number of customers in each group.\n"
                f"    c. Mention key metrics such as Recency, Frequency, and Monetary values for each group.\n"
                f"    d. Highlight differences and similarities among the groups based on these metrics.\n\n"
                f"2. Customer Behavior:\n"
                f"    a. Analyze the typical behavior of customers in each group.\n"
                f"    b. Provide insights based on the data provided.\n"
                f"    c. Compare and contrast the behavior of customers across different groups.\n\n"
                f"3. Purchasing Patterns:\n"
                f"    a. Highlight any notable patterns or trends in purchasing behavior within each group.\n"
                f"    b. Identify any seasonal or recurring trends.\n"
                f"    c. Discuss how purchasing patterns vary between groups.\n\n"
                f"4. Customer Value:\n"
                f"    a. Discuss the overall value these customers bring to the business.\n"
                f"    b. Include metrics such as average order size and total revenue contribution for each group.\n"
                f"    c. Compare the value of different groups to each other.\n"
                f"    d. Identify which groups are the most and least valuable.\n\n"
                f"5. Engagement Recommendations:\n"
                f"    a. Provide 2 key recommendations on how to engage with each customer group.\n"
                f"    b. Ensure the recommendations are actionable and data-driven.\n"
                f"    c. Discuss how engagement strategies should differ between groups.\n\n"
                f"To ensure the analysis is thorough and accurate, perform the following evaluation (eval) steps for each task:\n"
                f"    - Eval 1: Verify the accuracy of the data described in the segment overview.\n"
                f"    - Eval 2: Cross-check the customer behavior analysis with the provided data.\n"
                f"    - Eval 3: Ensure the purchasing patterns are correctly identified and described.\n"
                f"    - Eval 4: Confirm the customer value metrics are accurately calculated and compared.\n"
                f"    - Eval 5: Assess the feasibility and relevance of the engagement recommendations.\n\n"
                f"Here is the data:\n{filtered_data_str}"
            )

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=150,
                )
                return response.choices[0].message["content"].strip()
            except openai.error.RateLimitError:
                st.error(
                    "You have exceeded your OpenAI API quota. Please check your plan and billing details."
                )
                return None
            except Exception as e:
                st.error(f"Error with OpenAI request: {e}")
                return None

        try:
            openai_token = st.secrets["OPENAI_TOKEN"]
            st.write("OpenAI token loaded successfully.")

            recommendation = get_recommendation()
            if recommendation:
                st.markdown(recommendation)
            else:
                st.write(
                    "No recommendation received. This feature may be temporarily unavailable due to API quota limits."
                )
        except KeyError as e:
            st.error(f"Error loading OpenAI token: {e}")
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.write("This feature is temporarily unavailable due to API quota limits.")

    except FileNotFoundError:
        st.error(f"File not found at path {csv_path}.")
    except Exception as e:
        st.error(f"An error occurred while loading the file: {e}")


if __name__ == "__main__":
    main()
