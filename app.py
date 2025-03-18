import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

@st.cache_data
def load_data():
    """
    Googleスプレッドシート(Excel形式)の2つのURLから読み込んで
    1つのデータフレームに結合して返す
    """
    url1 = "https://docs.google.com/spreadsheets/d/1lApw-JzQEAg3XoAwerQ4d9uZ1XbqJ5Ql/export?format=xlsx&id=1lApw-JzQEAg3XoAwerQ4d9uZ1XbqJ5Ql"
    url2 = "https://docs.google.com/spreadsheets/d/1ntWDGEseHP8-Y7lwECEGEntyEP3wKk5G/export?format=xlsx&id=1ntWDGEseHP8-Y7lwECEGEntyEP3wKk5G"

    df1 = pd.read_excel(url1)
    df2 = pd.read_excel(url2)

    # 同じ列構造を想定
    df = pd.concat([df1, df2], ignore_index=True)
    return df

def filter_data(
    df,
    shikirihinmei_list,
    gensanchi_list,
    shukkasha_list,
    ibai_kubun_list,
    start_month,
    start_day,
    end_month,
    end_day
):
    # 必須(仕切品名)
    if shikirihinmei_list:
        df = df[df["仕切品名"].isin(shikirihinmei_list)]
    else:
        # 未選択の場合は空を返す
        return df.iloc[0:0]

    # 必須(原産地名称)
    if gensanchi_list:
        df = df[df["原産地名称"].isin(gensanchi_list)]
    else:
        return df.iloc[0:0]

    # 任意(出荷者名称)
    if shukkasha_list:
        df = df[df["出荷者名称"].isin(shukkasha_list)]

    # 任意(委買区分)
    if ibai_kubun_list:
        df = df[df["委買区分"].isin(ibai_kubun_list)]

    # 期間指定(月/日)が入力されていれば絞り込み
    if (start_month is not None) and (start_day is not None) \
       and (end_month is not None) and (end_day is not None):
        df = df[
            (
                (df["月"] > start_month)
                | ((df["月"] == start_month) & (df["日"] >= start_day))
            )
            &
            (
                (df["月"] < end_month)
                | ((df["月"] == end_month) & (df["日"] <= end_day))
            )
        ]

    return df

def page_item_search(df):
    st.subheader("■ 品目データ検索")

    # 必須
    unique_shikirihinmei = sorted(df["仕切品名"].dropna().unique())
    shikirihinmei_selected = st.multiselect("仕切品名(必須)", unique_shikirihinmei)

    # 必須
    unique_gensanchi = sorted(df["原産地名称"].dropna().unique())
    gensanchi_selected = st.multiselect("原産地名称(必須)", unique_gensanchi)

    # 任意
    unique_shukkasha = sorted(df["出荷者名称"].dropna().unique())
    shukkasha_selected = st.multiselect("出荷者名称(任意)", unique_shukkasha)

    # 任意
    unique_ibai = sorted(df["委買区分"].dropna().unique())
    ibai_selected = st.multiselect("委買区分(任意)", unique_ibai)

    # 期間指定(月/日)
    st.markdown("#### 期間指定")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_month = st.number_input("開始 月", min_value=1, max_value=12, value=1)
    with col2:
        start_day = st.number_input("開始 日", min_value=1, max_value=31, value=1)
    with col3:
        end_month = st.number_input("終了 月", min_value=1, max_value=12, value=12)
    with col4:
        end_day = st.number_input("終了 日", min_value=1, max_value=31, value=31)

    if st.button("検索実行"):
        filtered = filter_data(
            df,
            shikirihinmei_selected,
            gensanchi_selected,
            shukkasha_selected,
            ibai_selected,
            start_month,
            start_day,
            end_month,
            end_day
        )

        # 該当が0件の場合
        if len(filtered) == 0:
            st.warning("該当データがありません。")
            return

        # 1) 等級, 階級, 荷姿 ごとの 単価 平均
        groupedA = filtered.groupby(["等級", "階級", "荷姿"], as_index=False)["単価"].mean()
        groupedA.rename(columns={"単価": "平均単価"}, inplace=True)

        # 2) (グラフB) 月, 日 ごとの 金額 合計
        groupedB = filtered.groupby(["月", "日"], as_index=False)["金額"].sum()
        groupedB.rename(columns={"金額": "合計金額"}, inplace=True)

        # 3) 対象データのセリ人名一覧
        seribito_list = filtered["セリ人名"].dropna().unique().tolist()

        # 検索条件とセリ人名
        st.markdown("### 検索条件")
        st.write("仕切品名:", shikirihinmei_selected)
        st.write("原産地名称:", gensanchi_selected)
        st.write("出荷者名称:", shukkasha_selected)
        st.write("委買区分:", ibai_selected)
        st.write("期間:", f"{start_month}/{start_day} ～ {end_month}/{end_day}")

        st.markdown("### セリ人名一覧")
        st.write(seribito_list)

        st.markdown("### テーブルA (等級 × 階級 × 荷姿 × 平均単価)")
        st.dataframe(groupedA)

        st.markdown("### グラフB (月・日 × 金額)")
        fig, ax = plt.subplots()
        ax.plot(
            groupedB["月"].astype(str) + "/" + groupedB["日"].astype(str),
            groupedB["合計金額"],
            marker='o'
        )
        ax.set_xlabel("月/日")
        ax.set_ylabel("合計金額")
        ax.set_title("月・日ごとの金額推移")
        plt.xticks(rotation=45)
        st.pyplot(fig)

def page_customer_search(df):
    st.subheader("■ 顧客データ検索")

    # 必須
    unique_shikirihinmei = sorted(df["仕切品名"].dropna().unique())
    shikirihinmei_selected = st.multiselect("仕切品名(必須)", unique_shikirihinmei)

    # 必須
    unique_gensanchi = sorted(df["原産地名称"].dropna().unique())
    gensanchi_selected = st.multiselect("原産地名称(必須)", unique_gensanchi)

    # 任意
    unique_shukkasha = sorted(df["出荷者名称"].dropna().unique())
    shukkasha_selected = st.multiselect("出荷者名称(任意)", unique_shukkasha)

    # 任意
    unique_ibai = sorted(df["委買区分"].dropna().unique())
    ibai_selected = st.multiselect("委買区分(任意)", unique_ibai)

    # 期間指定(月/日)
    st.markdown("#### 期間指定")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_month = st.number_input("開始 月", min_value=1, max_value=12, value=1)
    with col2:
        start_day = st.number_input("開始 日", min_value=1, max_value=31, value=1)
    with col3:
        end_month = st.number_input("終了 月", min_value=1, max_value=12, value=12)
    with col4:
        end_day = st.number_input("終了 日", min_value=1, max_value=31, value=31)

    if st.button("検索実行"):
        filtered = filter_data(
            df,
            shikirihinmei_selected,
            gensanchi_selected,
            shukkasha_selected,
            ibai_selected,
            start_month,
            start_day,
            end_month,
            end_day
        )

        if len(filtered) == 0:
            st.warning("該当データがありません。")
            return

        # 買受人名, 等級, 階級, 荷姿 ごとの 数量合計
        groupedC = filtered.groupby(["買受人名", "等級", "階級", "荷姿"], as_index=False)["数量"].sum()
        groupedC.rename(columns={"数量": "合計数量"}, inplace=True)

        # セリ人名一覧
        seribito_list = filtered["セリ人名"].dropna().unique().tolist()

        st.markdown("### 検索条件")
        st.write("仕切品名:", shikirihinmei_selected)
        st.write("原産地名称:", gensanchi_selected)
        st.write("出荷者名称:", shukkasha_selected)
        st.write("委買区分:", ibai_selected)
        st.write("期間:", f"{start_month}/{start_day} ～ {end_month}/{end_day}")

        st.markdown("### セリ人名一覧")
        st.write(seribito_list)

        st.markdown("### 買受人名 × 等級 × 階級 × 荷姿 ごとの 数量合計")
        st.dataframe(groupedC)

def main():
    st.title("Googleスプレッドシートデータ一括検索アプリ")
    df = load_data()

    # 機能切り替え
    page = st.selectbox("機能を選択", ["品目データ検索", "顧客データ検索"])
    if page == "品目データ検索":
        page_item_search(df)
    else:
        page_customer_search(df)

if __name__ == "__main__":
    main()
