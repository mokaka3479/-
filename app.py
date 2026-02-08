import streamlit as st
import re
import pandas as pd

# ページの設定
st.set_page_config(page_title="調教分析ツール", layout="wide")
st.title("🏇 自分専用：調教分析Webツール")

# ジョッキー信頼度（ここを自由に書き換えて自分専用に！）
j_stars = {"川田":"★★★","ルメール":"★★★","坂井":"★★","武豊":"★★","松山":"★★","助手":"ー"}

# 入力欄
data_input = st.text_area("ネット競馬の調教報をまとめて貼り付けてください", height=200)

if st.button("一括分析を実行"):
    if data_input:
        blocks = re.split(r' -- | ―― ', data_input)
        results = []
        
        for b in blocks:
            m_name = re.search(r'([ァ-ヶー]{2,})', b)
            if not m_name: continue
            name = m_name.group(1)
            
            # 鞍上抽出
            m_jockey = re.search(r'(助手|[一-龠]{2,3})', b[:40])
            jn = m_jockey.group(1) if m_jockey else "助手"
            
            # タイム
            tm = re.findall(r'(?<!\()(\d{1,2}\.\d)(?!\))', b)
            if len(tm) < 2: continue
            ts = [float(t) for t in tm]
            at, lt = max(ts), ts[-1]
            
            # 併せ馬（あの採用ロジック）
            bn, ql = 0, "単走"
            r = re.search(r'内?外?([ァ-ヶー]{2,})[^\d]*(\d+秒\d+)?(先着|遅れ|併入)', b)
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

            # 調教スタイル
            ks = "馬なり" if any(x in b for x in ["馬な", "馬也"]) else "一杯" if "一杯" in b else "他"
            course = "CW" if "ＣＷ" in b else "小ダ" if "小ダ" in b else "坂路"
            tgt = 82.0 if course == "CW" else 70.0 if course == "小ダ" else 54.0
            
            # スコア
            sc = (tgt - at) * 5 + (12.2 - lt) * 30 + 50 + (5 if ks=="馬なり" else -3 if ks=="一杯" else 0) + bn
            
            results.append({
                '馬名': name, 'コース': course, '内容': ql,
                '点数': round(max(0, min(100, sc)), 1),
                '今走鞍上': f"{jn}({j_stars.get(jn,'★')})"
            })

        if results:
            df = pd.DataFrame(results).sort_values('点数', ascending=False)
            st.dataframe(df.style.background_gradient(subset=['点数'], cmap='Reds').format({'点数':'{:.1f}'}), use_container_width=True)
        else:
            st.error("解析不能：形式を確認してください")
    else:
        st.info("データを貼り付けてボタンを押してください")
