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

st.sidebar.title("メニュー")
page = st.sidebar.selectbox("ページを選択", ["選手登録", "試合開始・記録", "データ解析"])

if page == "選手登録":
    st.title("🏸 選手登録")
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



elif page == "試合開始・記録":
    st.title("📘 試合登録・配球記録")
    players_df = pd.read_csv(PLAYER_CSV)
    all_players = players_df["名前"].tolist()

    if st.session_state.match_id is None:
        st.subheader("📋 試合登録")
        today = datetime.date.today()
        selected_date = st.date_input("試合日", value=today)

        with st.form("match_form"):
            left_pair = st.multiselect("左ペア（Team A）", all_players)
            right_pair = st.multiselect("右ペア（Team B）", all_players)

            match_number = "①"
            left_str = "・".join(left_pair)
            right_str = "・".join(right_pair)
            auto_match_id = f"{selected_date}_{left_str}_vs_{right_str}_{match_number}"
            st.text_input("生成された試合ID", value=auto_match_id, disabled=True)
            submit = st.form_submit_button("試合を登録して開始")
            if submit:
                if len(left_pair) != 2 or len(right_pair) != 2:
                    st.warning("両ペアとも2人ずつ選択してください。")
                elif any(p in right_pair for p in left_pair):
                    st.warning("同じ選手を両方のチームに選ぶことはできません。")
                    st.warning("両ペアとも2人ずつ選択してください。")
                else:
                    df = pd.read_csv(MATCH_CSV)
                    if auto_match_id in df["試合ID"].values:
                        st.warning("この試合IDはすでに存在します。")
                    else:
                        for p in left_pair:
                            df.loc[len(df)] = [auto_match_id, "ダブルス", p, "A"]
                        for p in right_pair:
                            df.loc[len(df)] = [auto_match_id, "ダブルス", p, "B"]
                        df.to_csv(MATCH_CSV, index=False)
                    st.session_state.match_id = auto_match_id
                    st.session_state.rally_no = 1
                    st.session_state.shot_order = 1
                    st.session_state.score_A = 0
                    st.session_state.score_B = 0
                    st.success("試合を開始しました！")

    else:
        match_id = st.session_state.match_id
        match_df = pd.read_csv(MATCH_CSV)
        match_filtered = match_df[match_df["試合ID"] == match_id]
        if match_filtered.empty:
            st.error(f"試合ID「{match_id}」が見つかりません。試合を再登録してください。")
            st.stop()
        match_row = match_filtered.iloc[0]
        match_players = match_df[match_df["試合ID"] == match_id]
        left_team = match_players[match_players["チーム"] == "A"]["選手名"].tolist()
        right_team = match_players[match_players["チーム"] == "B"]["選手名"].tolist()
        all_players = left_team + right_team
        st.success(f"進行中の試合ID: {match_id}")
        st.subheader(f"🌟 スコア：{st.session_state.score_A} - {st.session_state.score_B}")
        st.markdown("---")

        col1, col2 = st.columns([2, 3])
        shot_saved = False
        submitted_data = {}

        with col1:
            st.markdown("#### コート図")
            st.image("new_court_map.webp", use_container_width=True)

        with col2:
            st.subheader("📝 配球記録")
            with st.form("record_form"):
                rally_no = st.session_state.rally_no
                shot_order = st.session_state.shot_order

                # 毎回直前のレシーバーを使用して次の打者を更新
                if st.session_state.shot_order > 1 and "last_receiver" in st.session_state and st.session_state["last_receiver"] in all_players:
                    st.session_state["next_player"] = st.session_state["last_receiver"]
                elif "next_player" not in st.session_state or st.session_state["next_player"] not in all_players:
                    st.session_state["next_player"] = all_players[0]
                default_hitter = st.session_state["next_player"]
                col_a, col_b = st.columns(2)
                st.session_state["last_hitter"] = default_hitter  # 強制更新
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**打った選手（自チーム）**")
                    player = st.selectbox("", all_players, index=all_players.index(st.session_state["next_player"]) if st.session_state["next_player"] in all_players else 0)
                with col_b:
                    st.markdown("**レシーブした選手（相手チーム）**")
                    receiver_candidates = right_team if player in left_team else left_team
                    receiver = st.selectbox("", receiver_candidates)
                    st.session_state["last_receiver"] = receiver
                

                area_list = ["RR", "CR", "LR", "RM", "CM", "LM", "RF", "CF", "LF"]
                default_start = st.session_state.last_end_area if st.session_state.last_end_area in area_list else "CM"
                start_area = st.selectbox("打点エリア", area_list, index=area_list.index(default_start))
                end_area = st.selectbox("着地点エリア", area_list)
                shot_type = st.radio("ショット種類", ["クリア", "スマッシュ", "ドロップ", "ロングリターン", "ショートリターン", "ドライブ", "ロブ", "プッシュ", "ヘアピン"], horizontal=True)
                result = st.radio("結果", ["続行", "得点", "ミス", "アウト"], horizontal=True)

                submit = st.form_submit_button("記録する")
                if submit:
                    submitted_data = {
                        "rally_no": rally_no,
                        "shot_order": shot_order,
                        "player": player,
                        "receiver": receiver,
                        "start_area": start_area,
                        "end_area": end_area,
                        "shot_type": shot_type,
                        "result": result
                    }
                    shot_saved = True

        if shot_saved:
            df = pd.read_csv(SHOT_CSV)
            if "レシーバー" not in df.columns:
                df["レシーバー"] = ""
            df.loc[len(df)] = [match_id, submitted_data["rally_no"], submitted_data["shot_order"], submitted_data["player"], submitted_data["start_area"], submitted_data["end_area"], submitted_data["shot_type"], submitted_data["result"], submitted_data["receiver"]]
            df.to_csv(SHOT_CSV, index=False)
            st.success("記録しました！")

            if submitted_data["result"] in ["得点", "ミス", "アウト"]:
                if submitted_data["player"] in left_team:
                    st.session_state.score_B += 1
                else:
                    st.session_state.score_A += 1

            st.session_state.last_end_area = submitted_data["end_area"]

            if submitted_data["result"] == "続行":
                st.session_state.shot_order += 1
                st.session_state.next_player = submitted_data["receiver"]
                st.session_state.last_receiver = submitted_data["receiver"]
            else:
                st.session_state.rally_no += 1
                st.session_state.shot_order = 1
                st.session_state.next_player = ""

        st.subheader("📊 この試合の記録")
        shot_df = pd.read_csv(SHOT_CSV)
        filtered_df = shot_df[shot_df["試合ID"] == match_id].sort_values(by=["ラリー番号", "ショット順"])
        st.dataframe(filtered_df)

        if st.button("⬅️ 最後の1件を削除"):
            df = pd.read_csv(SHOT_CSV)
            match_shots = df[df["試合ID"] == match_id]
            if not match_shots.empty:
                last_shot = match_shots.iloc[-1]
                df = df.drop(match_shots.tail(1).index)
                df.to_csv(SHOT_CSV, index=False)
                st.success("最後の配球記録を削除しました。")
                if last_shot["結果"] in ["得点", "ミス", "アウト"]:
                    if last_shot["打った選手"] in left_team:
                        st.session_state.score_B = max(0, st.session_state.score_B - 1)
                    else:
                        st.session_state.score_A = max(0, st.session_state.score_A - 1)
                st.session_state.shot_order = max(1, st.session_state.shot_order - 1)

        if st.button("❌ 試合終了"):
            st.session_state.match_id = None
            st.session_state.rally_no = 1
            st.session_state.shot_order = 1
            st.session_state.last_end_area = ""
            st.session_state.score_A = 0
            st.session_state.score_B = 0
            st.info("試合を終了しました。")
