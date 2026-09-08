import os
import requests
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

APP_NAME = "Expense Tracker"
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_URL = os.getenv("API_URL", f"http://{API_HOST}:{API_PORT}").rstrip("/")

def api_request(method, endpoint, token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.request(method, API_URL + endpoint, headers=headers, timeout=20, **kwargs)
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise RuntimeError(str(detail))
        return response.json()
    except requests.RequestException as error:
        raise RuntimeError(f"FastAPI is not available.\n\nExpected backend: {API_URL}\n\n{error}")

def money(value):
    return f"₹{float(value):,.2f}"

def run_streamlit_app():
    # STREAMLIT CONFIGURATION
    # ============================================================

    st.set_page_config(
        page_title=APP_NAME,
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded",
    )


    # ============================================================
    # CUSTOM CSS
    # ============================================================

    st.markdown(
        """
        <style>

        .main-title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0;
        }

        .subtitle {
            color: #777;
            font-size: 1.05rem;
            margin-bottom: 25px;
        }

        div[data-testid="stMetric"] {
            border: 1px solid rgba(128,128,128,.2);
            border-radius: 14px;
            padding: 18px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


    # ============================================================
    # SESSION STATE
    # ============================================================

    if "token" not in st.session_state:

        st.session_state.token = None


    if "user" not in st.session_state:

        st.session_state.user = None


    # ============================================================
    # LOGOUT
    # ============================================================

    def logout():

        st.session_state.token = None

        st.session_state.user = None

        st.rerun()


    # ============================================================
    # LOGIN / REGISTER SCREEN
    # ============================================================

    if not st.session_state.token:

        st.markdown(
            '<div class="main-title">'
            '💰 Expense Tracker'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="subtitle">'
            'Track your money. Understand your spending. '
            'Build better financial habits.'
            '</div>',
            unsafe_allow_html=True,
        )

        left, center, right = st.columns(
            [1, 1.2, 1]
        )

        with center:

            login_tab, register_tab = st.tabs(
                [
                    "🔐 Login",
                    "📝 Create Account",
                ]
            )

            # ----------------------------------------------------
            # LOGIN
            # ----------------------------------------------------

            with login_tab:

                with st.form(
                    "login_form"
                ):

                    email = st.text_input(
                        "Email",
                        placeholder="you@example.com",
                    )

                    password = st.text_input(
                        "Password",
                        type="password",
                    )

                    submitted = st.form_submit_button(
                        "Login",
                        use_container_width=True,
                    )

                    if submitted:

                        try:

                            result = api_request(
                                "POST",
                                "/auth/login",
                                json={
                                    "email": email,
                                    "password": password,
                                },
                            )

                            st.session_state.token = (
                                result[
                                    "access_token"
                                ]
                            )

                            st.session_state.user = (
                                result["user"]
                            )

                            st.rerun()

                        except RuntimeError as error:

                            st.error(
                                str(error)
                            )

            # ----------------------------------------------------
            # REGISTER
            # ----------------------------------------------------

            with register_tab:

                with st.form(
                    "register_form"
                ):

                    name = st.text_input(
                        "Full Name",
                        placeholder="Your name",
                    )

                    email = st.text_input(
                        "Email",
                        placeholder="you@example.com",
                        key="register_email",
                    )

                    password = st.text_input(
                        "Password",
                        type="password",
                        help="Minimum 6 characters",
                    )

                    confirm_password = st.text_input(
                        "Confirm Password",
                        type="password",
                    )

                    submitted = st.form_submit_button(
                        "Create Account",
                        use_container_width=True,
                    )

                    if submitted:

                        if password != confirm_password:

                            st.error(
                                "Passwords do not match."
                            )

                        elif len(password) < 6:

                            st.error(
                                "Password must be at least 6 characters."
                            )

                        else:

                            try:

                                result = api_request(
                                    "POST",
                                    "/auth/register",
                                    json={
                                        "name": name,
                                        "email": email,
                                        "password": password,
                                    },
                                )

                                st.session_state.token = (
                                    result[
                                        "access_token"
                                    ]
                                )

                                st.session_state.user = (
                                    result["user"]
                                )

                                st.rerun()

                            except RuntimeError as error:

                                st.error(
                                    str(error)
                                )

        st.stop()


    # ============================================================

    # AUTHENTICATED APPLICATION
    # ============================================================

    token = st.session_state.token

    user = st.session_state.user


    # ============================================================
    # LOAD CATEGORIES
    # ============================================================

    try:

        categories_data = api_request(
            "GET",
            "/categories",
            token,
        )

    except RuntimeError as error:

        st.error(
            str(error)
        )

        st.stop()


    cat_by_name = {
        item["name"]: item
        for item in categories_data
    }

    cat_by_id = {
        item["id"]: item
        for item in categories_data
    }


    # ============================================================
    # SIDEBAR
    # ============================================================

    with st.sidebar:

        st.title("💰 Finance")

        st.caption(
            f"Welcome, {user['name']}"
        )

        st.divider()

        page = st.radio(
            "Navigation",
            [
                "📊 Dashboard",
                "💸 Expenses",
                "💵 Income",
                "🎯 Budgets",
                "📈 Reports",
            ],
        )

        st.divider()

        st.caption(
            user["email"]
        )

        if st.button(
            "🚪 Logout",
            use_container_width=True,
        ):

            logout()


    # ============================================================
    # DASHBOARD
    # ============================================================

    if page == "📊 Dashboard":

        st.title(
            "📊 Dashboard"
        )

        try:

            data = api_request(
                "GET",
                "/dashboard",
                token,
            )

        except RuntimeError as error:

            st.error(
                str(error)
            )

            st.stop()

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "💵 Total Income",
            money(
                data["total_income"]
            ),
        )

        c2.metric(
            "💸 Total Expenses",
            money(
                data["total_expenses"]
            ),
        )

        c3.metric(
            "💰 Balance",
            money(
                data["balance"]
            ),
        )

        c4.metric(
            "📅 This Month",
            money(
                data["month_expenses"]
            ),
        )

        st.divider()

        left, right = st.columns(
            [1.5, 1]
        )

        with left:

            st.subheader(
                "📊 This Month's Spending"
            )

            breakdown = data[
                "category_breakdown"
            ]

            if breakdown:

                chart_df = pd.DataFrame(
                    breakdown
                )

                chart_df["label"] = (
                    chart_df["icon"]
                    + " "
                    + chart_df["category"]
                )

                fig = px.bar(
                    chart_df,
                    x="label",
                    y="amount",
                    text_auto=".2f",
                )

                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="Amount (₹)",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

            else:

                st.info(
                    "No expenses this month."
                )

        with right:

            st.subheader(
                "⚡ Quick Add Expense"
            )

            with st.form(
                "quick_expense"
            ):

                amount = st.number_input(
                    "Amount (₹)",
                    min_value=0.01,
                    step=100.0,
                )

                category_name = st.selectbox(
                    "Category",
                    list(
                        cat_by_name.keys()
                    ),
                )

                expense_date = st.date_input(
                    "Date",
                    value=date.today(),
                )

                description = st.text_input(
                    "Description",
                )

                if st.form_submit_button(
                    "Add Expense",
                    use_container_width=True,
                ):

                    try:

                        api_request(
                            "POST",
                            "/expenses",
                            token,
                            json={
                                "amount": amount,
                                "category_id":
                                    cat_by_name[
                                        category_name
                                    ]["id"],
                                "description":
                                    description
                                    or None,
                                "expense_date":
                                    str(
                                        expense_date
                                    ),
                            },
                        )

                        st.success(
                            "Expense added!"
                        )

                        st.rerun()

                    except RuntimeError as error:

                        st.error(
                            str(error)
                        )


    # ============================================================
    # EXPENSES PAGE
    # ============================================================

    elif page == "💸 Expenses":

        st.title(
            "💸 Expenses"
        )

        with st.expander(
            "➕ Add New Expense",
            expanded=True,
        ):

            with st.form(
                "expense_form"
            ):

                c1, c2 = st.columns(2)

                amount = c1.number_input(
                    "Amount (₹)",
                    min_value=0.01,
                    step=100.0,
                )

                category_name = c2.selectbox(
                    "Category",
                    list(
                        cat_by_name.keys()
                    ),
                )

                expense_date = c1.date_input(
                    "Date",
                    value=date.today(),
                )

                description = c2.text_input(
                    "Description",
                    placeholder="Lunch, shopping, fuel...",
                )

                if st.form_submit_button(
                    "Save Expense",
                    use_container_width=True,
                ):

                    try:

                        api_request(
                            "POST",
                            "/expenses",
                            token,
                            json={
                                "amount": amount,
                                "category_id":
                                    cat_by_name[
                                        category_name
                                    ]["id"],
                                "description":
                                    description
                                    or None,
                                "expense_date":
                                    str(
                                        expense_date
                                    ),
                            },
                        )

                        st.success(
                            "Expense saved."
                        )

                        st.rerun()

                    except RuntimeError as error:

                        st.error(
                            str(error)
                        )

        st.divider()

        st.subheader(
            "🔎 Expense History"
        )

        c1, c2, c3 = st.columns(3)

        start = c1.date_input(
            "From",
            value=date.today().replace(
                day=1
            ),
        )

        end = c2.date_input(
            "To",
            value=date.today(),
        )

        category_filter = c3.selectbox(
            "Category",
            [
                "All"
            ]
            + list(
                cat_by_name.keys()
            ),
        )

        try:

            params = {
                "start": str(start),
                "end": str(end),
            }

            if category_filter != "All":

                params[
                    "category_id"
                ] = cat_by_name[
                    category_filter
                ]["id"]

            rows = api_request(
                "GET",
                "/expenses",
                token,
                params=params,
            )

        except RuntimeError as error:

            st.error(
                str(error)
            )

            st.stop()

        if not rows:

            st.info(
                "No expenses found."
            )

        else:

            table = pd.DataFrame(
                [
                    {
                        "ID": item["id"],
                        "Date":
                            item[
                                "expense_date"
                            ],
                        "Category":
                            (
                                item["icon"]
                                + " "
                                + item["category"]
                            ),
                        "Amount":
                            item["amount"],
                        "Description":
                            item[
                                "description"
                            ]
                            or "",
                    }
                    for item in rows
                ]
            )

            st.dataframe(
                table,
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                "⬇️ Export CSV",
                table.to_csv(
                    index=False
                ),
                "expenses.csv",
                "text/csv",
            )

            st.divider()

            st.subheader(
                "✏️ Edit / Delete Expense"
            )

            selected = st.selectbox(
                "Select Expense",
                rows,
                format_func=lambda x:
                    (
                        f"#{x['id']} • "
                        f"{money(x['amount'])} • "
                        f"{x['category']} • "
                        f"{x['expense_date']}"
                    ),
            )

            with st.form(
                "edit_expense"
            ):

                c1, c2 = st.columns(2)

                amount = c1.number_input(
                    "Amount",
                    min_value=0.01,
                    value=float(
                        selected["amount"]
                    ),
                    step=100.0,
                )

                current_category = selected[
                    "category"
                ]

                category_name = c2.selectbox(
                    "Category",
                    list(
                        cat_by_name.keys()
                    ),
                    index=list(
                        cat_by_name.keys()
                    ).index(
                        current_category
                    ),
                )

                expense_date = c1.date_input(
                    "Date",
                    value=date.fromisoformat(
                        selected[
                            "expense_date"
                        ]
                    ),
                )

                description = c2.text_input(
                    "Description",
                    value=
                        selected[
                            "description"
                        ]
                        or "",
                )

                update_button, delete_button = (
                    st.columns(2)
                )

                update_clicked = (
                    update_button.form_submit_button(
                        "💾 Update",
                        use_container_width=True,
                    )
                )

                delete_clicked = (
                    delete_button.form_submit_button(
                        "🗑️ Delete",
                        use_container_width=True,
                    )
                )

                try:

                    if update_clicked:

                        api_request(
                            "PUT",
                            f"/expenses/{selected['id']}",
                            token,
                            json={
                                "amount": amount,
                                "category_id":
                                    cat_by_name[
                                        category_name
                                    ]["id"],
                                "description":
                                    description
                                    or None,
                                "expense_date":
                                    str(
                                        expense_date
                                    ),
                            },
                        )

                        st.success(
                            "Expense updated."
                        )

                        st.rerun()

                    if delete_clicked:

                        api_request(
                            "DELETE",
                            f"/expenses/{selected['id']}",
                            token,
                        )

                        st.success(
                            "Expense deleted."
                        )

                        st.rerun()

                except RuntimeError as error:

                    st.error(
                        str(error)
                    )


    # ============================================================
    # INCOME PAGE
    # ============================================================

    elif page == "💵 Income":

        st.title(
            "💵 Income"
        )

        with st.expander(
            "➕ Add Income",
            expanded=True,
        ):

            with st.form(
                "income_form"
            ):

                c1, c2 = st.columns(2)

                amount = c1.number_input(
                    "Amount (₹)",
                    min_value=0.01,
                    step=500.0,
                )

                source = c2.text_input(
                    "Source",
                    placeholder="Salary / Freelance / Business",
                )

                income_date = c1.date_input(
                    "Date",
                    value=date.today(),
                )

                description = c2.text_input(
                    "Description",
                )

                if st.form_submit_button(
                    "Save Income",
                    use_container_width=True,
                ):

                    if not source.strip():

                        st.error(
                            "Please enter an income source."
                        )

                    else:

                        try:

                            api_request(
                                "POST",
                                "/income",
                                token,
                                json={
                                    "amount": amount,
                                    "source":
                                        source.strip(),
                                    "description":
                                        description
                                        or None,
                                    "income_date":
                                        str(
                                            income_date
                                        ),
                                },
                            )

                            st.success(
                                "Income saved."
                            )

                            st.rerun()

                        except RuntimeError as error:

                            st.error(
                                str(error)
                            )

        st.divider()

        st.subheader(
            "📋 Income History"
        )

        try:

            income_rows = api_request(
                "GET",
                "/income",
                token,
            )

        except RuntimeError as error:

            st.error(
                str(error)
            )

            st.stop()

        if not income_rows:

            st.info(
                "No income records yet."
            )

        else:

            table = pd.DataFrame(
                [
                    {
                        "ID": item["id"],
                        "Date":
                            item[
                                "income_date"
                            ],
                        "Source":
                            item["source"],
                        "Amount":
                            item["amount"],
                        "Description":
                            item[
                                "description"
                            ]
                            or "",
                    }
                    for item in income_rows
                ]
            )

            st.dataframe(
                table,
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                "⬇️ Export Income CSV",
                table.to_csv(
                    index=False
                ),
                "income.csv",
                "text/csv",
            )

            st.divider()

            st.subheader(
                "✏️ Edit / Delete Income"
            )

            selected = st.selectbox(
                "Select Income",
                income_rows,
                format_func=lambda x:
                    (
                        f"#{x['id']} • "
                        f"{money(x['amount'])} • "
                        f"{x['source']} • "
                        f"{x['income_date']}"
                    ),
            )

            with st.form(
                "edit_income"
            ):

                c1, c2 = st.columns(2)

                amount = c1.number_input(
                    "Amount",
                    min_value=0.01,
                    value=float(
                        selected["amount"]
                    ),
                    step=500.0,
                )

                source = c2.text_input(
                    "Source",
                    value=selected[
                        "source"
                    ],
                )

                income_date = c1.date_input(
                    "Date",
                    value=date.fromisoformat(
                        selected[
                            "income_date"
                        ]
                    ),
                )

                description = c2.text_input(
                    "Description",
                    value=
                        selected[
                            "description"
                        ]
                        or "",
                )

                update_button, delete_button = (
                    st.columns(2)
                )

                update_clicked = (
                    update_button.form_submit_button(
                        "💾 Update",
                        use_container_width=True,
                    )
                )

                delete_clicked = (
                    delete_button.form_submit_button(
                        "🗑️ Delete",
                        use_container_width=True,
                    )
                )

                try:

                    if update_clicked:

                        api_request(
                            "PUT",
                            f"/income/{selected['id']}",
                            token,
                            json={
                                "amount": amount,
                                "source":
                                    source,
                                "description":
                                    description
                                    or None,
                                "income_date":
                                    str(
                                        income_date
                                    ),
                            },
                        )

                        st.success(
                            "Income updated."
                        )

                        st.rerun()

                    if delete_clicked:

                        api_request(
                            "DELETE",
                            f"/income/{selected['id']}",
                            token,
                        )

                        st.success(
                            "Income deleted."
                        )

                        st.rerun()

                except RuntimeError as error:

                    st.error(
                        str(error)
                    )


    # ============================================================
    # BUDGETS PAGE
    # ============================================================

    elif page == "🎯 Budgets":

        st.title(
            "🎯 Monthly Budgets"
        )

        with st.form(
            "budget_form"
        ):

            c1, c2, c3 = st.columns(3)

            category_name = c1.selectbox(
                "Category",
                list(
                    cat_by_name.keys()
                ),
            )

            month = c2.date_input(
                "Month",
                value=date.today().replace(
                    day=1
                ),
            )

            amount = c3.number_input(
                "Budget (₹)",
                min_value=1.0,
                step=500.0,
            )

            if st.form_submit_button(
                "Save Budget",
                use_container_width=True,
            ):

                try:

                    api_request(
                        "POST",
                        "/budgets",
                        token,
                        json={
                            "category_id":
                                cat_by_name[
                                    category_name
                                ]["id"],
                            "month":
                                str(
                                    month.replace(
                                        day=1
                                    )
                                ),
                            "amount":
                                amount,
                        },
                    )

                    st.success(
                        "Budget saved."
                    )

                    st.rerun()

                except RuntimeError as error:

                    st.error(
                        str(error)
                    )

        st.divider()

        try:

            budget_rows = api_request(
                "GET",
                "/budgets",
                token,
            )

            expense_rows = api_request(
                "GET",
                "/expenses",
                token,
            )

        except RuntimeError as error:

            st.error(
                str(error)
            )

            st.stop()

        spent = {}

        for expense in expense_rows:

            key = (
                expense["category_id"],
                expense[
                    "expense_date"
                ][:7],
            )

            spent[key] = (
                spent.get(
                    key,
                    0
                )
                + float(
                    expense["amount"]
                )
            )

        if not budget_rows:

            st.info(
                "You haven't created any budgets yet."
            )

        for budget in budget_rows:

            key = (
                budget[
                    "category_id"
                ],
                budget["month"][:7],
            )

            used = spent.get(
                key,
                0
            )

            limit = float(
                budget["amount"]
            )

            progress = (
                min(
                    used / limit,
                    1
                )
                if limit > 0
                else 0
            )

            st.write(
                f"**{budget['category']}** "
                f"• {budget['month'][:7]} "
                f"• {money(used)} / "
                f"{money(limit)}"
            )

            st.progress(
                progress
            )

            if used > limit:

                st.error(
                    f"Budget exceeded by "
                    f"{money(used - limit)}"
                )

            elif used >= limit * 0.8:

                st.warning(
                    "You have used more than "
                    "80% of this budget."
                )

            if st.button(
                "🗑️ Delete Budget",
                key=f"budget_{budget['id']}",
            ):

                try:

                    api_request(
                        "DELETE",
                        f"/budgets/{budget['id']}",
                        token,
                    )

                    st.rerun()

                except RuntimeError as error:

                    st.error(
                        str(error)
                    )

            st.divider()


    # ============================================================
    # REPORTS PAGE
    # ============================================================

    elif page == "📈 Reports":

        st.title(
            "📈 Reports & Analytics"
        )

        try:

            expense_rows = api_request(
                "GET",
                "/expenses",
                token,
            )

            income_rows = api_request(
                "GET",
                "/income",
                token,
            )

        except RuntimeError as error:

            st.error(
                str(error)
            )

            st.stop()

        if not expense_rows:

            st.info(
                "Add some expenses to generate reports."
            )

        else:

            expense_df = pd.DataFrame(
                [
                    {
                        "Date":
                            item[
                                "expense_date"
                            ],
                        "Category":
                            item[
                                "category"
                            ],
                        "Amount":
                            float(
                                item[
                                    "amount"
                                ]
                            ),
                    }
                    for item in expense_rows
                ]
            )

            expense_df["Date"] = pd.to_datetime(
                expense_df["Date"]
            )

            expense_df["Month"] = (
                expense_df[
                    "Date"
                ]
                .dt.to_period("M")
                .astype(str)
            )

            monthly = (
                expense_df
                .groupby(
                    "Month",
                    as_index=False,
                )["Amount"]
                .sum()
            )

            by_category = (
                expense_df
                .groupby(
                    "Category",
                    as_index=False,
                )["Amount"]
                .sum()
                .sort_values(
                    "Amount",
                    ascending=False,
                )
            )

            c1, c2 = st.columns(2)

            with c1:

                fig = px.line(
                    monthly,
                    x="Month",
                    y="Amount",
                    markers=True,
                    title="Monthly Expenses",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

            with c2:

                fig = px.pie(
                    by_category,
                    names="Category",
                    values="Amount",
                    title="Spending by Category",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

            st.subheader(
                "📊 Category Breakdown"
            )

            display_df = by_category.rename(
                columns={
                    "Category":
                        "Category",
                    "Amount":
                        "Amount (₹)",
                }
            )

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
            )

            # ----------------------------------------------------
            # INCOME VS EXPENSES
            # ----------------------------------------------------

            if income_rows:

                income_df = pd.DataFrame(
                    [
                        {
                            "Date":
                                item[
                                    "income_date"
                                ],
                            "Amount":
                                float(
                                    item[
                                        "amount"
                                    ]
                                ),
                        }
                        for item in income_rows
                    ]
                )

                income_df["Date"] = pd.to_datetime(
                    income_df["Date"]
                )

                income_df["Month"] = (
                    income_df[
                        "Date"
                    ]
                    .dt.to_period("M")
                    .astype(str)
                )

                monthly_income = (
                    income_df
                    .groupby(
                        "Month",
                        as_index=False,
                    )["Amount"]
                    .sum()
                )

                monthly_comparison = pd.merge(
                    monthly.rename(
                        columns={
                            "Amount":
                                "Expenses"
                        }
                    ),
                    monthly_income.rename(
                        columns={
                            "Amount":
                                "Income"
                        }
                    ),
                    on="Month",
                    how="outer",
                ).fillna(0)

                st.subheader(
                    "💵 Income vs Expenses"
                )

                long_df = monthly_comparison.melt(
                    id_vars="Month",
                    value_vars=[
                        "Income",
                        "Expenses",
                    ],
                    var_name="Type",
                    value_name="Amount",
                )

                fig = px.bar(
                    long_df,
                    x="Month",
                    y="Amount",
                    color="Type",
                    barmode="group",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )


    # ============================================================

if __name__ == "__main__":
    run_streamlit_app()
