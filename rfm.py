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


# Load CSV file
csv_path = "rfm-data.csv"
try:
    df = pd.read_csv(csv_path)

    # Convert 'date' column to datetime type
    df["date"] = pd.to_datetime(df["date"])

    # Create interactive date selection fields in the sidebar
    start_date = st.sidebar.date_input("Start date", df["date"].min().date())
    end_date = st.sidebar.date_input("End date", df["date"].max().date())

    # Filter data based on selected dates
    filtered_df = df[
        (df["date"] >= pd.to_datetime(start_date))
        & (df["date"] <= pd.to_datetime(end_date))
    ]

    # Calculate RFM values
    max_date = filtered_df["date"].max() + timedelta(days=1)
    rfm_df = (
        filtered_df.groupby("id")
        .agg(
            {
                "date": lambda x: (
                    max_date - x.max()
                ).days,  # Recency: days since last purchase
                "id": "count",  # Temporary Frequency: count of purchases
                "value": "sum",  # Monetary: total value of purchases
            }
        )
        .rename(
            columns={
                "date": "Recency",
                "id": "Temp_Frequency",  # Temporary frequency, count of purchases
                "value": "Monetary",
            }
        )
        .reset_index()
    )

    # Calculate Frequency as number of days between the first and last purchase / number of purchases
    frequency_df = (
        filtered_df.groupby("id")
        .agg(
            {
                "date": lambda x: max(
                    (x.max() - x.min()).days / len(x), 1
                )  # Ensure frequency is at least 1
            }
        )
        .rename(columns={"date": "Frequency"})
        .reset_index()
    )

    # Merge the frequency calculation back into the RFM dataframe
    rfm_df = rfm_df.drop(columns=["Temp_Frequency"]).merge(frequency_df, on="id")

    # Calculate Average Order Size (AOS)
    rfm_df["AOS"] = rfm_df.apply(
        lambda x: (
            x["Monetary"] / x["Frequency"]
            if pd.notna(x["Frequency"]) and x["Frequency"] != 0
            else 0
        ),
        axis=1,
    )

    # Initial RFM calculation with default parameters
    recency_thresholds = [3, 10, 25, 66]
    frequency_thresholds = [13.6, 24.5, 38.8, 66.6]
    monetary_thresholds = [6841, 3079, 1573, 672]

    rfm_df = recalculate_rfm(rfm_df, recency_thresholds, frequency_thresholds, monetary_thresholds)

    # CSS for styling buttons
    st.markdown(
        """
    <style>
    .stButton > button {
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .custom-button {
        background-color: lightgray;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .stMarkdown > div > div > div > div > div:first-child > div {
        display: flex;
        flex-wrap: wrap;
    }
    .stMarkdown > div > div > div > div > div:first-child > div > div {
        flex-grow: 0;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Create buttons
    buttons = [
        ("About Customers", "About Customers"),
        ("About Segmentation", "About Segmentation"),
        ("RFM Tuning", "RFM Tuning"),
        ("Recommended Strategy", "TO DO Analysis"),
    ]

    selected_button = None

    # Create columns for buttons to be displayed in rows
    row1 = st.columns(4)

    rows = [row1]

    for row, button_group in zip(rows, [buttons]):
        for col, (button_text, button_value) in zip(row, button_group):
            if col.button(button_text, key=button_value):
                selected_button = button_value

    # Display the graph based on the selected button
    if selected_button is None:
        selected_button = "About Segmentation"

    # Filter data based on the selected categories
    filtered_category_df = rfm_df

    if selected_button == "About Customers":
        # Add 'Category' column to filtered_df
        filtered_df = filtered_df.merge(rfm_df[["id", "Category"]], on="id", how="left")

        # Monthly revenue over time with stacked bar plot by category
        monthly_revenue = (
            filtered_df.set_index("date").resample("M")["value"].sum().reset_index()
        )

        # Ensure all categories are present
        category_monthly_revenue = (
            filtered_df.groupby([pd.Grouper(key="date", freq="M"), "Category"])["value"]
            .sum()
            .unstack()
            .fillna(0)
        )
        for category in category_order:
            if category not in category_monthly_revenue.columns:
                category_monthly_revenue[category] = 0

        # Sort columns by category_order
        category_monthly_revenue = category_monthly_revenue[category_order]

        fig3 = go.Figure()
        fig3.add_trace(
            go.Scatter(
                x=monthly_revenue["date"],
                y=monthly_revenue["value"],
                mode="lines",
                name="Total Revenue",
            )
        )

        for category in category_order:
            fig3.add_trace(
                go.Bar(
                    x=category_monthly_revenue.index,
                    y=category_monthly_revenue[category],
                    name=category,
                    marker_color=px.colors.qualitative.Pastel[
                        category_order.index(category)
                    ],
                )
            )

        fig3.update_layout(
            barmode="stack",
            title="Monthly Revenue Over Time",
            xaxis_title="Date",
            yaxis_title="Revenue",
            legend=dict(traceorder="normal"),
        )
        st.plotly_chart(fig3)
        st.markdown(
            "<p style='font-size: small;'>Revenue trend over time.</p>",
            unsafe_allow_html=True,
        )

        # Average Order Size by Category
        rfm_df["AOS"] = rfm_df["Monetary"] / rfm_df["Frequency"]
        aos_df = rfm_df.groupby("Category").agg({"AOS": "mean"}).reset_index()
        fig = px.bar(
            aos_df,
            x="Category",
            y="AOS",
            title="Average Order Size by Category",
            color="Category",
            category_orders={"Category": category_order},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig)

        fig2 = px.box(
            filtered_category_df,
            y="Recency",
            title="Boxplot Recency",
            color="Category",
            category_orders={"Category": category_order},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig2)
        st.markdown(
            "<p style='font-size: small;'>Recency shows how recently each customer made a purchase.</p>",
            unsafe_allow_html=True,
        )

        fig2 = px.box(
            filtered_category_df,
            y="Frequency",
            title="Boxplot Frequency",
            color="Category",
            category_orders={"Category": category_order},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig2)
        st.markdown(
            "<p style='font-size: small;'>Frequency shows how often each customer makes a purchase.</p>",
            unsafe_allow_html=True,
        )

        # Filter out extreme values
        filtered_monetary_df = filtered_category_df[
            filtered_category_df["Monetary"]
            <= filtered_category_df["Monetary"].quantile(0.95)
        ]
        fig2 = px.box(
            filtered_monetary_df,
            y="Monetary",
            title="Boxplot Monetary",
            color="Category",
            category_orders={"Category": category_order},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig2)
        st.markdown(
            "<p style='font-size: small;'>Monetary shows how much money each customer spends.</p>",
            unsafe_allow_html=True,
        )

    if selected_button == "About Segmentation":
        # Customizing the display for "About Segmentation"
        fig1 = px.treemap(
            rfm_df,
            path=["Category"],
            values="Monetary",
            color="Category",
            color_discrete_sequence=px.colors.qualitative.Pastel,  # Ensuring same color scheme
            title="Customer Distribution by RFM Categories (Monetary)",
        )

        # Calculate percentage of total monetary value for each category
        category_percentage = (
            rfm_df.groupby("Category")["Monetary"].sum()
            / rfm_df["Monetary"].sum()
            * 100
        )
        category_percentage = category_percentage.round(2).astype(str) + "%"
        fig1.data[0].texttemplate = (
            "%{label}<br>%{value}<br>" + category_percentage[fig1.data[0].ids].values
        )
        st.plotly_chart(fig1)

        # Calculate the number of customers in each category
        category_counts = (
            rfm_df["Category"].value_counts().reindex(category_order).reset_index()
        )
        category_counts.columns = ["Category", "Number of Customers"]

        # Calculate percentage of total customers for each category
        total_customers = category_counts["Number of Customers"].sum()
        category_counts["Percentage"] = (
            category_counts["Number of Customers"] / total_customers * 100
        ).round(2).astype(str) + "%"

        # Display the treemap with the number of customers in each category
        fig2 = px.treemap(
            category_counts,
            path=["Category"],
            values="Number of Customers",
            color="Category",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            title="Customer Distribution by RFM Categories (Customer Count)",
        )
        fig2.data[0].texttemplate = "%{label}<br>%{value}<br>%{customdata[0]}<br>"
        fig2.data[0].customdata = category_counts[["Percentage"]].values
        st.plotly_chart(fig2)

    if selected_button == "RFM Tuning":
        with st.sidebar.expander("RFM Parameters", expanded=True):
            st.markdown("### Recency Parameters")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                r5 = int(st.text_input("R5", 3))
            with col2:
                r4 = int(st.text_input("R4", 10))
            with col3:
                r3 = int(st.text_input("R3", 25))
            with col4:
                r2 = int(st.text_input("R2", 66))

            st.markdown("")
            with col1:
                f5 = float(st.text_input("F5", 13.6))
            with col2:
                f4 = float(st.text_input("F4", 24.5))
            with col3:
                f3 = float(st.text_input("F3", 38.8))
            with col4:
                f2 = float(st.text_input("F2", 66.6))

            st.markdown("")
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
            rfm_df = recalculate_rfm(
                rfm_df, [r5, r4, r3, r2], [f5, f4, f3, f2], [m5, m4, m3, m2]
            )

            st.success("RFM segmentation updated!")

        # Display the number of customers in each category
        st.markdown("### Number of Customers in Each Category")
        category_counts = (
            rfm_df["Category"].value_counts().reindex(category_order).reset_index()
        )
        category_counts.columns = ["Category", "Number of Customers"]
        st.dataframe(category_counts)

        # Display the updated RFM dataframe
        st.dataframe(rfm_df.head())

        fig = px.scatter_3d(
            filtered_category_df,
            x="Recency",
            y="Frequency",
            z="Monetary",
            color="Category",
            title="3D Scatter Plot of Recency, Frequency, and Monetary",
            height=800,
            category_orders={"Category": category_order},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )  # Increase height for better visualization
        fig.update_traces(marker=dict(size=5))  # Adjust marker size
        st.plotly_chart(fig)

        # Pareto Chart
        filtered_category_df_sorted = filtered_category_df.sort_values(
            "Monetary", ascending=False
        )

        # Aggregating data into 11 categories for readability
        aggregated_df = (
            filtered_category_df_sorted.groupby("Category")
            .agg({"Monetary": "sum"})
            .reset_index()
        )

        # Calculate the percentage of total revenue for each category
        total_revenue = aggregated_df["Monetary"].sum()
        aggregated_df["Percentage of Total Revenue"] = (
            100 * aggregated_df["Monetary"] / total_revenue
        )

        fig = go.Figure()

        # Bar chart for Monetary
        fig.add_trace(
            go.Bar(
                x=aggregated_df["Category"],
                y=aggregated_df["Monetary"],
                name="Monetary",
                marker_color=px.colors.qualitative.Pastel[:11],
            )
        )

        # Line chart for Percentage of Total Revenue
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

        # Create a secondary y-axis
        fig.update_layout(
            title="Pareto Chart",
            xaxis_title="Category",
            yaxis=dict(title="Monetary", side="left"),
            yaxis2=dict(
                title="Percentage of Total Revenue",
                side="right",
                overlaying="y",
                range=[0, 110],  # Extend the range a bit beyond 100%
            ),
            legend=dict(
                x=0.1,
                y=1.1,
                bgcolor="rgba(255,255,255,0)",
                bordercolor="rgba(255,255,255,0)",
            ),
        )

        st.plotly_chart(fig)
        st.markdown(
            "<p style='font-size: small;'>Pareto chart shows the percentage contribution of each customer category to the total revenue.</p>",
            unsafe_allow_html=True,
        )

        # Heatmap R & F
        # Calculate average order size (AOS) for each R and F combination
        heatmap_data = rfm_df.pivot_table(
            index="R_rank", columns="F_rank", values="AOS", aggfunc="mean"
        ).fillna(0)

        # Create the heatmap
        fig = px.imshow(
            heatmap_data,
            title="Heatmap of Recency and Frequency (Average Order Size)",
            color_continuous_scale="Blues",
            labels={"color": "Average Order Size"},
        )

        # Update layout to match the provided example
        fig.update_layout(xaxis_title="Frequency", yaxis_title="Recency")

        st.plotly_chart(fig)

    if selected_button == "TO DO Analysis":
        st.markdown("## Recommended Strategy")
    
        # Function to get recommendation from OpenAI
        def get_recommendation():
            try:
                openai.api_key = st.secrets["OPENAI_TOKEN"]
                st.write("OpenAI token loaded successfully.")
            except KeyError as e:
                st.error(f"Error loading OpenAI token: {e}")
                return None
    
            # Convert the filtered data frame to a CSV string
            filtered_data_str = filtered_category_df.head(100).to_csv(index=False)  # Send only first 100 rows
    
            prompt = (
                f"Based on the RFM analysis, provide a detailed and comprehensive description of the customers across all 11 segments. You are data analyst with perfect business feeling. "
                f"Analyze each segment individually, following this specific category order and structure:\n\n"
                
                f"Champions:\n"
                f"Customer Value:\n"
                f"    1 key sentence about this category business\n"
                f"Engagement Recommendations:\n"
                f"    Provide 2 key recommendations on how to engage with Champions.\n\n"
                
                f"Loyal Customers:\n"
                f"Customer Value:\n"
                f"    1 key sentence about this category business\n"
                f"Engagement Recommendations:\n"
                f"    Provide 2 key recommendations on how to engage with Loyal Customers.\n\n"
                
                f"Potential Loyalists:\n"
                f"Customer Value:\n"
                f"    1 key sentence about this category business\n"
                f"Engagement Recommendations:\n"
                f"    Provide 2 key recommendations on how to engage with Potential Loyalists.\n\n"
                
                f"Recent Customers:\n"
                f"Customer Value:\n"
                f"    1 key sentence about this category business\n"
                f"Engagement Recommendations:\n"
                f"    Provide 2 key recommendations on how to engage with Recent Customers.\n\n"
                
                f"Promising:\n"
                f"Customer Value:\n"
                f"    1 key sentence about this category business\n"
                f"Engagement Recommendations:\n"
                f"    Provide 2 key recommendations on how to engage with Promising customers.\n\n"
                
                f"Need Attention:\n"
                f"Customer Value:\n"
                f"    1 key sentence about this category business\n"
                f"Engagement Recommendations:\n"
                f"    Provide 2 key recommendations on how to engage with customers who Need Attention.\n\n"
                
                f"About to Sleep:\n"
                f"Customer Value:\n"
                f"    1 key sentence about this category business\n"
                f"Engagement Recommendations:\n"
                f"    Provide 2 key recommendations on how to engage with customers who are About to Sleep.\n\n"
                
                f"Can't Lose:\n"
                f"Customer Value:\n"
                f"    1 key sentence about this category business\n"
                f"Engagement Recommendations:\n"
                f"    Provide 2 key recommendations on how to engage with customers who Can't Lose.\n\n"
                
                f"At Risk:\n"
                f"Customer Value:\n"
                f"    1 key sentence about this category business\n"
                f"Engagement Recommendations:\n"
                f"    Provide 2 key recommendations on how to engage with customers who are At Risk.\n\n"
                
                f"Hibernating:\n"
                f"Customer Value:\n"
                f"    1 key sentence about this category business\n"
                f"Engagement Recommendations:\n"
                f"    Provide 2 key recommendations on how to engage with Hibernating customers.\n\n"
                
                f"Lost:\n"
                f"Customer Value:\n"
                f"    1 key sentence about this category business\n"
                f"Engagement Recommendations:\n"
                f"    Provide 2 key recommendations on how to engage with Lost customers.\n\n"

                f"! Make all names of Category bold\n"
                f"! Make all names like customer value and engagement recommendations bold\n"
                f"! Didnt use word RFM skore\n"
                f"! Follow the structure\n"

                f"Here is the data:\n{filtered_data_str}"
            )



    
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-16k",
                    messages=[
                        {"role": "system", "content": "You are a data analyst."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=1000,  # Increase the number of max tokens
                    temperature=0.7,  # Adjust the temperature for more creative responses
                )
                # Kontrola struktury odpovědi
                if 'choices' in response and len(response['choices']) > 0:
                    return response['choices'][0]['message']['content'].strip()
                else:
                    st.error("Unexpected API response structure")
                    return None
            except openai.error.RateLimitError:
                st.error(
                    "You have exceeded your OpenAI API quota. Please check your plan and billing details."
                )
                return None
            except openai.error.PermissionError:
                st.error(
                    "You have insufficient permissions for this operation. Please check your API key permissions."
                )
                return None
            except Exception as e:
                st.error(f"Error with OpenAI request: {e}")
                return None
    
        try:
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
