import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="調教分析ツール", layout="wide")
st.title("🏇 自分専用：調教分析Webツール（辛口版）")

j_stars = {"川田":"★★★","ルメール":"★★★","坂井":"★★","武豊":"★★","松山":"★★","助手":"ー"}

data_input = st.text_area("ネット競馬のデータをまとめて貼り付けてください", height=300)

if st.button("一括分析を実行"):
    if data_input:
        # 馬ごとの分割をより厳密に
        blocks = re.split(r'\d+\s+\d+\s+--|--\n', data_input)
        results = []
        
        for b in blocks:
            if len(b) < 20: continue
            lines = [l.strip() for l in b.split('\n') if l.strip()]
            name = lines[0] if lines else "不明"
            
            jm = re.search(r'(助手|[一-龠]{2,4})', b)
            jn = jm.group(1) if jm else "助手"
            
            tm = re.findall(r'(?<!\()(\d{1,2}\.\d)(?!\))', b)
            if len(tm) < 2: continue
            ts = [float(t) for t in tm]
            at, lt = max(ts), ts[-1]
            
            # 併せ馬（ボーナスを少し抑えめにし、内容を重視）
            bn, ql = 0, "単走"
            r = re.search(r'([ァ-ヶー]{2,}).*?(\d秒\d)?(先着|遅れ|併入)', b)
            if r:
                rn, df, st_res = r.group(1), r.group(2) or "0秒0", r.group(3)
                dv = float(df.replace('秒', '.')) if '秒' in df else 0.0
                strg = any(k in b for k in ["OP", "オープン", "重賞", "Ｇ"])
                if st_res == "先着":
                    bn += (dv * 8) + (5 if strg else 0)
                    ql = f"{rn}に{dv}s先" + ("(格上)" if strg else "")
                elif st_res == "遅れ":
                    bn -= (dv * 12); ql = f"{rn}に{dv}s遅れ"
                else: ql = f"{rn}併入"

            # 【辛口設定】コース別基準タイムを厳格化
            course = "CW" if "ＣＷ" in b else "小ダ" if "小ダ" in b else "坂路" if ("坂" in b) else "他"
            # 基準を厳しく（CW:80.0, 坂路:52.5, 小ダ:68.5）
            tgt = 80.0 if course == "CW" else 68.5 if course == "小ダ" else 52.5
            
            # 調教スタイル判定（一杯は大幅減点）
            ks = "馬なり" if any(x in b for x in ["馬な", "馬也"]) else "一杯" if "一杯" in b else "強め"
            ks_point = 3 if ks=="馬なり" else -10 if ks=="一杯" else 0
            
            # 【新・スコア計算式】
            # 基本点を40点とし、基準タイムとの差をシビアに反映
            sc = (tgt - at) * 4 + (12.0 - lt) * 25 + 40 + ks_point + bn
            
            # 85点を超えたら相当優秀、100点は「神」レベル
            final_score = round(max(0, min(100, sc)), 1)
            
            results.append({
                '馬名': name, 'コース': course, '内容': ql,
                '点数': final_score,
                '今走鞍上': f"{jn}({j_stars.get(jn,'★')})"
            })

        if results:
            df = pd.DataFrame(results).sort_values('点数', ascending=False)
            st.dataframe(df.style.background_gradient(subset=['点数'], cmap='Reds', vmin=30, vmax=90).format({'点数':'{:.1f}'}), use_container_width=True, height=len(results)*40+40)
        else:
            st.warning("馬のデータが見つかりませんでした。")
