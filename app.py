import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="調教分析ツール", layout="wide")
st.title("🏇 自分専用：調教分析Webツール")

# ジョッキー名簿（適宜追加してください）
j_stars = {"川田":"★★★","ルメール":"★★★","坂井":"★★","武豊":"★★","松山":"★★","助手":"ー"}

data_input = st.text_area("ネット競馬のデータをまとめて貼り付けてください", height=300)

if st.button("一括分析を実行"):
    if data_input:
        # 修正：より確実に馬ごとに分割するロジック
        blocks = re.split(r'\d+\s+\d+\s+--|--\n', data_input)
        results = []
        
        for b in blocks:
            if len(b) < 20: continue
            
            lines = [l.strip() for l in b.split('\n') if l.strip()]
            # 馬名（-- の直後の行を取得）
            name = lines[0] if lines else "不明"
            
            # ジョッキー抽出（前走の横にある名前を拾う）
            jm = re.search(r'(助手|[一-龠]{2,4})', b)
            jn = jm.group(1) if jm else "助手"
            
            # タイム抽出
            tm = re.findall(r'(?<!\()(\d{1,2}\.\d)(?!\))', b)
            if len(tm) < 2: continue
            ts = [float(t) for t in tm]
            at, lt = max(ts), ts[-1]
            
            # 併せ馬ボーナス
            bn, ql = 0, "単走"
            r = re.search(r'([ァ-ヶー]{2,}).*?(\d秒\d)?(先着|遅れ|併入)', b)
            if r:
                rn, df, st_res = r.group(1), r.group(2) or "0秒0", r.group(3)
                dv = float(df.replace('秒', '.')) if '秒' in df else 0.0
                strg = any(k in b for k in ["OP", "オープン", "重賞", "Ｇ"])
                if st_res == "先着":
                    bn += (dv * 15) + (8 if strg else 0)
                    ql = f"{rn}に{dv}s先" + ("(格上)" if strg else "")
                elif st_res == "遅れ":
                    bn -= (dv * 10); ql = f"{rn}に{dv}s遅れ"
                else: ql = f"{rn}併入"

            # スタイルとコース判定
            ks = "馬なり" if any(x in b for x in ["馬な", "馬也"]) else "一杯" if "一杯" in b else "強め"
            course = "CW" if "ＣＷ" in b else "小ダ" if "小ダ" in b else "坂路" if ("坂" in b) else "他"
            tgt = 82.0 if course == "CW" else 70.0 if course == "小ダ" else 54.0
            
            # スコア計算（さらに精度アップ）
            sc = (tgt - at) * 6 + (12.2 - lt) * 35 + 50 + (6 if ks=="馬なり" else -4 if ks=="一杯" else 0) + bn
            
            results.append({
                '馬名': name, 'コース': course, '内容': ql,
                '点数': round(max(0, min(100, sc)), 1),
                '今走鞍上': f"{jn}({j_stars.get(jn,'★')})"
            })

        if results:
            df = pd.DataFrame(results).sort_values('点数', ascending=False)
            # 全頭表示するために height を指定
            st.dataframe(df.style.background_gradient(subset=['点数'], cmap='Reds').format({'点数':'{:.1f}'}), use_container_width=True, height=len(results)*40)
        else:
            st.warning("馬のデータが見つかりませんでした。")
