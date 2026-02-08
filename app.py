import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="調教一括分析", layout="wide")
st.title("🏇 自分専用：調教分析Webツール")

j_stars = {"川田":"★★★","ルメール":"★★★","坂井":"★★","武豊":"★★","松山":"★★","助手":"ー"}

data_input = st.text_area("ネット競馬のデータをまとめて貼り付けてください", height=300)

if st.button("一括分析を実行"):
    if data_input:
        # 改行でバラバラなデータを、馬ごとの「カタマリ」にまとめ直す
        # 「数字 数字 --」というパターンの前で分割
        blocks = re.split(r'\n\d\s+\d\s+--\n|\d\t\d\t\n--', data_input)
        results = []
        
        for b in blocks:
            if len(b) < 10: continue
            
            # 馬名（最初の行にある名前を抽出）
            lines = [l.strip() for l in b.split('\n') if l.strip()]
            name = lines[0] if lines else "不明"
            
            # 鞍上
            jm = re.search(r'(助手|[一-龠]{2,3})', b[:100])
            jn = jm.group(1) if jm else "助手"
            
            # タイム
            tm = re.findall(r'(?<!\()(\d{1,2}\.\d)(?!\))', b)
            if len(tm) < 2: continue
            ts = [float(t) for t in tm]
            at, lt = max(ts), ts[-1]
            
            # 併せ馬
            bn, ql = 0, "単走"
            r = re.search(r'([ァ-ヶー]{2,}).*?(\d秒\d)?(先着|遅れ|併入)', b)
            if r:
                rn, df, st_res = r.group(1), r.group(2) or "0秒0", r.group(3)
                dv = float(df.replace('秒', '.')) if '秒' in df else 0.0
                strg = any(k in b for k in ["OP", "オープン", "重賞", "Ｇ"])
                if st_res == "先着":
                    bn += (dv * 12) + (7 if strg else 0)
                    ql = f"{rn}に{dv}s先(格上)" if strg else f"{rn}に{dv}s先"
                elif st_res == "遅れ":
                    bn -= (dv * 8); ql = f"{rn}に{dv}s遅れ"
                else: ql = f"{rn}併入"

            # スタイルとコース
            ks = "馬なり" if any(x in b for x in
