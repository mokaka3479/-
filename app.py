import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="G1調教査定ツール", layout="wide")
st.title("🏆 自分専用：G1級・厳格調教査定")

j_stars = {"川田":"★★★","ルメール":"★★★","坂井":"★★","武豊":"★★","松山":"★★","助手":"ー"}

data_input = st.text_area("調教報を貼り付けてください（G1査定モード）", height=300)

if st.button("一括分析を実行"):
    if data_input:
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
            
            # 併せ馬：遅れは致命的（大幅減点）
            bn, ql = 0, "単走"
            r = re.search(r'([ァ-ヶー]{2,}).*?(\d秒\d)?(先着|遅れ|併入)', b)
            if r:
                rn, df, st_res = r.group(1), r.group(2) or "0秒0", r.group(3)
                dv = float(df.replace('秒', '.')) if '秒' in df else 0.0
                if st_res == "先着":
                    bn += (dv * 10) + 5
                    ql = f"{rn}に{dv}s先着"
                elif st_res == "遅れ":
                    bn -= 20 # 遅れは一律で厳しく
                    ql = f"{rn}に{dv}s遅れ"
                else: ql = f"{rn}併入"

            # コース基準を極限まで引き上げ
            course = "CW" if "ＣＷ" in b else "小ダ" if "小ダ" in b else "坂路" if ("坂" in b) else "他"
            tgt_at = 79.0 if course == "CW" else 67.5 if course == "小ダ" else 51.5
            tgt_lt = 11.5 # G1ならラスト11.5秒が基準
            
            # 調教スタイル：一杯追いはG1ではマイナス評価
            ks = "馬なり" if any(x in b for x in ["馬な", "馬也"]) else "一杯" if "一杯" in b else "強め"
            ks_point = 10 if ks=="馬なり" else -15 if ks=="一杯" else 0
            
            # 【新・G1スコアリング】
            # ラスト1Fの加速（終い重点）を最重視
            sc = (tgt_at - at) * 3 + (tgt_lt - lt) * 45 + 35 + ks_point + bn
            
            results.append({
                '馬名': name, 'コース': course, '内容': ql,
                '点数': round(max(0, min(100, sc)), 1),
                '今走鞍上': f"{jn}({j_stars.get(jn,'★')})"
            })

        if results:
            df = pd.DataFrame(results).sort_values('点数', ascending=False)
            # ヒートマップの色付け範囲も厳しく（50〜95点）
            st.dataframe(df.style.background_gradient(subset=['点数'], cmap='Reds', vmin=50, vmax=95).format({'点数':'{:.1f}'}), use_container_width=True, height=len(results)*40+40)
        else:
            st.warning("解析可能なデータがありません。")
