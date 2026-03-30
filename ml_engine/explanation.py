import pandas as pd


def generate_financial_explanation(df):

    explanation = []

    # -------------------
    # INCOME CONTRIBUTION
    # -------------------
    income_df = df[df["transaction_type"] == "income"]

    income_category = income_df.groupby("category")["amount"].sum()
    total_income = income_category.sum()

    income_contribution = {}

    for category, value in income_category.items():

        percentage = round((value / total_income) * 100, 2)

        income_contribution[category] = {
            "amount": value,
            "percentage": percentage
        }

        explanation.append(
            f"{category} contributed {percentage}% of total income this month."
        )

    # -------------------
    # EXPENSE CONTRIBUTION
    # -------------------
    expense_df = df[df["transaction_type"] == "expense"]

    expense_category = expense_df.groupby("category")["amount"].sum()
    total_expense = expense_category.sum()

    expense_contribution = {}

    for category, value in expense_category.items():

        percentage = round((value / total_expense) * 100, 2)

        expense_contribution[category] = {
            "amount": value,
            "percentage": percentage
        }

        explanation.append(
            f"{category} contributed {percentage}% of total expenses this month."
        )

    return income_contribution, expense_contribution, explanation