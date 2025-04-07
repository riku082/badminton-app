import streamlit as st
import pandas as pd
import os
import ast
import json
import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go

PLAYER_CSV = "players.csv"
MATCH_CSV = "matches.csv"
SHOT_CSV = "shots.csv"

expected_columns = ["試合ID", "試合形式", "選手名", "チーム"]
if os.path.exists(MATCH_CSV):
    try:
        df_check = pd.read_csv(MATCH_CSV)
        if list(df_check.columns) != expected_columns:
            st.warning("⚠️ matchファイルの列構成が不正だったため、初期化しました。")
            os.remove(MATCH_CSV)
    except Exception as e:
        st.warning(f"⚠️ matchファイルの読み込みに失敗したため、初期化しました。\n詳細: {e}")
        os.remove(MATCH_CSV)

if not os.path.exists(PLAYER_CSV):
    pd.DataFrame(columns=["名前", "利き手", "チーム"]).to_csv(PLAYER_CSV, index=False)
if not os.path.exists(MATCH_CSV):
    pd.DataFrame(columns=expected_columns).to_csv(MATCH_CSV, index=False)
if not os.path.exists(SHOT_CSV):
    pd.DataFrame(columns=["試合ID", "ラリー番号", "ショット順", "打った選手", "打点", "着地", "ショット", "結果", "レシーバー"]).to_csv(SHOT_CSV, index=False)

for key in ["match_id", "last_end_area", "rally_no", "shot_order", "score_A", "score_B", "last_hitter", "next_player"]:
    if key not in st.session_state:
        st.session_state[key] = 0 if key.startswith("score") else (None if key == "match_id" else 1 if key == "rally_no" else "")

if "page" not in st.session_state:
    st.session_state.page = "選手登録"

st.sidebar.title(" メニュー")
if st.sidebar.button("🏸 選手登録"):
    st.session_state.page = "選手登録"
if st.sidebar.button("📋 試合管理"):
    st.session_state.page = "試合管理"
if st.sidebar.button("🗓 試合登録"):
    st.session_state.page = "試合登録"
if st.sidebar.button("📝 試合記録"):
    st.session_state.page = "試合開始・記録"
if st.sidebar.button("👤 プロフィール一覧"):
    st.session_state.page = "選手プロフィール一覧"
if st.sidebar.button("📊 データ解析"):
    st.session_state.page = "データ解析"
if st.sidebar.button("🧾 CSV編集"):
    st.session_state.page = "CSV編集"

page = st.session_state.page

if page == "選手登録":
    st.title("選手登録")
    with st.form("player_form"):
        name = st.text_input("名前")
        hand = st.selectbox("利き手", ["右", "左"])
        team = st.text_input("チーム名")
        submit = st.form_submit_button("登録")
        if submit:
            df = pd.read_csv(PLAYER_CSV)
            if name in df["名前"].values:
                st.warning("この選手はすでに登録されています。")
            else:
                df.loc[len(df)] = [name, hand, team]
                df.to_csv(PLAYER_CSV, index=False)
                st.success(f"{name} さんを登録しました！")
    st.subheader("📋 登録済み選手")
    st.dataframe(pd.read_csv(PLAYER_CSV))

elif page == "試合管理":
    st.title("試合管理（一覧と削除）")

    # 試合一覧表示
    if os.path.exists(MATCH_CSV):
        match_df = pd.read_csv(MATCH_CSV)
        st.subheader("📅 登録済みの試合一覧")
        selected_filter_player = st.selectbox("選手で絞り込み", ["全員"] + sorted(match_df["選手名"].unique().tolist()))
        if selected_filter_player != "全員":
            filtered_df = match_df[match_df["選手名"] == selected_filter_player]
        else:
            filtered_df = match_df
        st.dataframe(filtered_df)

        # 削除機能
        match_ids = match_df["試合ID"].unique().tolist()
        selected_delete_match = st.selectbox("削除したい試合IDを選択", match_ids)
        if st.button("🗑️ この試合を削除"):
            match_df = match_df[match_df["試合ID"] != selected_delete_match]
            match_df.to_csv(MATCH_CSV, index=False)

            shot_df = pd.read_csv(SHOT_CSV)
            shot_df = shot_df[shot_df["試合ID"] != selected_delete_match]
            shot_df.to_csv(SHOT_CSV, index=False)

            st.success(f"試合 {selected_delete_match} を削除しました。")
            st.stop()
    # グローバルで一度だけ定義
players_df = pd.read_csv(PLAYER_CSV)
all_players = players_df["名前"].tolist()




if page == "試合登録":
    st.title("🏸 試合登録")
    with st.form("match_form"):
        match_date = st.date_input("試合日付", value=datetime.date.today())
        match_number = st.selectbox("試合番号", ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"])
        selected_players = st.multiselect("選手（1〜4人）", all_players, max_selections=4)
        match_type = "ダブルス" if len(selected_players) > 2 else "シングルス"

        auto_match_id = f"{match_date}_{match_number}_{'_'.join(selected_players)}"
        st.text_input("自動生成された試合ID", value=auto_match_id, disabled=True)
        submit_match = st.form_submit_button("試合を登録")

        if submit_match and selected_players:
            match_df = pd.read_csv(MATCH_CSV)
            for player in selected_players:
                match_df.loc[len(match_df)] = [auto_match_id, match_type, player, ""]
            match_df.to_csv(MATCH_CSV, index=False)
            st.success("試合を登録しました。")

elif page == "選手プロフィール一覧":
    st.title("選手プロフィール一覧")
    df = pd.read_csv(SHOT_CSV)
    player_list = df["打った選手"].unique().tolist()
    cols = st.columns(2)
    for i, player in enumerate(player_list):
        with cols[i % 2]:
            with st.container():
                st.markdown("""
                <div style='background-color: #f0f2f6; padding: 16px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                """, unsafe_allow_html=True)

                player_df = df[df["打った選手"] == player]
                score = player_df[player_df["結果"] == "得点"].shape[0]
                miss = player_df[player_df["結果"] == "ミス"].shape[0]
                total = player_df.shape[0]
                values = [
                    score / total if total > 0 else 0,
                    1 - (miss / total) if total > 0 else 0,
                    player_df["ショット"].nunique() / 9,
                    player_df[player_df["打点"] == "CM"].shape[0] / total if total > 0 else 0
                ]
                categories = ["得点率", "ミス率（逆）", "多様性スコア", "中央打点率"]

                st.markdown(f"#### 🏸 {player}")
                player_info = players_df[players_df["名前"] == player].iloc[0]
                st.markdown(f"- チーム: {player_info['チーム']}")
                st.markdown(f"- 利き手: {player_info['利き手']}")

                st.markdown(f"- 試合数: {player_df['試合ID'].nunique()}")
                st.markdown(f"- 総ショット数: {total}")
                st.markdown(f"- 決定率: {(score / total * 100):.1f}%")
                st.markdown(f"- ミス率: {(miss / total * 100):.1f}%")

                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    name=player
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    showlegend=False,
                    margin=dict(t=0, b=0),
                    height=300
                )
                st.plotly_chart(fig_radar, use_container_width=True)

                if st.button(f"🔍 {player} のデータ解析を見る", key=f"view_{player}"):
                    st.session_state["selected_analysis_player"] = player
                    st.rerun()

                st.markdown("""</div>""", unsafe_allow_html=True)

elif page == "データ解析":
    st.title("データ解析")
    df = pd.read_csv(SHOT_CSV)
    if df.empty:
        st.warning("データがありません。記録を追加してください。")
    else:
        player_list = df["打った選手"].unique().tolist()
        selected_player = st.session_state.get("selected_analysis_player") or st.selectbox("選手を選択", player_list)
        player_df = df[df["打った選手"] == selected_player]

        st.subheader("📈 得点率・ミス率")
        score_count = player_df[player_df["結果"] == "得点"].shape[0]
        miss_count = player_df[player_df["結果"] == "ミス"].shape[0]
        total = player_df.shape[0]
        st.metric("得点率", f"{(score_count / total * 100):.1f}%")
        st.metric("ミス率", f"{(miss_count / total * 100):.1f}%")

        st.subheader("🔍 後衛からのショット傾向")
        rear_areas = ["RR", "CR", "LR"]
        rear_shots = player_df[player_df["打点"].isin(rear_areas)]

        drop_count = (rear_shots["ショット"] == "ドロップ").sum()
        smash_count = (rear_shots["ショット"] == "スマッシュ").sum()
        cross_count = rear_shots.apply(lambda row: row["着地"] in ["LF", "CF", "RF"] and row["打点"] in ["RR", "CR", "LR"] and row["打点"] != row["着地"], axis=1).sum()
        total_rear = len(rear_shots)

        drop_rate = drop_count / total_rear * 100 if total_rear > 0 else 0
        smash_rate = smash_count / total_rear * 100 if total_rear > 0 else 0
        cross_rate = cross_count / total_rear * 100 if total_rear > 0 else 0

        st.metric("ドロップ率（後衛）", f"{drop_rate:.1f}%")
        st.metric("スマッシュ率（後衛）", f"{smash_rate:.1f}%")
        st.metric("クロス選択率（後衛）", f"{cross_rate:.1f}%")

    
        st.subheader("レーダーチャート")
        categories = ["ミス率（逆）", "中央選択率", "クリア選択率", "ロブ選択率"]
        values = []

        # ミス率（逆）
        values.append(1 - (miss_count / total) if total > 0 else 0)

        # 中央選択率（打点または着地点が中央の割合）
        center_hits = player_df[(player_df["打点"].str.contains("C")) | (player_df["着地"].str.contains("C"))].shape[0]
        values.append(center_hits / total if total > 0 else 0)

        # クリア選択率
        clear_rate = player_df[player_df["ショット"] == "クリア"].shape[0] / total if total > 0 else 0
        values.append(clear_rate)

        # ロブ選択率
        lob_rate = player_df[player_df["ショット"] == "ロブ"].shape[0] / total if total > 0 else 0
        values.append(lob_rate)

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name=selected_player
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=False
        )
        st.plotly_chart(fig_radar, use_container_width=True)


  
        st.subheader("後衛からのショット傾向")
        rear_areas = ["RR", "CR", "LR"]
        rear_shots = player_df[player_df["打点"].isin(rear_areas)]
        if rear_shots.empty:
            st.info("後衛エリアからのショットデータがありません。")
        else:
            # ショット種別
            shot_counts = rear_shots["ショット"].value_counts()
            st.markdown("**後衛エリアからのショット種類の割合（全体ショットに対する割合）**")

            # 円グラフとして割合を全体ショット数で可視化
            total_shots = player_df.shape[0]
            shot_percent = (shot_counts / total_shots * 100).round(1)
            fig_pie = go.Figure(data=[
                go.Pie(labels=shot_percent.index, values=shot_percent.values, hole=0.4)
            ])
            fig_pie.update_traces(textinfo='label+percent')
            fig_pie.update_layout(margin=dict(t=0, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)

            








        st.subheader("📍 ミスが発生した打点エリア ヒートマップ")
        miss_df = player_df[player_df["結果"] == "ミス"]
        area_order = ["RR", "CR", "LR", "RM", "CM", "LM", "RF", "CF", "LF"]
        area_labels = {
            "RR": "右後", "CR": "中央後", "LR": "左後",
            "RM": "右中", "CM": "中央中", "LM": "左中",
            "RF": "右前", "CF": "中央前", "LF": "左前",
        }
        area_counts = miss_df["打点"].value_counts().reindex(area_order, fill_value=0)
        heatmap_data = np.array(area_counts.values).reshape(3, 3)

        fig, ax = plt.subplots(figsize=(5, 4))
        sns.heatmap(
            heatmap_data,
            annot=True,
            fmt="d",
            cmap="Reds",
            xticklabels=["右", "中央", "左"],
            yticklabels=["前", "中", "後"],
            ax=ax
        )
        ax.set_title(f"{selected_player} のミス発生打点分布")
        st.pyplot(fig)

        st.image("new_court_map.webp", caption="コート構成", use_container_width=True)


               



elif page == "試合開始・記録":
    st.title("個人ショット記録")

    st.subheader("🎯 試合と選手を選択")
    match_df = pd.read_csv(MATCH_CSV)
    match_ids = match_df["試合ID"].unique().tolist()
    selected_match = st.selectbox("試合IDを選択", match_ids)

    match_players = match_df[match_df["試合ID"] == selected_match]["選手名"].tolist()
    selected_player = st.selectbox("選手名を選択", match_players)

    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.image("new_court_map.webp", caption="コート図", use_container_width=True)
    with col_right:
        with st.form("individual_shot_form"):
            
            st.markdown("### 🔽 ショット記録")
            area_list = ["RR", "CR", "LR", "RM", "CM", "LM", "RF", "CF", "LF"]

            start_area = st.selectbox("打点エリア", area_list)
            end_area = st.selectbox("着地点エリア", area_list)
            shot_type = st.radio("ショット種類", ["クリア", "スマッシュ", "ドロップ", "ロングリターン", "ショートリターン", "ドライブ", "ロブ", "プッシュ", "ヘアピン"], horizontal=True)
            result = st.radio("結果", ["続行", "得点", "ミス", "アウト"], horizontal=True)
            match_id = selected_match

            submit = st.form_submit_button("記録する")
            if submit:
                df = pd.read_csv(SHOT_CSV)
                if "レシーバー" not in df.columns:
                    df["レシーバー"] = ""
                rally_no = 1
                shot_order = len(df[(df["試合ID"] == match_id)]) + 1
                df.loc[len(df)] = [match_id, rally_no, shot_order, selected_player, start_area, end_area, shot_type, result, ""]  
                df.to_csv(SHOT_CSV, index=False)
                st.success(f"{selected_player} のショットを記録しました！")
    st.subheader(f"📋 {selected_player} のショット履歴")
    df = pd.read_csv(SHOT_CSV)

    personal_shots = df[(df["打った選手"] == selected_player) & (df["試合ID"] == selected_match)].sort_values(by=["ラリー番号", "ショット順"])
    st.dataframe(personal_shots.reset_index(drop=True))

    if st.button("✅ この試合の記録を終了する"):
        st.success("試合の記録を終了しました。別のページへ移動してください。")
        st.stop()

    if st.button("🗑️ 最後の1件を削除"):
        if not personal_shots.empty:
            last_index = personal_shots.index[-1]
            df = df.drop(index=last_index)
            df.to_csv(SHOT_CSV, index=False)
            st.success("最後のショット記録を削除しました。")
            st.experimental_rerun()

elif page == "CSV編集":
    st.title("CSVファイル編集")

    file_option = st.selectbox("編集するCSVファイルを選択", ["players.csv", "matches.csv", "shots.csv"])
    file_path = file_option

    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        st.markdown(f"### {file_option} の内容を編集")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    if st.button("💾 変更を保存"):
    # すべてがNaNの列を削除
        cleaned_df = edited_df.dropna(axis=1, how='all')
        cleaned_df = cleaned_df.dropna(axis=0, how='all')
        cleaned_df.to_csv(file_path, index=False)
        st.success(f"{file_option} を保存しました（空の列は削除されました）。")

    else:
        st.warning(f"{file_path} が見つかりません。ファイルが存在するか確認してください。")
    